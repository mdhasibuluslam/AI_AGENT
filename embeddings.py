
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the model once per Python process."""
    return SentenceTransformer(MODEL_NAME)


def create_embedding(text: str) -> list[float]:
    """Convert text into a numerical embedding."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    vector = model.encode(
        text.strip(),
        normalize_embeddings=True,
    )

    return vector.tolist()


if __name__ == "__main__":
    text = "I need a laptop for programming"
    vector = create_embedding(text)

    print("Text:", text)
    print("Vector dimensions:", len(vector))
    print("First 5 values:", vector[:5])