from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader


MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


async def extract_uploaded_text(file: UploadFile) -> dict:
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are allowed.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 2 MB limit.",
        )

    if extension == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="TXT file must use UTF-8 encoding.",
            ) from None

    else:
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="File does not appear to be a valid PDF.",
            )

        try:
            reader = PdfReader(BytesIO(content), strict=True)

            if reader.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted PDFs are not supported.",
                )

            if len(reader.pages) > 100:
                raise HTTPException(
                    status_code=400,
                    detail="PDF cannot contain more than 100 pages.",
                )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not read this PDF file.",
            ) from None

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in the file.",
        )

    if len(text) > 200_000:
        raise HTTPException(
            status_code=400,
            detail="Extracted text exceeds the allowed limit.",
        )

    return {
        "filename": filename,
        "content_type": extension,
        "text": text,
        "characters": len(text),
    }