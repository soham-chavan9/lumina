"""Lumina API — RAG compliance assistant."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from backend.routes.ask_route import router as ask_router
from backend.routes.insights_route import router as insights_router
from backend.routes.library_route import router as library_router
from backend.routes.upload_route import router as upload_router
from backend.schemas import HealthResponse
from backend.utils.embed_store import get_embed_store

logging.basicConfig(level=logging.INFO)
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
    title="Lumina AI — Compliance Assistant",
    description="Upload policy PDFs, ask grounded compliance questions, get cited answers.",
    version="2.0.0",
    lifespan=lifespan,
)

cors_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(ask_router, prefix="/api", tags=["Ask"])
app.include_router(library_router, prefix="/api", tags=["Library"])
app.include_router(insights_router, prefix="/api", tags=["Insights"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    store = get_embed_store()
    return HealthResponse(
        status="ok",
        message="Lumina backend is live",
        vector_store_ready=store.is_ready(),
        document_chunks=store.chunk_count(),
        model=os.getenv("LUMINA_MODEL", "gpt-4o-mini"),
    )


@app.get("/")
def root():
    return {
        "message": "Lumina Backend",
        "endpoints": {
            "health": "/health",
            "upload": "/api/upload",
            "ask": "/api/ask",
            "documents": "/api/documents",
            "suggestions": "/api/suggestions",
            "scan": "/api/scan",
            "docs": "/docs",
        },
    }
