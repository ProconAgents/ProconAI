from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

# --- Setup ---
app = FastAPI(title="ProconAI API")

# Allow cross-origin requests (safe default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logger = logging.getLogger("uvicorn.access")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Data Model ---
class AdRequest(BaseModel):
    product: str
    tone: str = "friendly"

# --- Routes ---

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/ads/generate")
async def ads_generate(req: AdRequest):
    """
    Generate ad copy using OpenAI.
    Example body:
    {
      "product": "ProconAI",
      "tone": "confident"
    }
    """
    logger.info(f"Generating ad for product={req.product}, tone={req.tone}")
    
    prompt = (
        f"Write a {req.tone} advertisement for a product called '{req.product}'. "
        "Keep it engaging and under 3 sentences."
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        ad_text = resp.choices[0].message.content.strip()
        return {"ok": True, "text": ad_text}
    except Exception as e:
        logger.error(f"Error generating ad: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/ads/generate")
async def ads_generate_get(product: str, tone: str = "friendly"):
    """
    Alternate GET version for quick browser testing.
    Example:
      /ads/generate?product=ProconAI&tone=confident
    """
    prompt = (
        f"Write a {tone} advertisement for a product called '{product}'. "
        "Keep it engaging and under 3 sentences."
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        ad_text = resp.choices[0].message.content.strip()
        return {"ok": True, "text": ad_text}
    except Exception as e:
        return {"ok": False, "error": str(e)}
