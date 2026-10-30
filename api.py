
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
import os

from agent_service import chat
from auth_service import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    claim_conversation,
    init_auth_tables,
    login_users,
    register_user,
)
from file_service import (
    process_uploaded_file,
    save_uploaded_file,
    list_user_files,
)
from authorization import require_permission
from fastapi import File, UploadFile, Depends
from file_service import process_uploaded_file
from document_ingestion import split_text_into_chunks
from document_storage import save_document_chunks
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create auth tables before serving requests.
    init_auth_tables()
    yield


app = FastAPI(
    title="AI Business Support Agent",
    description="Authenticated API for the Gemini-powered agent",
    version="1.1.0",
    lifespan=lifespan,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value):
        if not isinstance(value, str):
            raise ValueError("password must be a string.")

        if len(value) < 12:
            raise ValueError("password must be at least 12 characters long.")

        return value
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value):
        if not isinstance(value, str):
            raise ValueError("email must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("email cannot be empty.")

        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value):
        if not isinstance(value, str):
            raise ValueError("password must be a string.")

        if len(value) < 1:
            raise ValueError("password must be at least 1 character long.")

        return value
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value):
        if not isinstance(value, str):
            raise ValueError("email must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("email cannot be empty.")

        return value


class RegisterResponse(BaseModel):
    user_id: int
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value):
        if not isinstance(value, str):
            raise ValueError("email must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("email cannot be empty.")

        return value



class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    @field_validator("expires_in", mode="before")
    @classmethod
    def validate_expires_in(cls, value):
        if not isinstance(value, int):
            raise ValueError("expires_in must be an integer.")

        if value <= 0:
            raise ValueError("expires_in must be a positive integer.")

        return value
    @field_validator("access_token", mode="before")
    @classmethod
    def validate_access_token(cls, value):
        if not isinstance(value, str):
            raise ValueError("access_token must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("access_token cannot be empty.")

        return value
    @field_validator("token_type", mode="before")
    @classmethod
    def validate_token_type(cls, value):
        if not isinstance(value, str):
            raise ValueError("token_type must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("token_type cannot be empty.")

        return value



class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: str = Field(min_length=1, max_length=100)

    @field_validator("message", mode="before")
    @classmethod
    def validate_message(cls, value):
        if not isinstance(value, str):
            raise ValueError("Message must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty.")

        if len(value) > 5000:
            raise ValueError("Message cannot exceed 5000 characters.")

        return value

    @field_validator("conversation_id", mode="before")
    @classmethod
    def validate_conversation_id(cls, value):
        if not isinstance(value, str):
            raise ValueError("Conversation ID must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("Conversation ID cannot be empty.")

        if len(value) > 100:
            raise ValueError("Conversation ID cannot exceed 100 characters.")

        return value


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    @field_validator("answer", mode="before")
    @classmethod
    def validate_answer(cls, value):
        if not isinstance(value, str):
            raise ValueError("Answer must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("Answer cannot be empty.")

        return value
    @field_validator("conversation_id", mode="before")
    @classmethod
    def validate_conversation_id(cls, value):
        if not isinstance(value, str):
            raise ValueError("Conversation ID must be a string.")

        value = value.strip()

        if not value:
            raise ValueError("Conversation ID cannot be empty.")

        return value
    


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register", response_model=RegisterResponse, status_code=201)
def register_endpoint(request: RegisterRequest):
    try:
        user_id = register_user(
            email=str(request.email),
            password=request.password,
        )
        return RegisterResponse(
            user_id=user_id,
            email=request.email,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Registration could not be completed.",
        ) from None


@app.post("/login", response_model=LoginResponse)
def login_endpoint(request: LoginRequest):
    try:
        token = login_users(
            email=str(request.email),
            password=request.password,
        )
        return LoginResponse(
            access_token=token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error during login.")
        raise HTTPException(
            status_code=500,
            detail="Login could not be completed.",
        ) from None


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    user_id: int = Depends(require_permission("chat:use")),
):
    conversation_id = request.conversation_id
    message = request.message

    if not conversation_id:
        raise HTTPException(
            status_code=422,
            detail="Conversation ID cannot be empty.",
        )

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    try:
        claim_conversation(user_id, conversation_id)
        answer = chat(
            message=message,
            conversation_id=conversation_id,
        )
        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error during chat processing.")
        raise HTTPException(
            status_code=500,
            detail="The agent could not process this request.",
        ) from None
        
@app.post("/files/extract")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(require_permission("chat:use")),
):
    result = await process_uploaded_file(file)

    return {
        "success": True,
        "filename": result["filename"],
        "content_type": result["content_type"],
        "characters": result["characters"],
        "text": result["text"],
    }
    



@app.post("/files/upload", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(require_permission("chat:use")),
):
    try:
        # 1. Extract text
        extracted = await process_uploaded_file(file)

        logger.info(
            "FILE EXTRACTED: filename=%s, characters=%s",
            extracted["filename"],
            len(extracted["text"]),
        )

        # 2. Save file
        saved = save_uploaded_file(user_id, extracted)

        logger.info("FILE SAVED: file_id=%s", saved["id"])

        # 3. Split into chunks
        chunks = split_text_into_chunks(
            extracted["text"],
            chunk_size=1000,
            overlap=150,
        )

        logger.info(
            "CHUNKS CREATED: file_id=%s, total_chunks=%s, chunk_lengths=%s",
            saved["id"],
            len(chunks),
            [len(chunk) for chunk in chunks],
        )

        # 4. Save chunks
        chunk_count = save_document_chunks(
            user_id=user_id,
            file_id=saved["id"],
            chunks=chunks,
        )

        logger.info(
            "CHUNKS SAVED: file_id=%s, saved_count=%s",
            saved["id"],
            chunk_count,
        )

        # 5. Response
        return {
            "success": True,
            "file": saved,
            "total_chunks": len(chunks),
            "saved_chunks": chunk_count,
            "status": "processed",
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while uploading file.")
        raise HTTPException(
            status_code=500,
            detail="Could not upload the file.",
        ) from None

@app.get("/files")
def get_my_files(
    user_id: int = Depends(require_permission("chat:use")),
):
    try:
        return {
            "success": True,
            "files": list_user_files(user_id),
        }
    except Exception:
        logger.exception("Unexpected error while listing user files.")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve uploaded files.",
        ) from None
