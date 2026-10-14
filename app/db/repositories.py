
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Document, DocumentChunk
from app.ingestion.chunker import DocumentChunk as ChunkInput
from app.embeddings.encoder import embed_texts


def create_document_with_chunks(
    db: Session,
    filename: str,
    file_type: str,
    chunks: list[ChunkInput],
) -> Document:
    """Persist a document and all its chunks atomically."""

    # Validate inputs before running the embedding model.
    for chunk in chunks:
        if not isinstance(chunk.content, str) or not chunk.content.strip():
            raise ValueError("Chunk content cannot be empty.")

    try:
        # Generate all embeddings in one batch.
        embeddings = embed_texts([chunk.content for chunk in chunks])

        document = Document(
            filename=filename,
            file_type=file_type,
        )

        db.add(document)
        db.flush()  # Assign the document ID before creating its chunks.

        for chunk, embedding in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    embedding=embedding,
                )
            )

        db.commit()
        return get_document_with_chunks(db, document.id)

    except Exception:
        db.rollback()
        raise


def get_document_with_chunks(
    db: Session,
    document_id: int,
) -> Document | None:
    """Fetch a document and its chunks, or return None."""
    statement = (
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )

    return db.scalar(statement)


def delete_document(
    db: Session,
    document_id: int,
) -> bool:
    """Delete a document and its associated chunks."""
    document = get_document_with_chunks(db, document_id)

    if document is None:
        return False

    try:
        db.delete(document)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise



def search_similar_chunks(
    db: Session,
    query_embedding: list[float],
    limit: int = 5,
) -> list[DocumentChunk]:
    """Return chunks ranked by cosine similarity to a query embedding."""
    if len(query_embedding) != 384:
        raise ValueError("Query embedding must contain 384 dimensions.")

    if limit < 1:
        raise ValueError("Search limit must be at least 1.")

    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )

    return list(db.scalars(statement).all())
