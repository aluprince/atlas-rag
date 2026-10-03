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
            # If the paragraph itself is larger than the chunk size,
            # flush the current chunk first, then split the paragraph.
            if len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(
                        DocumentChunk(
                            content=current_chunk,
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                        )
                    )
                    chunk_index += 1

                    current_chunk = _get_overlap(
                        current_chunk,
                        chunk_overlap,
                    )

                split_chunks = _split_text(
                    paragraph,
                    chunk_size,
                    chunk_overlap,
                )

                for split_chunk in split_chunks[:-1]:
                    chunks.append(
                        DocumentChunk(
                            content=split_chunk,
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                        )
                    )
                    chunk_index += 1

                current_chunk = split_chunks[-1]
                continue

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

        if current_chunk:
            # current_chunk should never exceed chunk_size here,
            # but this keeps the invariant explicit.
            split_chunks = _split_text(
                current_chunk,
                chunk_size,
                chunk_overlap,
            )

            for split_chunk in split_chunks:
                chunks.append(
                    DocumentChunk(
                        content=split_chunk,
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


def _split_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """
    Split oversized text into word-aware chunks with overlap.
    """
    chunks: list[str] = []
    remaining = text.strip()

    while len(remaining) > chunk_size:
        split_point = _find_split_point(
            remaining,
            chunk_size,
        )

        chunk = remaining[:split_point].strip()

        if chunk:
            chunks.append(chunk)

        overlap = _get_overlap(
            chunk,
            chunk_overlap,
        )

        remaining_text = remaining[split_point:].strip()

        remaining = (
            f"{overlap} {remaining_text}"
            if overlap
            else remaining_text
        )

    if remaining:
        chunks.append(remaining)

    return chunks


def _find_split_point(text: str, max_length: int) -> int:
    """
    Find a natural split point at or before max_length.

    Prefer whitespace so words are not split in half.
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