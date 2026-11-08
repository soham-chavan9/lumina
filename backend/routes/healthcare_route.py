"""Healthcare HIPAA workflows — breach clock, access requests, BAA screen."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta

from fastapi import Depends, APIRouter, HTTPException
from backend.auth import require_api_key
from backend.tenant import bind_tenant
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.llm_workflow import get_lumina_model
from backend.schemas import (
    AccessRequestGuideRequest,
    AccessRequestGuideResponse,
    BaaScreenRequest,
    BaaScreenResponse,
    BreachClockRequest,
    BreachClockResponse,
    BreachFactor,
)
from backend.utils.embed_store import get_embed_store

router = APIRouter(dependencies=[Depends(require_api_key), Depends(bind_tenant)])
logger = logging.getLogger(__name__)


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    return json.loads(text)


def _parse_day(value: str, *, allow_future: bool = False) -> date:
    raw = value.strip()
    parsed: date | None = None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(raw[:10] if "T" in raw else raw, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail="Use an ISO date like 2026-11-07 for discovered/received dates.",
            ) from exc
    if not allow_future and parsed > date.today():
        raise HTTPException(
            status_code=422,
            detail="Discovery/received date cannot be in the future.",
        )
    return parsed


def _deadline_meta(start: date, days: int) -> tuple[str, int | None]:
    deadline = start + timedelta(days=days)
    remaining = (deadline - date.today()).days
    return deadline.isoformat(), remaining


def _corpus_context(query: str, max_chars: int = 5500) -> tuple[str, list[str]]:
    """Retrieve matching passages only — never dump the whole corpus on a miss."""
    store = get_embed_store()
    if not store.is_ready():
        return "", []
    hits = store.query(query, k=8, max_distance=1.35)
    if not hits:
        return "", []
    parts = []
    sources = sorted({h["source"] for h in hits})
    total = 0
    for hit in hits:
        # Cap each passage so a single hit cannot exfiltrate a large blob.
        text = hit["text"][:900]
        chunk = f"[{hit['source']}]\n{text}"
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n".join(parts), sources



def _require_phi_ack(acknowledged: bool) -> None:
    if not acknowledged:
        raise HTTPException(
            status_code=400,
            detail=(
                "acknowledge_phi_export must be true. Lumina may send workflow "
                "details to the configured model provider — confirm before continuing."
            ),
        )

BREACH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Lumina for hospital and digital-health privacy officers.\n"
            "Ground EVERY claim in the policy context. HIPAA Breach Notification Rule: "
            "notify individuals without unreasonable delay and no later than 60 calendar days "
            "after discovery when unsecured PHI is breached.\n"
            "Apply the four-factor impermissible-use risk assessment.\n"
            "Return JSON only with keys: summary, likely_reportable (bool), "
            "four_factor (array of {{factor, assessment, risk: High|Medium|Low}}), "
            "immediate_actions (string array), policy_citations (string array).\n"
            "No markdown fences.",
        ),
        (
            "human",
            "Discovery date: {discovered_at}\n"
            "PHI involved: {phi_involved}\n"
            "Individuals affected (estimate): {individuals}\n"
            "Unauthorized recipient: {recipient}\n"
            "Incident:\n{description}\n\n"
            "Policy context:\n{context}",
        ),
    ]
)

ACCESS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Lumina for HIPAA Privacy Rule individual rights.\n"
            "Default statutory clock for access (§164.524): act within 30 days of receipt "
            "(one 30-day extension with written notice is common if policy allows).\n"
            "Use ONLY the policy context for org-specific steps; label statutory defaults clearly.\n"
            "Return JSON: summary, checklist (array), denial_or_delay_rules (array), "
            "policy_citations (array). No markdown fences.",
        ),
        (
            "human",
            "Request type: {request_type}\nReceived: {received_at}\nChannel: {channel}\n"
            "Notes: {notes}\n\nPolicy context:\n{context}",
        ),
    ]
)

BAA_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Lumina for healthcare vendor / Business Associate diligence.\n"
            "If a vendor creates, receives, maintains, or transmits PHI for a covered entity, "
            "a BAA is generally required before PHI flows.\n"
            "Ground recommendations in policy context when present.\n"
            "Return JSON: summary, ba_likely_required (bool), risk_level (High|Medium|Low), "
            "required_clauses (array), diligence_questions (array), blockers (array), "
            "policy_citations (array). No markdown fences.",
        ),
        (
            "human",
            "Vendor: {vendor}\nServices: {services}\nPHI CRT?: {phi}\nNotes: {notes}\n\n"
            "Policy context:\n{context}",
        ),
    ]
)


@router.post("/breach-clock", response_model=BreachClockResponse)
def breach_clock(payload: BreachClockRequest) -> BreachClockResponse:
    _require_phi_ack(payload.acknowledge_phi_export)
    discovered = _parse_day(payload.discovered_at)
    deadline, remaining = _deadline_meta(discovered, 60)
    context, sources = _corpus_context(
        f"breach notification incident response PHI disclosure {payload.description}"
    )

    mode: str = "fallback"
    try:
        raw = (BREACH_PROMPT | get_lumina_model() | StrOutputParser()).invoke(
            {
                "discovered_at": discovered.isoformat(),
                "phi_involved": payload.phi_involved,
                "individuals": payload.individuals_affected
                if payload.individuals_affected is not None
                else "unknown",
                "recipient": payload.unauthorized_recipient or "unknown",
                "description": payload.description,
                "context": context or "No matching policy passages retrieved.",
            }
        )
        data = _extract_json(raw)
        mode = "policy_grounded" if context else "fallback"
    except Exception:
        logger.exception("Breach clock LLM failed; using deterministic HIPAA shell")
        mode = "fallback"
        data = {
            "summary": (
                "Treat this as a potential breach of unsecured PHI until the four-factor "
                "assessment documents otherwise. Individual notification is due no later than "
                f"{deadline} (60 days from discovery), unless your filed policy is stricter."
            ),
            "likely_reportable": bool(payload.phi_involved),
            "four_factor": [
                {
                    "factor": "Nature and extent of PHI",
                    "assessment": "Document identifiers and clinical sensitivity involved.",
                    "risk": "Medium",
                },
                {
                    "factor": "Unauthorized person",
                    "assessment": (
                        (payload.unauthorized_recipient[:280] + "…")
                        if len(payload.unauthorized_recipient) > 280
                        else payload.unauthorized_recipient
                    )
                    or "Identify who received or could access the PHI.",
                    "risk": "Medium",
                },
                {
                    "factor": "Whether PHI was actually acquired or viewed",
                    "assessment": "Preserve logs/email evidence of access vs. bounce/quarantine.",
                    "risk": "Unknown",
                },
                {
                    "factor": "Extent of mitigation",
                    "assessment": "Record containment, retrieval, recipient attestations, and patient risk reduction.",
                    "risk": "Medium",
                },
            ],
            "immediate_actions": [
                "Open an incident record and freeze relevant logs/mailboxes.",
                "Contain: recall message, disable accounts, or isolate systems.",
                "Complete the four-factor assessment with Privacy + Security + Legal.",
                f"Calendar individual notification no later than {deadline}.",
            ],
            "policy_citations": [
                "HIPAA Breach Notification Rule — without unreasonable delay, ≤ 60 days from discovery."
            ],
        }

    factors = []
    for row in data.get("four_factor", [])[:4]:
        risk = str(row.get("risk", "Unknown")).capitalize()
        if risk not in {"High", "Medium", "Low", "Unknown"}:
            risk = "Unknown"
        factors.append(
            BreachFactor(
                factor=str(row.get("factor", "Factor")),
                assessment=str(row.get("assessment", "")),
                risk=risk,  # type: ignore[arg-type]
            )
        )

    return BreachClockResponse(
        summary=str(data.get("summary", "")).strip(),
        notification_deadline=deadline,
        days_remaining=remaining,
        likely_reportable=bool(data.get("likely_reportable", payload.phi_involved)),
        four_factor=factors,
        immediate_actions=[str(x) for x in data.get("immediate_actions", []) if str(x).strip()][:8],
        policy_citations=[str(x) for x in data.get("policy_citations", []) if str(x).strip()][:6],
        sources=sources,
        mode=mode,  # type: ignore[arg-type]
    )


@router.post("/access-request", response_model=AccessRequestGuideResponse)
def access_request_guide(payload: AccessRequestGuideRequest) -> AccessRequestGuideResponse:
    _require_phi_ack(payload.acknowledge_phi_export)
    received = _parse_day(payload.received_at)
    deadline, remaining = _deadline_meta(received, 30)
    context, sources = _corpus_context(
        f"individual right of access amendment accounting of disclosures {payload.request_type}"
    )

    mode: str = "fallback"
    try:
        raw = (ACCESS_PROMPT | get_lumina_model() | StrOutputParser()).invoke(
            {
                "request_type": payload.request_type,
                "received_at": received.isoformat(),
                "channel": payload.channel,
                "notes": payload.notes or "none",
                "context": context or "No matching policy passages retrieved.",
            }
        )
        data = _extract_json(raw)
        mode = "policy_grounded" if context else "fallback"
    except Exception:
        logger.exception("Access guide LLM failed; using statutory shell")
        mode = "fallback"
        data = {
            "summary": (
                f"Treat this {payload.request_type} request as received on {received.isoformat()}. "
                f"HIPAA access requests generally require action by {deadline} (30 days), "
                "with one possible 30-day extension if your policy and written notice allow it."
            ),
            "checklist": [
                "Authenticate the requestor and confirm identity/authority.",
                "Locate designated record set locations covering the request.",
                "Provide access in the requested form/format if readily producible.",
                "Log fulfillment date, format, and any fees charged.",
                "If delaying, issue written notice before the initial deadline.",
            ],
            "denial_or_delay_rules": [
                "Document any denial ground allowed by §164.524 and your filed policy.",
                "Offer review of denials where required.",
            ],
            "policy_citations": [
                "HIPAA Privacy Rule §164.524 — access of individuals to PHI (30-day standard)."
            ],
        }

    return AccessRequestGuideResponse(
        summary=str(data.get("summary", "")).strip(),
        statutory_deadline=deadline,
        days_remaining=remaining,
        checklist=[str(x) for x in data.get("checklist", []) if str(x).strip()][:10],
        denial_or_delay_rules=[
            str(x) for x in data.get("denial_or_delay_rules", []) if str(x).strip()
        ][:6],
        policy_citations=[str(x) for x in data.get("policy_citations", []) if str(x).strip()][:6],
        sources=sources,
        mode=mode,  # type: ignore[arg-type]
    )


@router.post("/baa-screen", response_model=BaaScreenResponse)
def baa_screen(payload: BaaScreenRequest) -> BaaScreenResponse:
    _require_phi_ack(payload.acknowledge_phi_export)
    context, sources = _corpus_context(
        f"business associate agreement vendor PHI {payload.vendor_name} {payload.services}"
    )

    mode: str = "fallback"
    try:
        raw = (BAA_PROMPT | get_lumina_model() | StrOutputParser()).invoke(
            {
                "vendor": payload.vendor_name,
                "services": payload.services,
                "phi": payload.creates_receives_maintains_or_transmits_phi,
                "notes": payload.notes or "none",
                "context": context or "No matching policy passages retrieved.",
            }
        )
        data = _extract_json(raw)
        mode = "policy_grounded" if context else "fallback"
    except Exception:
        logger.exception("BAA screen LLM failed; using diligence shell")
        mode = "fallback"
        needs = payload.creates_receives_maintains_or_transmits_phi
        data = {
            "summary": (
                f"{payload.vendor_name} "
                f"{'appears to require' if needs else 'may not require'} a BAA "
                "based on whether it creates/receives/maintains/transmits PHI for your covered entity. "
                "Do not share PHI until Privacy/Legal clears the contract package."
            ),
            "ba_likely_required": needs,
            "risk_level": "High" if needs else "Low",
            "required_clauses": [
                "Permitted uses/disclosures of PHI and prohibition on other uses",
                "Safeguards aligned to the Security Rule",
                "Breach reporting duties and cooperation",
                "Subcontractor flow-down of BAA obligations",
                "Return or destruction of PHI at termination",
            ],
            "diligence_questions": [
                "Where is PHI stored and who can access it?",
                "What independent security attestations exist (e.g., SOC 2, HITRUST)?",
                "What is the vendor’s incident notification SLA to us?",
                "Are subcontractors with PHI access under equivalent BAAs?",
            ],
            "blockers": [
                "No signed BAA before PHI access",
                "Unclear data flow or minimum-necessary justification",
            ]
            if needs
            else [],
            "policy_citations": [
                "HIPAA Privacy Rule — Business Associate requirements (§164.502 / §164.504)."
            ],
        }

    risk = str(data.get("risk_level", "Unknown")).capitalize()
    if risk not in {"High", "Medium", "Low", "Unknown"}:
        risk = "Unknown"

    return BaaScreenResponse(
        summary=str(data.get("summary", "")).strip(),
        ba_likely_required=bool(
            data.get("ba_likely_required", payload.creates_receives_maintains_or_transmits_phi)
        ),
        risk_level=risk,  # type: ignore[arg-type]
        required_clauses=[str(x) for x in data.get("required_clauses", []) if str(x).strip()][:8],
        diligence_questions=[
            str(x) for x in data.get("diligence_questions", []) if str(x).strip()
        ][:8],
        blockers=[str(x) for x in data.get("blockers", []) if str(x).strip()][:6],
        policy_citations=[str(x) for x in data.get("policy_citations", []) if str(x).strip()][:6],
        sources=sources,
        mode=mode,  # type: ignore[arg-type]
    )
