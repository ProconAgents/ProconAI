 from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from openai import OpenAI

app = FastAPI(title="ProconAI API")

# ----- Health -----
@app.get("/health")
def health():
    return {"status": "ok"}

# ----- Schema -----
class AdRequest(BaseModel):
    service: str
    target_city: str
    min_project_budget: int
    tone: str
    variants: int = 3
    hashtags: bool = True
    call_to_action: str = "Contact us today!"

# ----- OpenAI client -----
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----- Ad generator -----
@app.post("/ads/generate")
def generate_ads(req: AdRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    system = (
        "You write concise, premium ad copy for a high-end remodeler in Bonita Springs, FL."
        " Each variant should have a short headline and 1–2 sentence body. Keep it classy."
    )

    user = (
        f"Generate {req.variants} distinct ad variants for {req.service} in {req.target_city}. "
        f"Tone: {req.tone}. Minimum project budget implied: ${req.min_project_budget}+."
        f" Call to action: {req.call_to_action}. "
        f"Include tasteful hashtags: {req.hashtags}. Return as numbered bullets."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    text = (completion.choices[0].message.content or "").strip()
    return {"ads": text}
    
