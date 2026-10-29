import json
import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os

# Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/apex_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
app = FastAPI(title="Apex Operations API")

# Structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        return json.dumps(log_data)

logger = logging.getLogger("apex")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health endpoints
@app.get("/health", tags=["Health"])
async def health():
    """Liveness probe"""
    logger.info("Health check")
    return {"status": "healthy"}

@app.get("/readiness", tags=["Health"])
async def readiness(db: Session = Depends(get_db)):
    """Readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        logger.info("Readiness check passed")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {"status": "not_ready", "error": str(e)}

# Stub endpoints
@app.post("/users", response_model=User, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create user"""
    logger.info(f"Creating user: {user.email}")
    return {"id": 1, "name": user.name, "email": user.email}

@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user"""
    logger.info(f"Fetching user {user_id}")
    return {"id": user_id, "name": "Test User", "email": "test@example.com"}
