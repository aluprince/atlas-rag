from sqlalchemy.orm import Session

from app.db.models import DocumentChunk
from app.db.repositories import search_similar_chunks_with_scores
from app.embeddings.encoder import embed_text


def search_chunks(
    db: Session,
    question: str,
    limit: int = 5,
    document_id: int | None = None,
) -> list[tuple[DocumentChunk, float]]:
    """Embed a question and retrieve matching chunks with scores."""
    if not question or not question.strip():
        raise ValueError("Search question cannot be empty.")

    query_embedding = embed_text(question)

    return search_similar_chunks_with_scores(
        db=db,
        query_embedding=query_embedding,
        limit=limit,
        document_id=document_id,
    )
