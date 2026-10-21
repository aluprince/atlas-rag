from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.repositories import get_document_with_chunks
from app.db.session import get_db
from app.retrieval.search import search_chunks

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    document_id: int | None = Field(default=None, ge=1)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace.")
        return value.strip()


@router.post("/")
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
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

    return {
        "question": request.question,
        "document_id": request.document_id,
        "result_count": len(results),
        "results": [
            {
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "similarity_score": round(score, 4),
            }
            for chunk, score in results
        ],
    }
