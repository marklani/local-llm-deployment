import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, help="Model deployed in docker.")
args = parser.parse_args()

app = FastAPI()

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLLAMA_URL = "http://localhost:11434/api/chat"

@app.get("/", response_class=HTMLResponse)
async def index():
    file_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<h1>index.html not found!</h1><p>Make sure it is in the same folder as app.py</p>", status_code=404)

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        print(user_message)
        payload = {
            "model": f"{args.model}", # Change this to the model you have (e.g., mistral, phi3)
            "messages": [{"role": "user", "content": user_message}],
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=900)
        # Add timeout error too
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 makes it accessible on your local network/mobile
    uvicorn.run(app, host="0.0.0.0", port=8000)