
from fastapi import UploadFile

from database import get_connection
from file_upload import extract_uploaded_text


async def process_uploaded_file(file: UploadFile) -> dict:
    """Extract text without exposing internal errors."""
    return await extract_uploaded_text(file)


def save_uploaded_file(user_id: int, extracted: dict) -> dict:
    """Store an authenticated user's extracted document in PostgreSQL."""

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    filename = extracted["filename"]
    file_type = extracted["content_type"]
    text = extracted["text"]
    characters = extracted["characters"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO uploaded_files (
                    user_id,
                    original_filename,
                    file_type,
                    character_count,
                    extracted_text
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, original_filename, file_type,
                          character_count, created_at
                """,
                (user_id, filename, file_type, characters, text),
            )
            row = cur.fetchone()

    return {
        "id": row[0],
        "filename": row[1],
        "file_type": row[2],
        "characters": row[3],
        "created_at": row[4],
    }


def list_user_files(user_id: int) -> list[dict]:
    """Return metadata for the authenticated user's own uploads."""

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, original_filename, file_type,
                       character_count, created_at
                FROM uploaded_files
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "filename": row[1],
            "file_type": row[2],
            "characters": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]
