from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import json

app = FastAPI()

# Change this to "http://host.docker.internal:11434" if running THIS app in Docker too
OLLAMA_URL = "http://localhost:11434/api/chat"

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    model = data.get("model", "llama3") # Change to your model name

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_message}],
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)