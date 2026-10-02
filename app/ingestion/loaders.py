from dataclasses import dataclass
from pathlib import Path

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentLoaderError(Exception):
    """Raised when a document cannot be loaded."""


@dataclass
class DocumentPage:
    text: str
    page_number: int | None = None


def load_document(file_path: str) -> list[DocumentPage]:
    """
    Load a supported document and return its content as structured pages.

    PDF files preserve page numbers.
    DOCX, TXT, and Markdown are treated as single-page documents.
    """
    path = Path(file_path)

    if not path.exists():
        raise DocumentLoaderError(f"File not found: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentLoaderError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if extension == ".pdf":
        return _load_pdf(path)

    if extension == ".docx":
        return _load_docx(path)

    return _load_text(path)


def _load_pdf(path: Path) -> list[DocumentPage]:
    """Extract text from a PDF while preserving page numbers."""
    try:
        pages = []

        with pymupdf.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                if text:
                    pages.append(
                        DocumentPage(
                            text=text,
                            page_number=page_number,
                        )
                    )

        return pages

    except Exception as exc:
        raise DocumentLoaderError(
            f"Failed to read PDF: {path.name}"
        ) from exc


def _load_docx(path: Path) -> list[DocumentPage]:
    """Extract text from a DOCX file."""
    try:
        document = Document(path)

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        text = "\n\n".join(paragraphs)

        if not text:
            return []

        return [DocumentPage(text=text)]

    except Exception as exc:
        raise DocumentLoaderError(
            f"Failed to read DOCX: {path.name}"
        ) from exc


def _load_text(path: Path) -> list[DocumentPage]:
    """Load plain text or Markdown."""
    try:
        text = path.read_text(encoding="utf-8").strip()

        if not text:
            return []

        return [DocumentPage(text=text)]

    except UnicodeDecodeError as exc:
        raise DocumentLoaderError(
            f"Could not decode {path.name} as UTF-8."
        ) from exc

    except OSError as exc:
        raise DocumentLoaderError(
            f"Failed to read {path.name}."
        ) from exc


    