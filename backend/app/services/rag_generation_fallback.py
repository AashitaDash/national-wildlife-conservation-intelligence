import logging
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.schemas.chat import ChatResponse, ChatSourceItem, ChatRetrievalMetadata

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=ChatResponse)
def generate_fallback_answer(
    question: str,
    sources: List[ChatSourceItem],
    retrieval_meta: ChatRetrievalMetadata,
    conversation_history: List[Dict[str, Any]] = None,
):
    """Fallback generation when no LLM provider is available.
    Simply concatenates the top N source snippets into a plain answer.
    """
    # Assemble snippets (limit to 5 for brevity)
    snippet_texts = [s.snippet for s in sources[:5]]
    answer_body = " ".join(snippet_texts).strip()
    if not answer_body:
        answer_body = "No relevant information found."
    answer = f"[Retrieval‑only] {answer_body}"
    # Return response preserving original metadata
    return ChatResponse(
        answer=answer,
        sources=sources,
        retrieval_metadata=retrieval_meta,
        conversation_id=None,
    )

# Provide a simple engine object compatible with the original import pattern
class _FallbackEngine:
    def generate_answer(self, question: str, sources: List[ChatSourceItem], retrieval_meta: ChatRetrievalMetadata, conversation_history: List[Dict[str, Any]] = None):
        # Reuse the fallback answer function
        return generate_fallback_answer(
            question=question,
            sources=sources,
            retrieval_meta=retrieval_meta,
            conversation_history=conversation_history,
        )

# Export as rag_generation_engine to match expected name
rag_generation_engine = _FallbackEngine()
