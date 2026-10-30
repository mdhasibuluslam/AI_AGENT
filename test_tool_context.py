from unittest.mock import patch

import pytest
from langchain.tools import tool
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode

from tool_permissions import (
    set_tool_user,
    reset_tool_user,
    check_tool_permission,
    require_tool_permission,
)
from langgraph.graph import StateGraph, START, END, MessagesState

def test_missing_user_context_denied():
    with pytest.raises(PermissionError):
        check_tool_permission("chat:use")


def test_authorized_user_allowed():
    with patch("authorization.has_permission", return_value=True):
        token = set_tool_user(1)

        try:
            check_tool_permission("chat:use")
        finally:
            reset_tool_user(token)


def test_unauthorized_user_denied():
    with patch("authorization.has_permission", return_value=False):
        token = set_tool_user(1)

        try:
            with pytest.raises(PermissionError):
                check_tool_permission("chat:use")
        finally:
            reset_tool_user(token)


def test_denied_tool_does_not_execute_business_logic():
    executed = []

    @require_tool_permission("support:manage")
    def protected_tool():
        executed.append(True)
        return {"success": True}

    with patch("authorization.has_permission", return_value=False):
        token = set_tool_user(1)

        try:
            result = protected_tool()
        finally:
            reset_tool_user(token)

    assert result["success"] is False
    assert executed == []


def test_context_is_reset_after_execution():
    token = set_tool_user(123)

    assert token is not None

    reset_tool_user(token)

    with pytest.raises(PermissionError):
        check_tool_permission("chat:use")


def test_langgraph_toolnode_receives_user_context():

    @tool
    @require_tool_permission("chat:use")
    def protected_probe() -> dict:
        """Test whether LangGraph receives authenticated user context."""
        return {
            "success": True,
            "user_context_received": True,
        }

    # Create a small LangGraph workflow.
    builder = StateGraph(MessagesState)

    builder.add_node("tools", ToolNode([protected_probe]))

    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)

    test_graph = builder.compile()

    with patch("authorization.has_permission", return_value=True):
        token = set_tool_user(1)

        try:
            result = test_graph.invoke({
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "protected_probe",
                                "args": {},
                                "id": "test-call-1",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            })

        finally:
            reset_tool_user(token)

    import json

    tool_message = result["messages"][-1]

    payload = json.loads(tool_message.content)

    assert payload["success"] is True
    assert payload["user_context_received"] is True