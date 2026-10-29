
from unittest.mock import patch

import pytest

from rag import retrieve_knowledge


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        None,
        123,
        "a" * 1001,
    ],
)
def test_invalid_query_is_rejected_before_embedding(query):
    with patch("rag.create_embedding") as mock_embedding:
        with pytest.raises(ValueError):
            retrieve_knowledge(query)

    mock_embedding.assert_not_called()


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        11,
        True,
        False,
        1.5,
        "4",
        None,
    ],
)
def test_invalid_limit_is_rejected_before_embedding(limit):
    with patch("rag.create_embedding") as mock_embedding:
        with pytest.raises(ValueError):
            retrieve_knowledge("return policy", limit=limit)

    mock_embedding.assert_not_called()


def test_database_error_does_not_leak_details():
    secret_detail = "internal_database_password_details"

    with (
        patch("rag.create_embedding", return_value=[0.0] * 384),
        patch(
            "rag.get_connection",
            side_effect=RuntimeError(secret_detail),
        ),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            retrieve_knowledge("return policy")

    assert str(exc_info.value) == (
        "Knowledge retrieval is temporarily unavailable."
    )
    assert secret_detail not in str(exc_info.value)


def test_valid_query_is_trimmed_before_embedding():
    with (
        patch("rag.create_embedding", return_value=[0.0] * 384) as mock_embedding,
        patch("rag.get_connection") as mock_connection,
    ):
        mock_connection.side_effect = RuntimeError("test failure")

        with pytest.raises(RuntimeError):
            retrieve_knowledge("  return policy  ")

    mock_embedding.assert_called_once_with("return policy")
