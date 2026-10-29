from database import get_connection
from embeddings import create_embedding


def to_vector_literal(vector: list[float]) -> str:
    """Convert a numeric vector to pgvector's text format."""
    if not vector:
        raise ValueError("Vector cannot be empty.")

    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def init_vector_store():
    """Enable pgvector and migrate Step 12 embeddings."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            cur.execute("""
                ALTER TABLE knowledge_chunks
                ADD COLUMN IF NOT EXISTS embedding_vector vector(384);
            """)

            # Copy existing JSONB embeddings into native vector storage.
            cur.execute("""
                UPDATE knowledge_chunks
                SET embedding_vector = embedding::text::vector
                WHERE embedding_vector IS NULL;
            """)

            # Approximate nearest-neighbor index for cosine distance.
            cur.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_knowledge_chunks_embedding_hnsw
                ON knowledge_chunks
                USING hnsw (embedding_vector vector_cosine_ops);
            """)

        # The connection context commits on success.


def store_text(text: str) -> int:
    """Embed and store a new knowledge chunk."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    vector = create_embedding(text.strip())
    vector_literal = to_vector_literal(vector)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_chunks
                    (content, embedding, embedding_vector)
                VALUES (%s, %s::jsonb, %s::vector)
                RETURNING id;
            """, (
                text.strip(),
                __import__("json").dumps(vector),
                vector_literal,
            ))
            row = cur.fetchone()

    return row[0]


def search_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """Search PostgreSQL for the closest vectors."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    query_vector = to_vector_literal(create_embedding(query))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    content,
                    1 - (embedding_vector <=> %s::vector)
                        AS similarity
                FROM knowledge_chunks
                WHERE embedding_vector IS NOT NULL
                ORDER BY embedding_vector <=> %s::vector
                LIMIT %s;
            """, (query_vector, query_vector, top_k))

            rows = cur.fetchall()

    return [
        {
            "id": row_id,
            "content": content,
            "similarity": float(similarity),
        }
        for row_id, content, similarity in rows
    ]


if __name__ == "__main__":
    init_vector_store()
    print("Vector store initialized and existing embeddings migrated.")

    results = search_knowledge("I need a computer for coding", top_k=3)
    print("\nSemantic search results:")

    for item in results:
        print(f"\nID: {item['id']}")
        print(f"Similarity: {item['similarity']:.4f}")
        print(f"Text: {item['content']}")