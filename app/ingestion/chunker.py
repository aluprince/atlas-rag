from dataclasses import dataclass

from app.ingestion.loaders import DocumentPage


@dataclass
class DocumentChunk:
    content: str
    chunk_index: int
    page_number: int | None


def chunk_document(
    pages: list[DocumentPage],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[DocumentChunk]:
    """
    Split document pages into overlapping chunks.

    Chunks are created within individual pages so that
    page-level source metadata is preserved.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    chunks: list[DocumentChunk] = []
    chunk_index = 1

    for page in pages:
        paragraphs = _split_paragraphs(page.text)
        current_chunk = ""

        for paragraph in paragraphs:
            if not current_chunk:
                current_chunk = paragraph
                continue

            candidate = f"{current_chunk}\n\n{paragraph}"

            if len(candidate) <= chunk_size:
                current_chunk = candidate
                continue

            chunks.append(
                DocumentChunk(
                    content=current_chunk,
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                )
            )

            chunk_index += 1

            overlap = _get_overlap(
                current_chunk,
                chunk_overlap,
            )

            current_chunk = (
                f"{overlap}\n\n{paragraph}"
                if overlap
                else paragraph
            )

            while len(current_chunk) > chunk_size:
                split_point = _find_split_point(
                    current_chunk,
                    chunk_size,
                )

                chunks.append(
                    DocumentChunk(
                        content=current_chunk[:split_point].strip(),
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                    )
                )

                chunk_index += 1

                overlap = _get_overlap(
                    current_chunk[:split_point],
                    chunk_overlap,
                )

                remaining = current_chunk[split_point:].strip()

                current_chunk = (
                    f"{overlap} {remaining}"
                    if overlap
                    else remaining
                )

        if current_chunk:
            chunks.append(
                DocumentChunk(
                    content=current_chunk,
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                )
            )

            chunk_index += 1

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """Split text into clean, non-empty paragraphs."""
    return [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]


def _find_split_point(text: str, max_length: int) -> int:
    """
    Find a natural split point at or before max_length.

    Prefer whitespace so we don't split words in half.
    """
    if len(text) <= max_length:
        return len(text)

    split_point = text.rfind(" ", 0, max_length)

    if split_point == -1:
        return max_length

    return split_point


def _get_overlap(text: str, overlap_size: int) -> str:
    """
    Return a word-aware trailing portion of text.

    The returned overlap will not begin in the middle
    of a word.
    """
    if overlap_size == 0:
        return ""

    start = max(0, len(text) - overlap_size)

    if start == 0:
        return text

    while start < len(text) and not text[start].isspace():
        start += 1

    return text[start:].strip()