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

# ---- Diagnostics ----
@app.get("/diag")
async def diag():
    try:
        sdk_found = importlib.util.find_spec("openai") is not None
    except Exception:
        sdk_found = False
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "openai_sdk_installed": sdk_found,
        "api_key_found": bool(api_key),
        "api_key_preview": (api_key[:8] + "...") if api_key else None,
        "python_version": sys.version,
    }

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

# ---- Optional GET wrapper for convenience ----
@app.get("/ads/generate", response_model=dict)
async def ads_generate_get(product: str, tone: str = "friendly"):
    try:
        prompt = f"Write a {tone or 'friendly'} 50-word ad for {product}."
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
