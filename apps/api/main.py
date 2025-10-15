from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}
from fastapi import FastAPI
from pydantic import BaseModel
import os
import openai

app = FastAPI()

# Health Check
@app.get("/health")
def health():
    return {"status": "ok"}

# Define the Ad Request model
class AdRequest(BaseModel):
    service: str
    target_city: str
    min_project_budget: int
    tone: str
    variants: int = 3
    hashtags: bool = True
    call_to_action: str = "Contact us today!"

# Create the ad generation endpoint
@app.post("/ads/generate")
async def generate_ads(req: AdRequest):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    prompt = f"""
    Generate {req.variants} short, engaging ads for a {req.service} business 
    in {req.target_city} with a minimum project budget of ${req.min_project_budget}.
    Use a {req.tone} tone.
    Include hashtags: {req.hashtags}.
    End each with a call to action: {req.call_to_action}.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    ads = response.choices[0].message["content"].strip()
    return {"ads": ads}
