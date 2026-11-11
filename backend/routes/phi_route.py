"""PHI scan: find HIPAA Safe Harbor identifiers in a PDF without storing it.

Detection is rule-based and runs in-process; the document is never indexed,
persisted or sent to a model provider. Logs record counts only, never values.
"""

import logging
import os
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.auth import require_api_key
from backend.config import get_settings
from backend.routes.upload_route import _read_capped
from backend.schemas import PhiCategorySummary, PhiScanResponse
from backend.utils.pdf_parser import extract_text_from_pdf
from backend.utils.phi_detector import CATEGORY_LABELS, detect_phi, looks_like_patient_record, mask

router = APIRouter(dependencies=[Depends(require_api_key)])
logger = logging.getLogger(__name__)

SCAN_NOTE = (
    "Scanned on this server with rule-based Safe Harbor checks. The file was not stored, "
    "indexed or sent to a model provider. Rules can miss identifiers; review before sharing."
)


@router.post("/phi-scan", response_model=PhiScanResponse)
async def phi_scan(file: UploadFile = File(...)) -> PhiScanResponse:
    settings = get_settings()
    filename = re.sub(r"[^\w.\- ]+", "_", os.path.basename(file.filename or "document.pdf"))[:120]
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files can be scanned.")

    content = await _read_capped(file, settings.max_upload_mb * 1024 * 1024)
    if content is None:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb}MB limit.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF (missing %PDF- header).")

    text = extract_text_from_pdf(content)
    if not text.strip() or text.startswith(("Error:", "No extractable")):
        raise HTTPException(status_code=422, detail="No extractable text (scanned images need OCR first).")

    hits = detect_phi(text[:1_500_000])
    grouped: dict[str, list[str]] = {}
    for hit in hits:
        grouped.setdefault(hit.category, []).append(hit.value)
    categories = [
        PhiCategorySummary(
            category=category,
            label=CATEGORY_LABELS.get(category, category),
            count=len(values),
            examples=[mask(v) for v in values[:3]],
        )
        for category, values in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    logger.info("PHI scan: %s identifiers in %s categories", len(hits), len(categories))
    return PhiScanResponse(
        filename=filename,
        verdict="phi_found" if hits else "no_phi_found",
        likely_patient_record=looks_like_patient_record(hits),
        identifier_count=len(hits),
        categories=categories,
        note=SCAN_NOTE,
    )
