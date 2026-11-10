"""Lumina API — HIPAA privacy desk (production-ready FastAPI app)."""

import logging
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

from backend.config import get_settings
from backend.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from backend.routes.ask_route import router as ask_router
from backend.routes.healthcare_route import router as healthcare_router
from backend.routes.insights_route import router as insights_router
from backend.routes.library_route import router as library_router
from backend.routes.upload_route import router as upload_router
from backend.schemas import HealthResponse
from backend.utils.embed_store import get_embed_store

settings = get_settings()
settings.validate_for_boot()

logging.basicConfig(
    level=logging.INFO if settings.is_prod else logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("lumina")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store = get_embed_store()
    if settings.seed_sample_docs and not store.is_ready():
        try:
            indexed = store.index_pdfs_from_folder()
            logger.info("Seeded %s sample PDF(s) into vector store", indexed)
        except Exception as exc:
            logger.warning("Sample doc seeding skipped: %s", exc)
    logger.info(
        "Lumina %s started (env=%s, model=%s)",
        settings.version,
        settings.env,
        settings.model,
    )
    yield


app = FastAPI(
    title="Lumina",
    description=(
        "HIPAA privacy desk for health systems — grounded policy Q&A, breach clocks, "
        "patient access guides, and BAA vendor screens."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url=None if settings.is_prod else "/docs",
    redoc_url=None if settings.is_prod else "/redoc",
    openapi_url=None if settings.is_prod else "/openapi.json",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    limit_per_minute=settings.rate_limit_per_minute,
    llm_limit_per_minute=settings.llm_rate_limit_per_minute,
    trust_proxy=settings.trust_proxy,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key", "X-Tenant-Id"],
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(ask_router, prefix="/api", tags=["Ask"])
app.include_router(library_router, prefix="/api", tags=["Library"])
app.include_router(insights_router, prefix="/api", tags=["Insights"])
app.include_router(healthcare_router, prefix="/api", tags=["Healthcare"])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if settings.is_prod and exc.status_code >= 500:
        detail = "Internal server error"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request",
            "errors": None if settings.is_prod else exc.errors(),
        },
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
        model=settings.model,
    )


@app.get("/ready")
def readiness():
    """Readiness: process up; in production also require API key + OpenAI key."""
    problems: list[str] = []
    if settings.is_prod:
        if not settings.api_key:
            problems.append("missing_api_key")
        if not settings.openai_api_key:
            problems.append("missing_openai_api_key")
    ready = len(problems) == 0
    payload = {
        "ready": ready,
        "env": settings.env,
        "version": settings.version,
    }
    if problems:
        payload["problems"] = problems
    return JSONResponse(status_code=200 if ready else 503, content=payload)


@app.get("/")
def root():
    payload = {
        "service": "lumina",
        "industry": "healthcare-hipaa",
        "version": settings.version,
        "health": "/health",
        "ready": "/ready",
    }
    if not settings.is_prod:
        payload["endpoints"] = {
            "upload": "/api/upload",
            "ask": "/api/ask",
            "documents": "/api/documents",
            "suggestions": "/api/suggestions",
            "scan": "/api/scan",
            "breach_clock": "/api/breach-clock",
            "access_request": "/api/access-request",
            "baa_screen": "/api/baa-screen",
            "docs": "/docs",
        }
    return payload
