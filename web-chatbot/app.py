import os
import argparse
import sqlite3
import json
import base64
import io
from typing import Annotated, TypedDict, List, Union, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from pypdf import PdfReader  # <--- Added for PDF processing

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
    image_data: str

llm = ChatOpenAI(
    base_url="http://localhost:12434/v1",
    api_key="sk-no-key-required",
    model=args.model
)

def chatbot_node(state: AgentState):
    summary = state.get("summary", "")
    messages = state["messages"]
    image_data = state.get("image_data")

    if image_data:
        last_msg = messages[-1]
        multimodal_content = [
            {"type": "text", "text": last_msg.content},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
        messages = messages[:-1] + [HumanMessage(content=multimodal_content, id=last_msg.id)]

    if summary:
        system_msg = SystemMessage(content=f"Summary of previous conversation: {summary}")
        messages = [system_msg] + messages

    response = llm.invoke(messages)
    return {"messages": [response], "image_data": ""}

def summarizer_node(state: AgentState):
    clean_messages = [msg for msg in state["messages"] if msg.id != "ephemeral_image"]

    if len(clean_messages) <= 15:
        return {}

    existing_summary = state.get("summary", "")
    prompt = (
        f"Current summary: {existing_summary}\n\nExtend the summary with the new info:"
        if existing_summary else "Summarize this chat:"
    )

    messages = clean_messages + [SystemMessage(content=prompt)]
    print("Sending clean messages to summarizer (No Base64!):", len(messages))

    try:
        response = llm.invoke(messages)
        delete_msgs = [RemoveMessage(id=m.id) for m in clean_messages[:-3]]
        return {"summary": response.content, "messages": delete_msgs}
    except Exception as e:
        print(f"[Warning] Summarizer failed safely: {e}.")
        return {}

# --- 3. Build & Compile the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("chatbot", chatbot_node)
workflow.add_node("summarize", summarizer_node)

workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", "summarize")
workflow.add_edge("summarize", END)

DB_PATH = "memory.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")

memory = SqliteSaver(conn)
agent = workflow.compile(checkpointer=memory)

# --- Helper to parse PDF ---
def extract_text_from_b64_pdf(b64_string: str) -> str:
    try:
        pdf_bytes = base64.b64decode(b64_string)
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        text_content = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content.append(f"--- Page {i+1} ---\n{text}")

        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return "[Error: Could not extract text from this PDF file]"

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
        user_text = data.get("message", "").strip()
        media_data = data.get("media")

        if not user_text and not media_data:
            raise HTTPException(status_code=400, detail="Empty request payload.")

        payload_messages = []
        base64_image_string = None

        # Process attached media
        if media_data:
            media_type = media_data.get("type")
            media_b64 = media_data.get("data")

            if media_type == "image":
                base64_image_string = media_b64
            elif media_type == "pdf":
                pdf_text = extract_text_from_b64_pdf(media_b64)
                # Inject extracted text into the user's message context clearly
                user_text = f"{user_text}\n\n[Attached Document Contents]\n{pdf_text}".strip()

        if user_text:
            payload_messages.append(HumanMessage(content=user_text))

        config = {"configurable": {"thread_id": "default_user"}}

        try:
            result = agent.invoke(
                {
                    "messages": payload_messages,
                    "image_data": base64_image_string
                },
                config=config
            )
            final_msg = result["messages"][-1]
        except Exception as graph_err:
            print(f"Database/Graph state aborted safely: {graph_err}")
            raise HTTPException(status_code=500, detail="Failed to process conversation state.")

        return {
            "message": {
                "role": "assistant",
                "content": final_msg.content
            }
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Critical System Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)