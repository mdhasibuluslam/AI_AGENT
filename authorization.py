# authorization.py

from fastapi import Depends, HTTPException

from database import get_connection
from auth_dependencies import get_current_user_id


def get_user_roles(user_id: int) -> set[str]:
    """Return the current roles assigned to a user."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                """,
                (user_id,),
            )
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def get_user_permissions(user_id: int) -> set[str]:
    """Return permissions granted through the user's roles."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.name
                FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                """,
                (user_id,),
            )
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def has_permission(user_id: int, permission: str) -> bool:
    return permission in get_user_permissions(user_id)


def require_permission(permission: str):
    """Build a FastAPI dependency for a required permission."""

    def permission_checker(
        user_id: int = Depends(get_current_user_id),
    ) -> int:
        if not has_permission(user_id, permission):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action.",
            )

        return user_id

    return permission_checker