
from functools import lru_cache
from typing import TYPE_CHECKING

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer":
    """Load the embedding model only when first needed."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Text to embed cannot be empty.")

    model = get_embedding_model()
    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if any(not text or not text.strip() for text in texts):
        raise ValueError("Texts to embed cannot contain empty strings.")

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return embeddings.tolist()
