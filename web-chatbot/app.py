import os
import argparse
import sqlite3
from typing import Annotated, TypedDict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

# LangChain / LangGraph Imports
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

# --- 1. Setup Arguments & Model ---
parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="gemma4", help="Model deployed in ollama.")
args = parser.parse_args()

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. Define Agent State & Logic ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str

llm = ChatOllama(model=args.model, temperature=0.7)

def chatbot_node(state: AgentState):
    summary = state.get("summary", "")
    messages = state["messages"]

    if summary:
        # Inject summary as context for the model
        system_msg = SystemMessage(content=f"Summary of previous conversation: {summary}")
        messages = [system_msg] + messages

    response = llm.invoke(messages)
    return {"messages": [response]}

def summarizer_node(state: AgentState):
    # Summarize if context gets long (e.g., > 15 messages)
    if len(state["messages"]) <= 15:
        return {}

    existing_summary = state.get("summary", "")
    prompt = f"Current summary: {existing_summary}\n\nExtend the summary with the new info:" if existing_summary else "Summarize this chat:"

    messages = state["messages"] + [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    # Keep the last 3 messages for immediate continuity, delete the rest
    delete_msgs = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]

    return {"summary": response.content, "messages": delete_msgs}

# --- 3. Build & Compile the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("chatbot", chatbot_node)
workflow.add_node("summarize", summarizer_node)

workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", "summarize")
workflow.add_edge("summarize", END)

# Persistent SQLite memory
conn = sqlite3.connect("memory.db", check_same_thread=False)
memory = SqliteSaver(conn)
agent = workflow.compile(checkpointer=memory)

# --- 4. API Routes ---

@app.get("/", response_class=HTMLResponse)
async def index():
    file_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<h1>index.html not found!</h1>", status_code=404)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")

        # In a real app, 'thread_id' would come from a cookie or user login
        # Here we use a hardcoded 'default_user' to keep memory across refreshes
        config = {"configurable": {"thread_id": "default_user"}}

        # Run the agent
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config
        )

        # Get the last message from the result
        final_msg = result["messages"][-1]

        return {
            "message": {
                "role": "assistant",
                "content": final_msg.content
            }
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)