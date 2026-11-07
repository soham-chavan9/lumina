"""Document library — list and clear indexed sources."""

import logging

from fastapi import APIRouter

from backend.schemas import DocumentInfo, DocumentsResponse
from backend.utils.embed_store import get_embed_store

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/documents", response_model=DocumentsResponse)
def list_documents() -> DocumentsResponse:
    store = get_embed_store()
    docs = [DocumentInfo(**item) for item in store.list_documents()]
    return DocumentsResponse(documents=docs, total_chunks=store.chunk_count())


@router.delete("/documents", response_model=DocumentsResponse)
def clear_documents() -> DocumentsResponse:
    store = get_embed_store()
    store.clear()
    logger.info("Document library cleared")
    return DocumentsResponse(documents=[], total_chunks=0)
