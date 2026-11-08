"""PDF upload → chunk → embed into the shared FAISS store."""

import logging
import os
import re

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.config import get_settings
from backend.schemas import UploadFileResult, UploadResponse
from backend.utils.embed_store import get_embed_store
from backend.utils.pdf_parser import extract_text_from_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)) -> UploadResponse:
    settings = get_settings()
    max_files = settings.max_upload_files
    max_bytes = settings.max_upload_mb * 1024 * 1024

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > max_files:
        raise HTTPException(status_code=400, detail=f"Max {max_files} files per request.")

    store = get_embed_store()
    results: list[UploadFileResult] = []

    for file in files:
        raw_name = file.filename or "unnamed.pdf"
        filename = re.sub(r"[^\w.\- ]+", "_", os.path.basename(raw_name))[:120]
        try:
            if not filename.lower().endswith(".pdf"):
                results.append(
                    UploadFileResult(
                        filename=filename,
                        status="Skipped: only PDF files are supported.",
                    )
                )
                continue

            content = await file.read()
            if len(content) > max_bytes:
                results.append(
                    UploadFileResult(
                        filename=filename,
                        status=f"Skipped: file exceeds {settings.max_upload_mb}MB limit.",
                    )
                )
                continue

            text = extract_text_from_pdf(content)
            if (
                not text.strip()
                or text.startswith("Error:")
                or text.startswith("No extractable")
            ):
                results.append(
                    UploadFileResult(
                        filename=filename,
                        status="Skipped: no extractable text.",
                    )
                )
                continue

            chunks = store.add_document(text, source=filename)
            results.append(
                UploadFileResult(
                    filename=filename,
                    status="Embedded successfully.",
                    preview=None,  # Do not return document body over the wire.
                    chunks=chunks,
                )
            )
            logger.info("Embedded %s (%s chunks)", filename, chunks)
        except Exception:
            logger.exception("Upload failed for %s", filename)
            results.append(
                UploadFileResult(
                    filename=filename,
                    status="Error: failed to process file.",
                )
            )

    return UploadResponse(
        summary=f"Processed {len(results)} file(s)",
        results=results,
    )
