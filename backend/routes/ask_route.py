"""Single /ask path — retrieval is code-gated; LLM only runs when context exists."""

import logging
import os
import re

from fastapi import Depends, APIRouter, HTTPException
from backend.auth import require_api_key

from backend.llm_workflow import generate_lumina_answer, parse_lumina_output
from backend.schemas import AskRequest, AskResponse, SourceDoc
from backend.utils.embed_store import get_embed_store
from backend.utils.performance_logger import log_performance

router = APIRouter(dependencies=[Depends(require_api_key)])
logger = logging.getLogger(__name__)

INJECTION_PHRASES = (
    "ignore previous",
    "disregard previous",
    "ignore all instructions",
    "jailbreak",
    "you are no longer",
    "override system",
    "system message",
)


def detect_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in INJECTION_PHRASES)


def _normalize_confidence(value: str) -> str:
    cleaned = (value or "Unknown").strip().capitalize()
    if cleaned not in {"High", "Medium", "Low", "Unknown"}:
        return "Unknown"
    return cleaned


@router.post("/ask", response_model=AskResponse)
@log_performance
async def ask_question(data: AskRequest) -> AskResponse:
    question = data.question.strip()
    logger.info("Incoming question (%s chars)", len(question))

    if len(question) < 6:
        return AskResponse(
            answer="Please enter a more specific compliance-related question.",
            confidence="Low",
            refused=True,
        )

    if detect_prompt_injection(question):
        logger.warning("Prompt injection blocked")
        return AskResponse(
            answer="Your question contains prohibited instructions and was blocked.",
            confidence="High",
            refused=True,
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY.")

    store = get_embed_store()

    # Code gate: never call the LLM without retrieved context
    if not store.is_ready():
        return AskResponse(
            answer="No documents are indexed yet. Upload a policy PDF first.",
            confidence="High",
            refused=True,
        )

    max_distance = float(os.getenv("LUMINA_MAX_DISTANCE", "1.2"))
    results = store.query(question, k=6, max_distance=max_distance)
    if not results:
        return AskResponse(
            answer="Not found in document.",
            citation="No sufficiently relevant chunks retrieved.",
            confidence="High",
            refused=True,
        )

    context = "\n\n".join(res["text"][:900] for res in results)
    if len(context) > 4500:
        context = context[:4500]

    sources = sorted({res["source"] for res in results})
    # Snippets are intentionally short to reduce corpus exfiltration surface.
    source_docs = [
        SourceDoc(source=res["source"], snippet=res["text"][:80] + ("…" if len(res["text"]) > 80 else ""))
        for res in results[:3]
    ]

    try:
        raw = generate_lumina_answer(question=question, context=context)
        parsed = parse_lumina_output(raw)
    except Exception:
        logger.exception("/ask LLM failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer. Check server logs and API quota.",
        )

    answer = parsed.get("answer") or "Not found in document."
    citation = parsed.get("citation") or ""
    confidence = _normalize_confidence(parsed.get("confidence", "Unknown"))

    if re.search(r"not found in document", answer, re.IGNORECASE):
        confidence = "High"

    return AskResponse(
        answer=answer,
        citation=citation,
        confidence=confidence,  # type: ignore[arg-type]
        sources=sources,
        source_documents=source_docs,
        refused=False,
    )
