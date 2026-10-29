
import pytest
from pydantic import ValidationError

from api import ChatRequest


def test_valid_request():
    request = ChatRequest(
        message="  Find a product  ",
        conversation_id="  test-conversation-1  ",
    )
    assert request.message == "Find a product"
    assert request.conversation_id == "test-conversation-1"


@pytest.mark.parametrize("message", ["", " ", "   ", "\t\n"])
def test_rejects_empty_message(message):
    with pytest.raises(ValidationError):
        ChatRequest(
            message=message,
            conversation_id="test-conversation-1",
        )


def test_rejects_oversized_message():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="x" * 5001,
            conversation_id="test-conversation-1",
        )


def test_rejects_empty_conversation_id():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="Hello",
            conversation_id="   ",
        )


def test_rejects_oversized_conversation_id():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="Hello",
            conversation_id="x" * 101,
        )
