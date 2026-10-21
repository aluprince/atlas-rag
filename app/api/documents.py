from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.repositories import create_document_with_chunks
from app.db.session import get_db
from app.ingestion.chunker import chunk_document
from app.ingestion.loaders import (
    DocumentLoaderError,
    SUPPORTED_EXTENSIONS,
    load_document,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a PDF, DOCX, TXT, or MD file.",
        )

    temp_path = None

    try:
        content = file.file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the 10 MB upload limit.",
            )

        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        pages = load_document(str(temp_path))

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the document.",
            )

        chunks = chunk_document(pages)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks could be created from this document.",
            )

        document = create_document_with_chunks(
            db=db,
            filename=filename,
            file_type=extension,
            chunks=chunks,
        )

        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "chunk_count": len(document.chunks),
            "status": "processed",
        }

    except DocumentLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        file.file.close()
