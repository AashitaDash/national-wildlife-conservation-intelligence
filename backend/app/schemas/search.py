from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SearchQueryRequest(BaseModel):
    query: str
    species_id: Optional[int] = None
    location_id: Optional[int] = None
    threat_category: Optional[str] = None
    source_type: Optional[str] = None
    hybrid_alpha: Optional[float] = 0.5  # 0.0 = purely keyword BM25/like, 1.0 = purely vector semantic
    limit: Optional[int] = 20


class SearchResultItem(BaseModel):
    id: int
    entity_type: str  # "DOCUMENT", "OBSERVATION", "SPECIES"
    title: str
    snippet: str
    relevance_score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
