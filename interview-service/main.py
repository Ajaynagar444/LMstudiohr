import os
import asyncio
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker

from openai import OpenAI

# ================= LOAD ENV =================
load_dotenv()

app = FastAPI(title="AI Interview Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= LM STUDIO =================
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-7b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")

client = OpenAI(
    base_url=BASE_URL,
    api_key="lm-studio"
)

def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=150
    )
    return response.choices[0].message.content


# ================= DATABASE =================
user = os.getenv("POSTGRES_USER", "postgres")
password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
db_name = os.getenv("POSTGRES_DB", "resume_db")  #  SAME DB as resume-service

DATABASE_URL = f"postgresql://{user}:{password}@localhost:5432/{db_name}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ================= TABLES =================
class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    resume_id = Column(Integer)
    resume_summary = Column(Text)
    experience_years = Column(Integer)


Base.metadata.create_all(bind=engine)


# ================= REQUEST MODELS =================
class StartSessionRequest(BaseModel):
    user_id: int
    resume_id: int


class NextQuestionRequest(BaseModel):
    session_id: int
    user_reply: str


# ================= PROMPT =================
def build_prompt(history, resume_summary, user_input, exp):
    return f"""
You are a strict technical interviewer.

RULES:
- Ask ONLY ONE question
- Max 15 words
- Based on resume
- No explanation

Experience: {exp} years

Resume Summary:
{resume_summary}

Conversation:
{history}

Last Answer:
{user_input}

QUESTION:
"""


# ================= START SESSION =================
@app.post("/session/start")
async def start_session(req: StartSessionRequest):
    db = SessionLocal()

    # Fetch resume from DB
    result = db.execute(text("""
        SELECT summary, experience_years
        FROM resumes
        WHERE id = :id
    """), {"id": req.resume_id}).fetchone()

    if not result:
        db.close()
        return {"error": "Resume not found"}

    session = InterviewSession(
        user_id=req.user_id,
        resume_id=req.resume_id,
        resume_summary=result[0],
        experience_years=result[1]
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()

    return {
        "session_id": session.id,
        "question": "Tell me about yourself?"
    }


# ================= NEXT QUESTION (API) =================
@app.post("/session/next")
async def next_question(req: NextQuestionRequest):
    db = SessionLocal()

    # Save USER
    db.add(InterviewMessage(
        session_id=req.session_id,
        role="USER",
        content=req.user_reply
    ))
    db.commit()

    # Get history
    messages = db.query(InterviewMessage).filter(
        InterviewMessage.session_id == req.session_id
    ).all()

    history = "\n".join([f"{m.role}: {m.content}" for m in messages])

    # Get session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == req.session_id
    ).first()

    if not session:
        db.close()
        return {"error": "Session not found"}

    # Generate question
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        call_llm,
        build_prompt(history, session.resume_summary, req.user_reply, session.experience_years)
    )

    # Save AI
    db.add(InterviewMessage(
        session_id=req.session_id,
        role="AI",
        content=response
    ))
    db.commit()
    db.close()

    return {"ai_question": response}


# ================= WEBSOCKET =================
@app.websocket("/ws/interview/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: int):
    await websocket.accept()

    db = SessionLocal()

    try:
        while True:
            user_text = await websocket.receive_text()

            # Save USER
            db.add(InterviewMessage(
                session_id=session_id,
                role="USER",
                content=user_text
            ))
            db.commit()

            # Get history
            messages = db.query(InterviewMessage).filter(
                InterviewMessage.session_id == session_id
            ).order_by(InterviewMessage.id).all()

            history = "\n".join([f"{m.role}: {m.content}" for m in messages])

            # Get session
            session = db.query(InterviewSession).filter(
                InterviewSession.id == session_id
            ).first()

            if not session:
                await websocket.send_text("Session error")
                continue

            # Generate AI response
            loop = asyncio.get_event_loop()
            ai_response = await loop.run_in_executor(
                None,
                call_llm,
                build_prompt(history, session.resume_summary, user_text, session.experience_years)
            )

            # Save AI
            db.add(InterviewMessage(
                session_id=session_id,
                role="AI",
                content=ai_response
            ))
            db.commit()

            # Send response
            await websocket.send_text(ai_response)

    except WebSocketDisconnect:
        db.close()


# ================= HEALTH =================
@app.get("/")
def home():
    return {"status": "Interview service running"}