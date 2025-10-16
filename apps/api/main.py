from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# Try import; if the SDK isn't present we'll return a helpful error at request time.
try:
    from openai import OpenAI  # new SDK
except Exception:  # SDK not installed or import error
    OpenAI = None

app = FastAPI(title="ProconAI API")
# --- Diagnostics ---
@app.get("/diag")
async def diag():
    import importlib, os, sys
    try:
        sdk_found = importlib.util.find_spec("openai") is not None
    except Exception as e:
        sdk_found = False

    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "openai_sdk_installed": sdk_found,
        "api_key_found": bool(api_key),
        "api_key_preview": (api_key[:8] + "...") if api_key else None,
        "python_version": sys.version,
    }
from fastapi import HTTPException
from pydantic import BaseModel

class AdRequest(BaseModel):
    product: str
    tone: str | None = "friendly"

from fastapi import HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
import traceback, logging

logger = logging.getLogger("uvicorn.error")
client = OpenAI()  # uses env OPENAI_API_KEY / OPENAI_PROJECT

class AdRequest(BaseModel):
    product: str
    tone: str | None = "friendly"

@app.post("/ads/generate")
# put these imports near the top if not present
from fastapi import HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
import traceback, logging

logger = logging.getLogger("uvicorn.error")
client = OpenAI()  # uses env OPENAI_API_KEY / OPENAI_PROJECT

class AdRequest(BaseModel):
    product: str
    tone: str | None = "friendly"

@app.post("/ads/generate", response_model=dict)
async def ads_generate(req: AdRequest):
    """
    JSON body:
    {
      "product": "ProconAI",
      "tone": "confident"
    }
    """
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

# (optional) allow simple GET links too
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

@app.get("/health")
def health():
    return {"status": "ok"}

class AdRequest(BaseModel):
    service: str
    target_city: str
    min_project_budget: int
    tone: str
    variants: int = 3
    hashtags: bool = True
    call_to_action: str = "Contact us today!"

def get_client():
    """Create OpenAI client only when needed; fail gracefully if misconfigured."""
    if OpenAI is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI SDK not installed. Add 'openai>=1.37.0' to requirements.txt and redeploy."
        )
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured in environment variables."
        )
    return OpenAI(api_key=api_key)

@app.post("/ads/generate")
def generate_ads(req: AdRequest):
    client = get_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You write concise, premium ad copy for a high-end remodeler in Bonita Springs, FL. "
                "Each variant should have a short headline and 1–2 sentence body. Keep it classy."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate {req.variants} distinct ad variants for {req.service} in {req.target_city}. "
                f"Tone: {req.tone}. Minimum project budget implied: ${req.min_project_budget}+. "
                f"Call to action: {req.call_to_action}. Include tasteful hashtags: {req.hashtags}. "
                "Return as numbered bullets."
            ),
        },
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=messages,
    )

    text = (resp.choices[0].message.content or "").strip()
    return {"ads": text}
