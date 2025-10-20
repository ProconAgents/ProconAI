# apps/api/main.py

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import logging, traceback, importlib, os, sys

app = FastAPI(title="ProconAI API")

# ---- OpenAI client (uses env: OPENAI_API_KEY + OPENAI_PROJECT) ----
client = OpenAI()
logger = logging.getLogger("uvicorn.error")

# ---- Health ----
@app.get("/health")
async def health():
    return {"status": "ok"}
# ---- Ad generation (POST expects JSON) ----
class AdRequest(BaseModel):
    product: str
    tone: str | None = "friendly"

@app.post("/ads/generate", response_model=dict)
async def ads_generate(req: AdRequest):
    try:
        prompt = f"Write a {req.tone or 'friendly'} 50-word ad for {req.product}."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise creative ad generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=180,
        )
        text = resp.choices[0].message.content
        return {"ok": True, "text": text}
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": str(e)})


   
