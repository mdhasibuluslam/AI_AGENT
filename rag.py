
from pgvector import Vector
from pgvector.psycopg import register_vector

from database import get_connection
from embeddings import create_embedding



MAX_QUERY_LENGTH = 1000
MAX_RESULTS = 10


def retrieve_knowledge(
    query: str,
    limit: int = 4,
) -> list[dict]:
    """
    Retrieve relevant knowledge chunks using PostgreSQL and pgvector.
    """

    # 1. Validate query type
    if not isinstance(query, str):
        raise ValueError("Query must be a string.")

    query = query.strip()

    # 2. Reject empty or oversized queries
    if not query:
        raise ValueError("Query cannot be empty.")

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Query is too long.")

    # 3. Validate result limit
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= MAX_RESULTS
    ):
        raise ValueError(
            f"Limit must be an integer between 1 and {MAX_RESULTS}."
        )

    # 4. Generate embedding and retrieve results
    try:
        query_vector = create_embedding(query)
        vector = Vector(query_vector)

        with get_connection() as conn:
            register_vector(conn)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        content,
                        embedding_vector <=> %s AS distance
                    FROM knowledge_chunks
                    WHERE embedding_vector IS NOT NULL
                    ORDER BY embedding_vector <=> %s
                    LIMIT %s
                    """,
                    (vector, vector, limit),
                )

                rows = cur.fetchall()

        # 5. Return predictable output
        return [
            {
                "id": row[0],
                "content": row[1],
                "distance": float(row[2]),
            }
            for row in rows
        ]

    except Exception:
        # Never expose raw database or embedding errors to callers.
        raise RuntimeError(
            "Knowledge retrieval is temporarily unavailable."
        ) from None
