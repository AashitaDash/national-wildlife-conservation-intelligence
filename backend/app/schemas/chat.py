from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., max_length=5000, description="Message content text")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    conversation_id: Optional[str] = Field(None, max_length=100, description="Optional conversation tracking ID")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Bounded recent conversation turns")
    include_external: Optional[bool] = Field(False, description="Optionally include live external API queries")


class ChatSourceItem(BaseModel):
    id: str = Field(..., description="Stable source citation tag, e.g., 'S1', 'S2'")
    source_type: str = Field(..., description="'DATABASE', 'DOCUMENT', or 'EXTERNAL'")
    title: str = Field(..., description="Species, document title, or dataset name")
    reference: Optional[str] = Field(None, description="URL, record ID, or chunk reference")
    snippet: str = Field(..., description="Excerpt or structured facts used as grounding evidence")
    relevance_score: float = Field(..., description="Retrieval similarity score [0.0 - 1.0]")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")


class ChatRetrievalMetadata(BaseModel):
    intent: str
    db_species_retrieved: int = 0
    db_observations_retrieved: int = 0
    documents_retrieved: int = 0
    external_records_retrieved: int = 0
    llm_provider: str = "extractive_synthesizer"
    llm_model: str = "nlp-vector-hybrid"
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSourceItem]
    retrieval_metadata: ChatRetrievalMetadata
    conversation_id: Optional[str] = None
