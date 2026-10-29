
from database import get_connection


def get_history(conversation_id: str):
    """Load conversation messages in their original order."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY id ASC;
                """,
                (conversation_id,),
            )

            rows = cur.fetchall()

    return [
        {"role": role, "content": content}
        for role, content in rows
    ]


def save_message(
    conversation_id: str,
    role: str,
    content: str,
):
    """Save one message to PostgreSQL."""
    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation_messages
                    (conversation_id, role, content)
                VALUES (%s, %s, %s);
                """,
                (conversation_id, role, content),
            )