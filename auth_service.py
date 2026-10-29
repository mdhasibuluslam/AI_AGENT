from database import get_connection
from auth import hash_password, verify_password, create_access_token

class EmailAlreadyExistsError(Exception):
    """Raised when trying to register an email that already exists."""
    pass

class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""
    pass

def init_auth_tables() -> None:
    """Create the users table if it doesn't exist."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_conversations (
                    conversation_id VARCHAR(100) PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id)
                        ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()
            
            

def register_user(email: str, password: str) -> int:
    """Register a new user and assign the default customer role."""
    normalized_email = email.strip().lower()
    hashed_password = hash_password(password)

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # 1. Create the user.
            cursor.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
                """,
                (normalized_email, hashed_password),
            )
            result = cursor.fetchone()

            if result is None:
                raise EmailAlreadyExistsError(
                    f"Email {normalized_email} is already registered."
                )

            user_id = int(result[0])

            # 2. Assign the default customer role.
            cursor.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s, id
                FROM roles
                WHERE name = 'customer'
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                (user_id,),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Default customer role could not be assigned. "
                    "Check that the 'customer' role exists."
                )
                

        # 3. Commit both changes together.
        connection.commit()
        return user_id

    except EmailAlreadyExistsError:
        connection.rollback()
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

        
def login_users(email:str, password:str) -> str:
    """Authenticate a user and return an access token."""
    normalized_email = email.strip().lower()
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE email = %s;",
                (normalized_email,)
            )
            result = cursor.fetchone()
            if not result:
                raise InvalidCredentialsError("Invalid email or password.")
            user_id, stored_password_hash = result
            if not verify_password(password, stored_password_hash):
                raise InvalidCredentialsError("Invalid email or password.")
            access_token = create_access_token(user_id)
        return access_token
    except InvalidCredentialsError:
        raise
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()
        
        
        

def claim_conversation(user_id: int, conversation_id: str) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # First check whether the conversation already has an owner.
            cur.execute(
                """
                SELECT user_id
                FROM user_conversations
                WHERE conversation_id = %s
                """,
                (conversation_id,),
            )
            row = cur.fetchone()

            if row is not None:
                if int(row[0]) != user_id:
                    raise PermissionError(
                        "You do not have access to this conversation."
                    )
                conn.commit()
                return

            # Do not let a user claim legacy history with no owner.
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM conversation_messages
                    WHERE conversation_id = %s
                )
                """,
                (conversation_id,),
            )
            has_legacy_messages = cur.fetchone()[0]

            if has_legacy_messages:
                raise PermissionError(
                    "This legacy conversation needs a trusted migration."
                )

            # Claim only a new, unused conversation ID.
            cur.execute(
                """
                INSERT INTO user_conversations (conversation_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT (conversation_id) DO NOTHING
                """,
                (conversation_id, user_id),
            )

            cur.execute(
                """
                SELECT user_id
                FROM user_conversations
                WHERE conversation_id = %s
                """,
                (conversation_id,),
            )
            owner = cur.fetchone()

            if owner is None or int(owner[0]) != user_id:
                raise PermissionError(
                    "You do not have access to this conversation."
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()