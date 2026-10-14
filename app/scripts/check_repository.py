
from app.db.session import SessionLocal
from app.db.repositories import (
    create_document_with_chunks,
    get_document_with_chunks,
    delete_document,
)
from app.ingestion.chunker import DocumentChunk


def main():
    with SessionLocal() as db:
        document = create_document_with_chunks(
            db,
            "repository-check.txt",
            ".txt",
            [
                DocumentChunk(
                    content="Repository persistence works.",
                    chunk_index=1,
                    page_number=None,
                )
            ],
        )

        document_id = document.id

        print(f"Saved: {document_id}, {document.filename}")
        print(f"Chunks: {len(document.chunks)}")

        loaded = get_document_with_chunks(db, document_id)
        print(f"Fetched: {loaded.chunks[0].content}")

        print(f"Deleted: {delete_document(db, document_id)}")


if __name__ == "__main__":
    main()
