"""PDF upload → chunk → embed into the shared FAISS store."""

import logging
import os
import re
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.schemas import UploadFileResult, UploadResponse
from backend.utils.embed_store import get_embed_store
from backend.utils.pdf_parser import extract_text_from_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILES = 10
MAX_BYTES = 15 * 1024 * 1024  # 15 MB per file


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_FILES} files per request.")

    store = get_embed_store()
    results: List[UploadFileResult] = []

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
            if len(content) > MAX_BYTES:
                results.append(
                    UploadFileResult(
                        filename=filename,
                        status="Skipped: file exceeds 15MB limit.",
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
            preview = text[:300] + ("..." if len(text) > 300 else "")
            results.append(
                UploadFileResult(
                    filename=filename,
                    status="Embedded successfully.",
                    preview=preview,
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
