import pytest

from app.ingestion.chunker import (
    DocumentChunk,
    chunk_document,
)
from app.ingestion.loaders import DocumentPage


def test_chunk_document_returns_chunks():
    pages = [
        DocumentPage(
            text=(
                "Atlas RAG is an enterprise knowledge assistant. "
                "Employees can use Atlas to search internal documentation."
            ),
            page_number=1,
        )
    ]

    chunks = chunk_document(
        pages,
        chunk_size=60,
        chunk_overlap=10,
    )

    assert len(chunks) > 1
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)


def test_chunks_preserve_page_number():
    pages = [
        DocumentPage(
            text=(
                "This is content from page one. "
                "It contains enough information to create chunks."
            ),
            page_number=1,
        ),
        DocumentPage(
            text=(
                "This is content from page two. "
                "It contains different information."
            ),
            page_number=2,
        ),
    ]

    chunks = chunk_document(
        pages,
        chunk_size=40,
        chunk_overlap=5,
    )

    page_numbers = {chunk.page_number for chunk in chunks}

    assert page_numbers == {1, 2}


def test_chunk_indexes_start_at_one():
    pages = [
        DocumentPage(
            text="Atlas RAG is an enterprise knowledge assistant.",
            page_number=1,
        )
    ]

    chunks = chunk_document(
        pages,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert chunks[0].chunk_index == 1


def test_chunk_indexes_are_sequential():
    pages = [
        DocumentPage(
            text=(
                "Atlas RAG is an enterprise knowledge assistant. "
                "Employees can search documentation and ask questions "
                "about company policies and engineering procedures."
            ),
            page_number=1,
        )
    ]

    chunks = chunk_document(
        pages,
        chunk_size=50,
        chunk_overlap=10,
    )

    indexes = [chunk.chunk_index for chunk in chunks]

    assert indexes == list(range(1, len(chunks) + 1))


def test_chunks_do_not_exceed_chunk_size():
    pages = [
        DocumentPage(
            text=(
                "Atlas RAG is an enterprise knowledge assistant. "
                "Employees can search internal company documentation "
                "and ask questions about company policies."
            ),
            page_number=1,
        )
    ]

    chunk_size = 50

    chunks = chunk_document(
        pages,
        chunk_size=chunk_size,
        chunk_overlap=10,
    )

    for chunk in chunks:
        assert len(chunk.content) <= chunk_size


def test_empty_document_returns_no_chunks():
    pages = []

    chunks = chunk_document(pages)

    assert chunks == []


def test_empty_page_returns_no_chunks():
    pages = [
        DocumentPage(
            text="",
            page_number=1,
        )
    ]

    chunks = chunk_document(pages)

    assert chunks == []


def test_invalid_chunk_size_raises_error():
    pages = [
        DocumentPage(
            text="Some content.",
            page_number=1,
        )
    ]

    with pytest.raises(
        ValueError,
        match="chunk_size must be greater than 0",
    ):
        chunk_document(
            pages,
            chunk_size=0,
            chunk_overlap=0,
        )


def test_negative_overlap_raises_error():
    pages = [
        DocumentPage(
            text="Some content.",
            page_number=1,
        )
    ]

    with pytest.raises(
        ValueError,
        match="chunk_overlap cannot be negative",
    ):
        chunk_document(
            pages,
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_overlap_cannot_equal_chunk_size():
    pages = [
        DocumentPage(
            text="Some content.",
            page_number=1,
        )
    ]

    with pytest.raises(
        ValueError,
        match="chunk_overlap must be smaller than chunk_size",
    ):
        chunk_document(
            pages,
            chunk_size=100,
            chunk_overlap=100,
        )