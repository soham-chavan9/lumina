"""Lumina API — production RAG compliance assistant."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from backend.middleware import SecurityHeadersMiddleware
from backend.routes.ask_route import router as ask_router
from backend.routes.insights_route import router as insights_router
from backend.routes.library_route import router as library_router
from backend.routes.upload_route import router as upload_router
from backend.schemas import HealthResponse
from backend.utils.embed_store import get_embed_store

ENV = os.getenv("LUMINA_ENV", "development").lower()
IS_PROD = ENV in {"production", "prod"}

logging.basicConfig(
    level=logging.INFO if IS_PROD else logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("lumina")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store = get_embed_store()
    seed = os.getenv("LUMINA_SEED_SAMPLE_DOCS", "false").lower() in {"1", "true", "yes"}
    if seed and not store.is_ready():
        try:
            indexed = store.index_pdfs_from_folder()
            logger.info("Seeded %s sample PDF(s) into vector store", indexed)
        except Exception as exc:
            logger.warning("Sample doc seeding skipped: %s", exc)
    yield


app = FastAPI(
    title="Lumina",
    description="Grounded compliance Q&A over your policy corpus.",
    version="2.1.0",
    lifespan=lifespan,
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

_cors_raw = os.getenv("CORS_ORIGINS")
default_origins = (
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
)
cors_origins = [
    o.strip() for o in (_cors_raw or default_origins).split(",") if o.strip()
]
if IS_PROD and not _cors_raw:
    logger.warning("Production CORS is still using localhost defaults — set CORS_ORIGINS")

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(ask_router, prefix="/api", tags=["Ask"])
app.include_router(library_router, prefix="/api", tags=["Library"])
app.include_router(insights_router, prefix="/api", tags=["Insights"])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if IS_PROD and exc.status_code >= 500:
        detail = "Internal server error"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request", "errors": exc.errors() if not IS_PROD else None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    store = get_embed_store()
    return HealthResponse(
        status="ok",
        message="Lumina is ready",
        vector_store_ready=store.is_ready(),
        document_chunks=store.chunk_count(),
        model=os.getenv("LUMINA_MODEL", "gpt-4o-mini"),
    )


@app.get("/ready")
def readiness():
    """Kubernetes-style readiness: process up; corpus may still be empty."""
    return {"ready": True, "env": ENV}


@app.get("/")
def root():
    payload = {
        "service": "lumina",
        "version": "2.1.0",
        "health": "/health",
        "ready": "/ready",
    }
    if not IS_PROD:
        payload["endpoints"] = {
            "upload": "/api/upload",
            "ask": "/api/ask",
            "documents": "/api/documents",
            "suggestions": "/api/suggestions",
            "scan": "/api/scan",
            "docs": "/docs",
        }
    return payload
