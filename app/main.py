import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        return json.dumps(log_obj)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Database setup
DATABASE_URL = "postgresql://user:password@db:5432/apex_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSchema(BaseModel):
    name: str
    email: str

    class Config:
        from_attributes = True

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Application shutdown")

# FastAPI app
app = FastAPI(title="Apex Operations API", version="1.0.0", lifespan=lifespan)

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
async def readiness(db: Session = None):
    """Readiness probe"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        logger.info("Readiness check passed")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")

# User endpoints
@app.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserSchema, db: Session = None):
    """Create a new user"""
    db = SessionLocal()
    try:
        db_user = User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created: {user.email}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=400, detail="Email already exists or invalid data")
    finally:
        db.close()

@app.get("/users/{user_id}", response_model=UserSchema)
async def get_user(user_id: int):
    """Get user by ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User retrieved: {user_id}")
        return user
    finally:
        db.close()

@app.get("/users", response_model=list[UserSchema])
async def list_users():
    """List all users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        logger.info(f"Listed {len(users)} users")
        return users
    finally:
        db.close()

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """Delete a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found for deletion: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
        db.commit()
        logger.info(f"User deleted: {user_id}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
