
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Document, DocumentChunk
from app.db.repositories import (
    create_document_with_chunks,
    delete_document,
    get_document_with_chunks,
)
from app.ingestion.chunker import DocumentChunk as ChunkInput


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def mock_embedding_generation(monkeypatch):
    """Use fake vectors so repository tests don't load the real model."""
    def fake_embed_texts(texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]

    monkeypatch.setattr(
        "app.db.repositories.embed_texts",
        fake_embed_texts,
    )


def test_create_document_with_chunks(db: Session):
    chunks = [
        ChunkInput(
            content="First chunk",
            chunk_index=1,
            page_number=1,
        ),
        ChunkInput(
            content="Second chunk",
            chunk_index=2,
            page_number=2,
        ),
    ]

    document = create_document_with_chunks(
        db=db,
        filename="handbook.pdf",
        file_type=".pdf",
        chunks=chunks,
    )

    assert document.id is not None
    assert document.filename == "handbook.pdf"
    assert document.file_type == ".pdf"
    assert len(document.chunks) == 2
    assert document.chunks[0].content == "First chunk"
    assert document.chunks[1].page_number == 2
    assert all(chunk.embedding is not None for chunk in document.chunks)
    assert all(len(chunk.embedding) == 384 for chunk in document.chunks)


def test_get_missing_document_returns_none(db: Session):
    result = get_document_with_chunks(db, document_id=999)

    assert result is None


def test_delete_document_also_deletes_chunks(db: Session):
    document = create_document_with_chunks(
        db=db,
        filename="handbook.pdf",
        file_type=".pdf",
        chunks=[
            ChunkInput(
                content="A saved chunk",
                chunk_index=1,
                page_number=1,
            )
        ],
    )
    document_id = document.id

    assert delete_document(db, document_id) is True
    assert get_document_with_chunks(db, document_id) is None

    remaining_chunks = db.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
    )
    assert remaining_chunks == 0

    assert delete_document(db, document_id) is False


def test_invalid_chunk_is_rejected_before_saving_document(db: Session):
    invalid_chunks = [
        ChunkInput(
            content=None,
            chunk_index=1,
            page_number=1,
        )
    ]

    with pytest.raises(
        ValueError,
        match="Chunk content cannot be empty",
    ):
        create_document_with_chunks(
            db=db,
            filename="invalid.pdf",
            file_type=".pdf",
            chunks=invalid_chunks,
        )

    document_count = db.scalar(
        select(func.count()).select_from(Document)
    )
    assert document_count == 0
