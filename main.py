"""
Gap Field — FastAPI backend.

Receives a prompt from the frontend, forwards it to the Anthropic API using
a server-side API key (never exposed to the browser), and returns the
model's raw text response.
"""

import os
import logging

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gap-field")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Comma-separated list of allowed origins, e.g. "https://gapfield.vercel.app,https://example.com"
# Falls back to "*" for local development only — lock this down in production.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app = FastAPI(title="Gap Field API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)


class AnalyzeResponse(BaseModel):
    text: str


@app.get("/")
async def root():
    return {"status": "Gap Field backend is running"}


@app.get("/health")
async def health():
    return {"ok": True, "api_key_configured": bool(ANTHROPIC_API_KEY)}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not set on the server.",
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 1800,
                    "messages": [{"role": "user", "content": req.prompt}],
                },
            )
    except httpx.RequestError as exc:
        logger.error("Anthropic request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach the analysis service.") from exc

    if response.status_code != 200:
        logger.error("Anthropic API error %s: %s", response.status_code, response.text)
        raise HTTPException(
            status_code=502,
            detail=f"The analysis service rejected the request ({response.status_code}).",
        )

    data = response.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))

    if not text:
        raise HTTPException(status_code=502, detail="The analysis service returned an empty response.")

    return AnalyzeResponse(text=text)
