import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.rag_service import rag_retrieval_engine, rag_generation_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["RAG AI Assistant"])


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask the grounded Wildlife Conservation RAG AI Assistant",
    description=(
        "Retrieves multi-source platform evidence (PostgreSQL species records, observation stats, "
        "threats, risk scores, and research document chunks) and synthesizes an evidence-grounded response "
        "with verifiable citations ([S1], [S2]). Untrusted document content is isolated against prompt injections."
    )
)
def ask_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Authenticated endpoint for the RAG chatbot assistant.
    Guarantees strict grounding against database records and research document embeddings.
    """
    clean_question = request.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The question field cannot be empty or contain only whitespace."
        )

    if len(clean_question) > 2000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The question exceeds the maximum length of 2000 characters."
        )

    try:
        # Step 1: Query Preprocessing & Intent Detection & Multi-source Hybrid Retrieval
        sources, retrieval_meta = rag_retrieval_engine.retrieve(db, clean_question)

        # Step 2: Context Assembly & Grounded LLM Generation with Citation Validation
        response = rag_generation_engine.generate_answer(
            question=clean_question,
            sources=sources,
            retrieval_meta=retrieval_meta,
            conversation_history=request.conversation_history
        )
        
        # Attach caller's conversation_id if provided
        if request.conversation_id:
            response.conversation_id = request.conversation_id

        return response

    except Exception as e:
        logger.error(f"Error during RAG execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the assistant response: {str(e)}"
        )
