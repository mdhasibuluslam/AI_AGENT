
from langchain_core.messages import HumanMessage, AIMessage

from agent import graph
from memory import get_history, save_message


def extract_text(content) -> str:
    """Convert an LLM response content value to plain text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))

        return "\n".join(part for part in parts if part)

    return str(content)


def chat(message: str, conversation_id: str) -> str:
    """Run the existing agent and persist the conversation."""
    message = message.strip()
    conversation_id = conversation_id.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    if not conversation_id:
        raise ValueError("Conversation ID cannot be empty.")

    history = get_history(conversation_id)

    messages = []

    for item in history:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        elif item["role"] == "assistant":
            messages.append(AIMessage(content=item["content"]))

    messages.append(HumanMessage(content=message))

    result = graph.invoke({
        "messages": messages,
        "conversation_id": conversation_id,
        "user_message": message,
    })

    if not result.get("messages"):
        raise RuntimeError("The agent returned no messages.")

    answer = extract_text(result["messages"][-1].content).strip()

    if not answer:
        raise RuntimeError("The agent returned an empty answer.")

    save_message(conversation_id, "user", message)
    save_message(conversation_id, "assistant", answer)

    return answer