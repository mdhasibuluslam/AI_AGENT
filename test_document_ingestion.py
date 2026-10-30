
import pytest

from document_ingestion import split_text_into_chunks


def test_empty_document_is_rejected():
    with pytest.raises(ValueError):
        split_text_into_chunks("   ")


def test_chunks_respect_maximum_size():
    text = "A" * 2500

    chunks = split_text_into_chunks(
        text,
        chunk_size=1000,
        overlap=150,
    )

    assert len(chunks) == 3
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_chunks_preserve_overlap():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    chunks = split_text_into_chunks(
        text,
        chunk_size=10,
        overlap=3,
    )

    assert chunks[0][-3:] == chunks[1][:3]
    assert chunks[1][-3:] == chunks[2][:3]


def test_document_is_reconstructed_without_overlap():
    text = "A" * 2500
    chunks = split_text_into_chunks(text, 1000, 150)

    reconstructed = chunks[0] + "".join(
        chunk[150:] for chunk in chunks[1:]
    )

    assert reconstructed == text


def test_invalid_overlap_is_rejected():
    with pytest.raises(ValueError):
        split_text_into_chunks("Some text", chunk_size=10, overlap=10)


def test_non_string_input_is_rejected():
    with pytest.raises(ValueError):
        split_text_into_chunks(None)


def test_oversized_document_is_rejected():
    text = "A" * 200_001

    with pytest.raises(ValueError):
        split_text_into_chunks(text)
