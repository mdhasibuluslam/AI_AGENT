
from contextvars import ContextVar, Token
from functools import wraps
from inspect import iscoroutinefunction

_current_user_id: ContextVar[int | None] = ContextVar(
    "current_tool_user_id",
    default=None,
)


def set_tool_user(user_id: int) -> Token:
    """Set authenticated user for the current execution context."""

    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        raise ValueError("Invalid user ID.")

    return _current_user_id.set(user_id)


def reset_tool_user(token: Token) -> None:
    """Restore the previous execution context."""
    _current_user_id.reset(token)


def check_tool_permission(permission: str) -> None:
    """Verify permission using the existing RBAC system."""

    user_id = _current_user_id.get()

    if user_id is None:
        raise PermissionError("Authenticated user context is missing.")

    from authorization import has_permission

    if not has_permission(user_id, permission):
        raise PermissionError("Permission denied.")


def require_tool_permission(permission: str):
    """Protect a sync or async tool before its business logic runs."""

    if not isinstance(permission, str) or not permission.strip():
        raise ValueError("Permission must be a non-empty string.")
    
    permission = permission.strip()

    def decorator(func):

        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    check_tool_permission(permission)
                except PermissionError:
                    return {
                        "success": False,
                        "error": "You are not authorized to use this tool.",
                    }

                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                check_tool_permission(permission)
            except PermissionError:
                return {
                    "success": False,
                    "error": "You are not authorized to use this tool.",
                }

            return func(*args, **kwargs)

        return sync_wrapper

    return decorator
