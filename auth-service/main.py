import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Load env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# App
app = FastAPI(title="Auth Service")

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB config
user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
db = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{user}:{password}@localhost:5432/{db}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"

# Helper function to handle passwords > 72 bytes
def prepare_password(password: str) -> str:
    """Pre-hash passwords longer than 72 bytes using SHA256"""
    if len(password.encode("utf-8")) > 72:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    return password

# Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Schemas
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/")
def root():
    return {"message": "Auth Service Running "}

@app.post("/register")
def register(req: RegisterRequest, db=Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Pre-hash long passwords to work around bcrypt 72-byte limit
    prepared_password = prepare_password(req.password)
    hashed_password = pwd_context.hash(prepared_password)

    user = User(
        email=req.email,
        password_hash=hashed_password,
        name=req.name
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered", "user_id": user.id}

@app.post("/login")
def login(req: LoginRequest, db=Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    prepared_password = prepare_password(req.password)
    if not user or not pwd_context.verify(prepared_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=1)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": token, "user_id": user.id}

print("Auth Service Loaded Successfully")