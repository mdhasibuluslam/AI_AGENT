
import numpy as np

from psycopg.types.json import Jsonb

from database import get_connection
from embeddings import create_embedding


def init_knowledge_table():
    """Create a table for text and embedding vectors."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


def store_text(text: str):
    """Generate an embedding and save it with its text."""
    vector = create_embedding(text)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO knowledge_chunks
                    (content, embedding)
                VALUES (%s, %s);
                """,
                (text, Jsonb(vector)),
            )


def search_knowledge(query: str, top_k: int = 3):
    """Find semantically similar text using cosine similarity."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_vector = np.array(
        create_embedding(query),
        dtype=np.float32,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content, embedding
                FROM knowledge_chunks;
                """
            )
            rows = cur.fetchall()

    results = []

    for row_id, content, stored_vector in rows:
        vector = np.array(
            stored_vector,
            dtype=np.float32,
        )

        # Embeddings are normalized, so dot product
        # is cosine similarity (subject to floating-point rounding).
        score = float(np.dot(query_vector, vector))

        results.append(
            {
                "id": row_id,
                "content": content,
                "similarity": score,
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]


if __name__ == "__main__":
    init_knowledge_table()

    sample_texts = [
        "Our laptop comes with a one-year warranty.",
        "Customers can return eligible products within 30 days.",
        "The MacBook is suitable for programming and software development.",
        "Orders are shipped after payment confirmation.",
    ]

    # Seed only once for this simple demonstration.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM knowledge_chunks;"
            )
            count = cur.fetchone()[0]

    if count == 0:
        for text in sample_texts:
            store_text(text)

        print("Sample knowledge saved.")

    query = "I need a computer for coding"
    results = search_knowledge(query)

    print("\nQuery:", query)

    for item in results:
        print(
            f"\nSimilarity: {item['similarity']:.4f}"
        )
        print("Text:", item["content"])