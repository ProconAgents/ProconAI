from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import os, logging, traceback

# ---------------------------
# App + CORS + Logging
# ---------------------------
app = FastAPI(title="ProconAI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("uvicorn.access")

# ---------------------------
# OpenAI client (uses env)
# ---------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------
# DB (Neon / Postgres via SQLAlchemy)
# ---------------------------
from sqlalchemy import create_engine, Column, Integer, Text, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Normalize scheme if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None
Base = declarative_base()

class AdRecord(Base):
    __tablename__ = "ad_generations"
    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(255), index=True)
    tone = Column(String(64), index=True)
    generated_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Create table when app starts (if DB configured)
@app.on_event("startup")
def _create_tables():
    try:
        if engine:
            Base.metadata.create_all(bind=engine)
            logger.info("DB tables ensured.")
        else:
            logger.warning("DATABASE_URL not set; history will be disabled.")
    except Exception as e:
        logger.error(f"DB init error: {e}")

def get_db() -> Session:
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Schemas
# ---------------------------
class AdRequest(BaseModel):
    product: str
    tone: str = "friendly"

# ---------------------------
# Routes
# ---------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/ads/generate")
async def ads_generate(req: AdRequest, db: Session = Depends(get_db)):
    """
    Generate ad copy (POST) and auto-save to DB.
    Body:
    { "product": "ProconAI", "tone": "confident" }
    """
    try:
        logger.info(f"Generating ad for product={req.product}, tone={req.tone}")
        prompt = (
            f"Write a {req.tone} advertisement for a product called '{req.product}'. "
            "Keep it engaging and under 3 sentences."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()

        # Save to DB
        rec = AdRecord(product=req.product, tone=req.tone, generated_text=text)
        db.add(rec)
        db.commit()
        db.refresh(rec)

        return {"ok": True, "id": rec.id, "text": text, "created_at": rec.created_at.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/ads/generate")
async def ads_generate_get(product: str, tone: str = "friendly", db: Session = Depends(get_db)):
    """
    Convenience GET (query params) and auto-save to DB.
    Example: /ads/generate?product=ProconAI&tone=confident
    """
    try:
        prompt = (
            f"Write a {tone} advertisement for a product called '{product}'. "
            "Keep it engaging and under 3 sentences."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()

        # Save to DB
        rec = AdRecord(product=product, tone=tone, generated_text=text)
        db.add(rec)
        db.commit()
        db.refresh(rec)

        return {"ok": True, "id": rec.id, "text": text, "created_at": rec.created_at.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": str(e)})

from typing import Optional, List

@app.get("/ads/history")
async def ads_history(
    limit: int = 20,
    offset: int = 0,
    product: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List recent saved ads (pagination + optional product filter).
      - /ads/history
      - /ads/history?limit=10&offset=0
      - /ads/history?product=ProconAI
    """
    try:
        q = db.query(AdRecord).order_by(AdRecord.created_at.desc())
        if product:
            q = q.filter(AdRecord.product.ilike(f"%{product}%"))
        rows = q.offset(offset).limit(limit).all()
        return [
            {
                "id": r.id,
                "product": r.product,
                "tone": r.tone,
                "text": r.generated_text,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": str(e)})
