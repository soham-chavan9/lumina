"""Insights MVPs — suggested questions + compliance risk scan."""

import json
import logging
import re
from typing import List

from fastapi import APIRouter, HTTPException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.llm_workflow import get_lumina_model
from backend.schemas import (
    RiskFinding,
    RiskScanResponse,
    SuggestionItem,
    SuggestionsResponse,
)
from backend.utils.embed_store import get_embed_store

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_SUGGESTIONS = [
    SuggestionItem(question="What personal data does this policy cover?", category="privacy"),
    SuggestionItem(question="What are the data breach notification requirements?", category="incident"),
    SuggestionItem(question="How can a user withdraw consent?", category="rights"),
    SuggestionItem(question="Who is responsible for compliance oversight?", category="governance"),
]

SUGGEST_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write short compliance interview questions grounded ONLY in the context.\n"
            "Return JSON array of exactly 4 objects: "
            '{{"question":"...","category":"privacy|security|rights|governance|incident"}}.\n'
            "No markdown fences.",
        ),
        ("human", "Document names: {sources}\n\nContext:\n{context}"),
    ]
)

SCAN_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Lumina, a compliance risk analyst.\n"
            "Use ONLY the provided policy context.\n"
            "Return JSON with keys: summary (string), "
            "findings (array of {{title, severity: High|Medium|Low, detail, recommendation}}), "
            "strengths (array of strings).\n"
            "Max 5 findings. No markdown fences.",
        ),
        ("human", "Sources: {sources}\n\nContext:\n{context}"),
    ]
)


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    return json.loads(text)


@router.get("/suggestions", response_model=SuggestionsResponse)
def get_suggestions() -> SuggestionsResponse:
    store = get_embed_store()
    if not store.is_ready():
        return SuggestionsResponse(suggestions=DEFAULT_SUGGESTIONS)

    docs = store.list_documents()
    sources = ", ".join(d["source"] for d in docs) or "uploaded policies"
    context = store.sample_context(3500)
    if not context:
        return SuggestionsResponse(suggestions=DEFAULT_SUGGESTIONS)

    try:
        chain = SUGGEST_PROMPT | get_lumina_model() | StrOutputParser()
        raw = chain.invoke({"sources": sources, "context": context})
        data = _extract_json(raw)
        items: List[SuggestionItem] = []
        for row in data[:4]:
            items.append(
                SuggestionItem(
                    question=str(row.get("question", "")).strip(),
                    category=str(row.get("category", "general")).strip() or "general",
                )
            )
        items = [i for i in items if i.question]
        if items:
            return SuggestionsResponse(suggestions=items)
    except Exception:
        logger.exception("Suggestion generation failed; using defaults")

    return SuggestionsResponse(suggestions=DEFAULT_SUGGESTIONS)


@router.post("/scan", response_model=RiskScanResponse)
def run_risk_scan() -> RiskScanResponse:
    store = get_embed_store()
    if not store.is_ready():
        raise HTTPException(
            status_code=400,
            detail="Upload at least one policy PDF before running a risk scan.",
        )

    docs = store.list_documents()
    sources = [d["source"] for d in docs]
    context = store.sample_context(6000)
    if not context:
        raise HTTPException(status_code=400, detail="No readable document context found.")

    try:
        chain = SCAN_PROMPT | get_lumina_model() | StrOutputParser()
        raw = chain.invoke({"sources": ", ".join(sources), "context": context})
        data = _extract_json(raw)
    except Exception:
        logger.exception("Risk scan failed")
        raise HTTPException(
            status_code=500,
            detail="Risk scan failed. Check OpenAI quota and try again.",
        )

    findings = []
    for row in data.get("findings", [])[:5]:
        severity = str(row.get("severity", "Medium")).strip().capitalize()
        if severity not in {"High", "Medium", "Low"}:
            severity = "Medium"
        findings.append(
            RiskFinding(
                title=str(row.get("title", "Finding")).strip(),
                severity=severity,  # type: ignore[arg-type]
                detail=str(row.get("detail", "")).strip(),
                recommendation=str(row.get("recommendation", "")).strip(),
            )
        )

    strengths = [str(s).strip() for s in data.get("strengths", []) if str(s).strip()][:5]
    summary = str(data.get("summary", "Compliance scan complete.")).strip()

    return RiskScanResponse(
        summary=summary,
        findings=findings,
        strengths=strengths,
        sources=sources,
    )
