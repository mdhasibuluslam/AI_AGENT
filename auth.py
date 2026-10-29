import os 
from datetime import datetime , timedelta, timezone
import jwt
from pwdlib import PasswordHash

Password_hash = PasswordHash.recommended()


jwt_sc = os.getenv("JWT_SECRET_KEY")
if not jwt_sc:
    raise RuntimeError("jwt secret key is missing from environment variables.")
jhw_al = "HS256"
Access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
if not 1<=Access_token_expire_minutes<=1440:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440.")

def hash_password(password: str) -> str:
    """Hash a password using pwdlib."""
    return Password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return Password_hash.verify(password, hashed_password)

def create_access_token(user_id: str) -> str:
    """Create a JWT access token for a user."""
    now = datetime.now(timezone.utc)
    expire = timedelta(minutes=Access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expire,
    }
    return jwt.encode(payload, jwt_sc, algorithm=jhw_al)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        jwt_sc,
        algorithms=[jhw_al],
        options={"require": ["exp", "iat", "sub"]},
    )

    user_id = int(payload["sub"])

    if user_id <= 0:
        raise ValueError("Invalid token subject.")

    return user_id

