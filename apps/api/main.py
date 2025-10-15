from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# Try import; if the SDK isn't present we'll return a helpful error at request time.
try:
    from openai import OpenAI  # new SDK
except Exception:  # SDK not installed or import error
    OpenAI = None

app = FastAPI(title="ProconAI API")

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
