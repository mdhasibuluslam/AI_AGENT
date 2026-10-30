
from database import get_connection


def save_document_chunks(
    user_id: int,
    file_id: int,
    chunks: list[str],
) -> int:
    """Save chunks only if the uploaded file belongs to this user."""

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or user_id <= 0
    ):
        raise ValueError("Invalid user ID.")

    if (
        not isinstance(file_id, int)
        or isinstance(file_id, bool)
        or file_id <= 0
    ):
        raise ValueError("Invalid file ID.")

    if not isinstance(chunks, list) or not chunks:
        raise ValueError("Chunks must be a non-empty list.")

    if any(
        not isinstance(chunk, str) or not chunk.strip()
        for chunk in chunks
    ):
        raise ValueError("Every chunk must contain text.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Verify ownership using the authenticated user ID.
            cur.execute(
                """
                SELECT id
                FROM uploaded_files
                WHERE id = %s AND user_id = %s
                FOR UPDATE
                """,
                (file_id, user_id),
            )

            if cur.fetchone() is None:
                raise PermissionError(
                    "File not found or access denied."
                )

            # Replace previous chunks atomically.
            cur.execute(
                """
                DELETE FROM document_chunks
                WHERE file_id = %s AND user_id = %s
                """,
                (file_id, user_id),
            )

            cur.executemany(
                """
                INSERT INTO document_chunks (
                    user_id, file_id, chunk_index, chunk_text
                )
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (user_id, file_id, index, chunk.strip())
                    for index, chunk in enumerate(chunks)
                ],
            )

    return len(chunks)
