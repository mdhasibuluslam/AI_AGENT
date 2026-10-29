
import pytest
from fastapi import HTTPException, UploadFile
from io import BytesIO

from file_upload import extract_uploaded_text


def make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
    )


@pytest.mark.asyncio
async def test_extract_txt():
    file = make_upload(
        "policy.txt",
        b"Customers can return eligible products within 30 days.",
    )

    result = await extract_uploaded_text(file)

    assert result["filename"] == "policy.txt"
    assert "30 days" in result["text"]


@pytest.mark.asyncio
async def test_reject_unsupported_extension():
    file = make_upload("script.exe", b"test")

    with pytest.raises(HTTPException) as exc:
        await extract_uploaded_text(file)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_reject_empty_file():
    file = make_upload("empty.txt", b"")

    with pytest.raises(HTTPException) as exc:
        await extract_uploaded_text(file)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_reject_oversized_file():
    file = make_upload(
        "large.txt",
        b"a" * (2 * 1024 * 1024 + 1),
    )

    with pytest.raises(HTTPException) as exc:
        await extract_uploaded_text(file)

    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_reject_invalid_pdf():
    file = make_upload("fake.pdf", b"This is not a PDF.")

    with pytest.raises(HTTPException) as exc:
        await extract_uploaded_text(file)

    assert exc.value.status_code == 400
