from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# Allows your frontend (hosted anywhere) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

class AnalyzeRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "Gap Field backend is running"}

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5",
                "max_tokens": 1800,
                "messages": [{"role": "user", "content": req.prompt}],
            },
            timeout=60.0,
        )
    data = response.json()

    if "error" in data:
        return {"error": data["error"]}

    content = data.get("content", [])
    text = "".join(block.get("text", "") for block in content)
    return {"text": text}
