import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories import get_document_with_chunks
from app.db.session import get_db
from app.retrieval.search import search_chunks
from app.services.llm import (
    LLMConfigurationError,
    LLMProviderError,
    generate_answer,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    document_id: int | None = Field(default=None, ge=1)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace.")
        return value.strip()


@router.post("/")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="The language model is not configured.",
        )

    if request.document_id is not None:
        document = get_document_with_chunks(db, request.document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

    results = search_chunks(
        db=db,
        question=request.question,
        limit=request.limit,
        document_id=request.document_id,
    )

    if not results:
        return {
            "question": request.question,
            "answer": (
                "I couldn't find any relevant document content "
                "to answer your question."
            ),
            "document_id": request.document_id,
            "sources": [],
        }

    context_parts = []
    sources = []

    for index, (chunk, score) in enumerate(results, start=1):
        source_label = f"S{index}"

        context_parts.append(
            f"[{source_label}]\n"
            f"Filename: {chunk.document.filename}\n"
            f"Page: {chunk.page_number or 'Unknown'}\n"
            f"Content:\n{chunk.content}"
        )

        sources.append(
            {
                "source_id": source_label,
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "similarity_score": round(score, 4),
                "content": chunk.content,
            }
        )

    context = "\n\n---\n\n".join(context_parts)

    try:
        answer = generate_answer(
            question=request.question,
            context=context,
        )
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "question": request.question,
        "answer": answer,
        "document_id": request.document_id,
        "sources": sources,
    }
