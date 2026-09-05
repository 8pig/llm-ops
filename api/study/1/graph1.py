import os
from typing import TypedDict, Annotated, Any

import dotenv
from langchain_classic.agents.chat.prompt import HUMAN_MESSAGE
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessageGraph, START, END
from langgraph.graph.message import add_messages

dotenv.load_dotenv()

llm = ChatOpenAI(
    model="qwen3-max-2026-01-23",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)





class State(TypedDict):
    """图结构状态"""
    messages: Annotated[list, add_messages]
    use_name: str


def chatbot(state: State)->Any:

    ai_message = llm.invoke(state["messages"])
    return {"messages": [ai_message], "use_name": "chatbot"}


graph_builder = StateGraph(State)

graph_builder.add_node("llm", chatbot)

graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)

# graph_builder.set_entry_point("llm")
# graph_builder.set_finish_point("llm")


graph = graph_builder.compile()

print(graph.invoke({"messages": [("human", "你好, 你是谁")], "use_name": "graph"}))









