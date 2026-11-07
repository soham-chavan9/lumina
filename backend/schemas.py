"""Typed API envelopes for Lumina — structured internal protocol, not freeform prose."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Confidence = Literal["High", "Medium", "Low", "Unknown"]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceDoc(BaseModel):
    source: str
    snippet: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    citation: str = ""
    confidence: Confidence = "Unknown"
    sources: List[str] = Field(default_factory=list)
    source_documents: List[SourceDoc] = Field(default_factory=list)
    refused: bool = False


class UploadFileResult(BaseModel):
    filename: str
    status: str
    preview: Optional[str] = None
    chunks: Optional[int] = None


class UploadResponse(BaseModel):
    summary: str
    results: List[UploadFileResult]


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
    documents: List[DocumentInfo]
    total_chunks: int


class SuggestionItem(BaseModel):
    question: str
    category: str = "general"


class SuggestionsResponse(BaseModel):
    suggestions: List[SuggestionItem]


class RiskFinding(BaseModel):
    title: str
    severity: Literal["High", "Medium", "Low"]
    detail: str
    recommendation: str = ""


class RiskScanResponse(BaseModel):
    summary: str
    findings: List[RiskFinding] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class BreachClockRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=4000)
    discovered_at: str = Field(
        ...,
        description="ISO date or datetime when the incident was discovered (YYYY-MM-DD).",
    )
    phi_involved: bool = True
    individuals_affected: Optional[int] = Field(default=None, ge=0)
    unauthorized_recipient: str = ""


class BreachFactor(BaseModel):
    factor: str
    assessment: str
    risk: Literal["High", "Medium", "Low", "Unknown"] = "Unknown"


class BreachClockResponse(BaseModel):
    summary: str
    notification_deadline: str
    days_remaining: Optional[int] = None
    likely_reportable: bool
    four_factor: List[BreachFactor] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)
    policy_citations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class AccessRequestGuideRequest(BaseModel):
    request_type: Literal["access", "amendment", "restriction", "accounting"] = "access"
    received_at: str = Field(..., description="ISO date the request was received.")
    channel: str = Field(default="patient portal", max_length=120)
    notes: str = Field(default="", max_length=2000)


class AccessRequestGuideResponse(BaseModel):
    summary: str
    statutory_deadline: str
    days_remaining: Optional[int] = None
    checklist: List[str] = Field(default_factory=list)
    denial_or_delay_rules: List[str] = Field(default_factory=list)
    policy_citations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class BaaScreenRequest(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=200)
    services: str = Field(..., min_length=5, max_length=2000)
    creates_receives_maintains_or_transmits_phi: bool = True
    notes: str = Field(default="", max_length=2000)


class BaaScreenResponse(BaseModel):
    summary: str
    ba_likely_required: bool
    risk_level: Literal["High", "Medium", "Low", "Unknown"] = "Unknown"
    required_clauses: List[str] = Field(default_factory=list)
    diligence_questions: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    policy_citations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

