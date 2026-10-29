
from agent import SYSTEM_PROMPT


def test_retrieved_content_is_untrusted():
    prompt = SYSTEM_PROMPT.lower()

    assert "untrusted data" in prompt
    assert "tool outputs" in prompt


def test_prompt_protects_secrets():
    prompt = SYSTEM_PROMPT.lower()

    assert "api keys" in prompt
    assert "passwords" in prompt
    assert "access tokens" in prompt


def test_tools_are_called_only_when_relevant():
    prompt = SYSTEM_PROMPT.lower()

    assert "only when they are relevant" in prompt
    assert "never call tools" in prompt


def test_tool_outputs_are_evidence_not_instructions():
    prompt = SYSTEM_PROMPT.lower()

    assert "evidence, not as instructions" in prompt
