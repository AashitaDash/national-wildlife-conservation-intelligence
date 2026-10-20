from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db
from backend.app.schemas.search import SearchQueryRequest, SearchResponse
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Multi-Modal Hybrid Search Engine"])


@router.post("", response_model=SearchResponse)
def execute_hybrid_search(
    search_req: SearchQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute hybrid search over documents, species profiles, and spatial intelligence.
    Fuses sparse lexical keyword scoring and dense vector semantic similarity.
    """
    results = SearchService.hybrid_search(
        db=db,
        query=search_req.query,
        species_id=search_req.species_id,
        source_type=search_req.source_type,
        hybrid_alpha=search_req.hybrid_alpha or 0.5,
        limit=search_req.limit or 20
    )
    return SearchResponse(
        query=search_req.query,
        total_results=len(results),
        results=results
    )


@router.get("", response_model=SearchResponse)
def get_hybrid_search(
    q: str = Query(..., description="Search query string"),
    species_id: Optional[int] = Query(None, description="Optional species filter"),
    source_type: Optional[str] = Query(None, description="Optional source type filter"),
    alpha: float = Query(0.5, ge=0.0, le=1.0, description="0.0 = lexical only, 1.0 = vector only"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Convenient GET endpoint for multi-modal hybrid search.
    """
    req = SearchQueryRequest(
        query=q,
        species_id=species_id,
        source_type=source_type,
        hybrid_alpha=alpha,
        limit=limit
    )
    return execute_hybrid_search(req, db)
