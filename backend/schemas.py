"""Typed API envelopes for Lumina — structured internal protocol, not freeform prose."""

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["High", "Medium", "Low", "Unknown"]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceDoc(BaseModel):
    source: str
    snippet: str | None = None


class AskResponse(BaseModel):
    answer: str
    citation: str = ""
    confidence: Confidence = "Unknown"
    sources: list[str] = Field(default_factory=list)
    source_documents: list[SourceDoc] = Field(default_factory=list)
    refused: bool = False


class UploadFileResult(BaseModel):
    filename: str
    status: str
    preview: str | None = None
    chunks: int | None = None


class UploadResponse(BaseModel):
    summary: str
    results: list[UploadFileResult]


class HealthResponse(BaseModel):
    status: str
    message: str
    vector_store_ready: bool
    document_chunks: int
    model: str


class DocumentInfo(BaseModel):
    source: str
    chunks: int


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]
    total_chunks: int


class SuggestionItem(BaseModel):
    question: str
    category: str = "general"


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]


class RiskFinding(BaseModel):
    title: str
    severity: Literal["High", "Medium", "Low"]
    detail: str
    recommendation: str = ""


class RiskScanResponse(BaseModel):
    summary: str
    findings: list[RiskFinding] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class BreachClockRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=4000)
    discovered_at: str = Field(
        ...,
        description="ISO date or datetime when the incident was discovered (YYYY-MM-DD).",
    )
    phi_involved: bool = True
    individuals_affected: int | None = Field(default=None, ge=0)
    unauthorized_recipient: str = Field(default="", max_length=500)


class BreachFactor(BaseModel):
    factor: str
    assessment: str
    risk: Literal["High", "Medium", "Low", "Unknown"] = "Unknown"


class BreachClockResponse(BaseModel):
    summary: str
    notification_deadline: str
    days_remaining: int | None = None
    likely_reportable: bool
    four_factor: list[BreachFactor] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    policy_citations: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    mode: Literal["policy_grounded", "fallback"] = "fallback"


class AccessRequestGuideRequest(BaseModel):
    request_type: Literal["access", "amendment", "restriction", "accounting"] = "access"
    received_at: str = Field(..., description="ISO date the request was received.")
    channel: str = Field(default="patient portal", max_length=120)
    notes: str = Field(default="", max_length=2000)


class AccessRequestGuideResponse(BaseModel):
    summary: str
    statutory_deadline: str
    days_remaining: int | None = None
    checklist: list[str] = Field(default_factory=list)
    denial_or_delay_rules: list[str] = Field(default_factory=list)
    policy_citations: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    mode: Literal["policy_grounded", "fallback"] = "fallback"


class BaaScreenRequest(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=200)
    services: str = Field(..., min_length=5, max_length=2000)
    creates_receives_maintains_or_transmits_phi: bool = True
    notes: str = Field(default="", max_length=2000)


class BaaScreenResponse(BaseModel):
    summary: str
    ba_likely_required: bool
    risk_level: Literal["High", "Medium", "Low", "Unknown"] = "Unknown"
    required_clauses: list[str] = Field(default_factory=list)
    diligence_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    policy_citations: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    mode: Literal["policy_grounded", "fallback"] = "fallback"

