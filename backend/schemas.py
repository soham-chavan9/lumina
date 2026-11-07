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

