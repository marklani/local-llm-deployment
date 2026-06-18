import os
import argparse
import sqlite3
import json # Ensure json is imported
from typing import Annotated, TypedDict, List, Union, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

# LangChain / LangGraph Imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

# --- 1. Setup Arguments & Model ---
parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="gemma4:e4b", help="Model deployed in docker model runner.")
args = parser.parse_args()

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 2. Define Agent State & Logic ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str

# Note: For multimodal to work, the llama.cpp server must be running a
# Vision-capable model (like LLaVA or a Vision-variant of Gemma).
llm = ChatOpenAI(
    base_url="http://localhost:12434/v1",
    api_key="sk-no-key-required",
    model=args.model
)

def chatbot_node(state: AgentState):
    summary = state.get("summary", "")
    # In a multimodal setup, 'messages' contains the history
    messages = state["messages"]

    if summary:
        system_msg = SystemMessage(content=f"Summary of previous conversation: {summary}")
        messages = [system_msg] + messages

    # The LLM.invoke handles the list of content blocks automatically
    response = llm.invoke(messages)
    return {"messages": [response]}

def summarizer_node(state: AgentState):
    if len(state["messages"]) <= 15:
        return {}

    existing_summary = state.get("summary", "")
    prompt = f"Current summary: {existing_summary}\n\nExtend the summary with the new info:" if existing_summary else "Summarize this chat:"

    messages = state["messages"] + [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    delete_msgs = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]
    return {"summary": response.content, "messages": delete_msgs}

# --- 3. Build & Compile the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("chatbot", chatbot_node)
workflow.add_node("summarize", summarizer_node)

workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", "summarize")
workflow.add_edge("summarize", END)

DB_PATH = "memory.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
        user_text = data.get("message", "")
        media_data = data.get("media") # This will be a dict or None

        # --- MULTIMODAL MESSAGE CONSTRUCTION ---
        content = []

        # 1. Add the media if it exists
        if media_data and media_data.get("type") == "image":
            base64_string = media_data.get("data")
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_string}"
                }
            })

        # 2. Add the text
        content.append({
            "type": "text",
            "text": user_text
        })

        config = {"configurable": {"thread_id": "default_user"}}

        # Pass the list of content blocks to the HumanMessage
        result = agent.invoke(
            {"messages": [HumanMessage(content=content)]},
            config=config
        )

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
