
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)
from database import init_db

from agent import graph

from memory import (
    get_history,
    save_message,
)


CONVERSATION_ID = "conversation_001"
init_db()


# --------------------------------------------
# 6. Make sure response is text
# --------------------------------------------
def extract_text(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)

            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))

        return "\n".join(
            part for part in parts if part
        )

    return str(content)

def run_agent(user_message: str):

    # --------------------------------------------
    # 1. Get previous conversation
    # --------------------------------------------

    history = get_history(
        CONVERSATION_ID
    )


    # --------------------------------------------
    # 2. Convert memory → LangChain messages
    # --------------------------------------------

    messages = []


    for item in history:

        if item["role"] == "user":

            messages.append(
                HumanMessage(
                    content=item["content"]
                )
            )

        elif item["role"] == "assistant":

            messages.append(
                AIMessage(
                    content=item["content"]
                )
            )


    # --------------------------------------------
    # 3. Add current user message
    # --------------------------------------------

    messages.append(
        HumanMessage(
            content=user_message
        )
    )


    # --------------------------------------------
    # 4. Run LangGraph
    # --------------------------------------------

    result = graph.invoke(
        {
            "messages": messages,
            "conversation_id": CONVERSATION_ID,
            "user_message": user_message,
        }
    )


    # --------------------------------------------
    # 5. Get final AI response
    # --------------------------------------------

    final_msg  = result["messages"][-1]
    response = extract_text(final_msg.content)




    # --------------------------------------------
    # 7. Save conversation
    # --------------------------------------------

    save_message(
        CONVERSATION_ID,
        "user",
        user_message,
    )


    save_message(
        CONVERSATION_ID,
        "assistant",
        response,
    )


    return response


# ==================================================
# CLI
# ==================================================

print()
print("AI Business Support Agent")
print("Type 'exit' to quit.")
print()


while True:

    user_message = input(
        "You: "
    ).strip()


    if user_message.lower() == "exit":

        break


    if not user_message:

        continue


    try:

        response = run_agent(
            user_message
        )

        print()
        print(
            "AI:",
            response
        )
        print()


    except Exception as error:

        print()
        print(
            "Error:",
            error
        )
        print()
