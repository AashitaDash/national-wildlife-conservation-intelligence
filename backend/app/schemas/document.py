from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    source_type: str = "INCIDENT_LOG"  # RESEARCH_PAPER, GOVT_REPORT, INCIDENT_LOG, ARTICLE
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    raw_text: str


class DocumentCreate(DocumentBase):
    pass


class ThreatExtractionItem(BaseModel):
    threat_id: int
    category_name: str
    mention_count: int
    confidence_score: float


class SpeciesExtractionItem(BaseModel):
    species_id: int
    common_name: str
    scientific_name: str
    mention_count: int


class DocumentResponse(BaseModel):
    id: int
    title: str
    source_type: str
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    species_mentions: Optional[List[SpeciesExtractionItem]] = []
    threat_mentions: Optional[List[ThreatExtractionItem]] = []

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    cleaned_text: Optional[str] = None
    nlp_results: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Multi-Document Conservation Synthesis schemas
# ─────────────────────────────────────────────────────────────────────────────

class SynthesisRequest(BaseModel):
    """Request body for POST /documents/synthesize."""
    document_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of document IDs to synthesise. At least one required.",
    )


class EvidenceItem(BaseModel):
    """A single supporting evidence sentence with source provenance."""
    sentence: str
    document_id: int
    document_title: str
    relevance: float


class SourceDocumentSummary(BaseModel):
    """Lightweight source-document provenance record."""
    id: int
    title: str
    source_type: str
    author: Optional[str] = None
    summary: Optional[str] = None
    relevance_score: Optional[float] = None
    snippet: Optional[str] = None


class SynthesisResponse(BaseModel):
    """Conservation Intelligence Brief returned by /documents/synthesize."""
    summary: str
    species: List[Dict[str, Any]]
    threats: List[Dict[str, Any]]
    topics: List[Dict[str, Any]]
    documents_analyzed: int
    evidence: List[EvidenceItem]
    evidence_strength: str          # HIGH | MEDIUM | LOW | INSUFFICIENT
    conflicting_evidence: bool
    source_documents: List[SourceDocumentSummary]
    missing_document_ids: List[int]
    evidence_strength_rationale: str


# ─────────────────────────────────────────────────────────────────────────────
# Evidence-Grounded Question Answering schemas
# ─────────────────────────────────────────────────────────────────────────────

class QARequest(BaseModel):
    """Request body for POST /documents/ask."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="A natural-language question about the indexed conservation corpus.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of documents to retrieve from hybrid search.",
    )


class QAResponse(BaseModel):
    """Evidence-grounded answer returned by /documents/ask."""
    question: str
    answer: str
    evidence: List[EvidenceItem]
    evidence_strength: str          # HIGH | MEDIUM | LOW | INSUFFICIENT
    conflicting_evidence: bool
    source_documents: List[SourceDocumentSummary]
    retrieved_species: List[str]
    retrieved_threats: List[str]
    evidence_strength_rationale: str
    diagnostic_metadata: Optional[Dict[str, Any]] = None

