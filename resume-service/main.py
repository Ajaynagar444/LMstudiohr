import os
import json
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from openai import OpenAI
from langchain_community.document_loaders import PyMuPDFLoader

load_dotenv()

app = FastAPI(title="Resume Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.getenv("MODEL_NAME", "mistral-7b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")

client = OpenAI(
    base_url=BASE_URL,
    api_key="lm-studio"
)

def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=300
    )
    return response.choices[0].message.content


# ================= DATABASE =================
user = os.getenv("POSTGRES_USER", "postgres")
password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
db_name = os.getenv("POSTGRES_DB", "resume_db")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= TABLE =================
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    filename = Column(String)
    raw_text = Column(Text)
    summary = Column(Text)
    skills = Column(JSON)
    experience_years = Column(Integer)

Base.metadata.create_all(bind=engine)

# ================= HEALTH =================
@app.get("/")
def home():
    return {"message": "Resume Service Running"}

# ================= ANALYZE RESUME =================
@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...), user_id: int = Form(...)):
    content = await file.read()

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        temp_path = tmp_file.name
        tmp_file.write(content)

    try:
        # Extract PDF text
        loader = PyMuPDFLoader(temp_path)
        docs = loader.load()

        text = ""
        for doc in docs:
            text += doc.page_content + "\n"

        text = text[:1000]  # limit for performance

        # ================= PROMPT =================
        prompt = f"""
You are a strict AI resume analyzer.

RULES:
- Return ONLY valid JSON
- No explanation
- No markdown

Format:
{{
"summary":"...",
"skills":[],
"experience_years":0
}}

Resume:
{text}
"""
        # ================= CALL LLM =================
        try:
            result = call_llm(prompt)
        except Exception as e:
            return {"error": f"LLM error: {str(e)}"}

        # ================= CLEAN RESPONSE =================
        cleaned = result.strip().replace("```json", "").replace("```", "")

        # ================= SAFE PARSE =================
        try:
            data = json.loads(cleaned)
        except:
            data = {
                "summary": cleaned[:200],
                "skills": [],
                "experience_years": 0
            }

        # ================= SAVE TO DB =================
        db = SessionLocal()

        resume = Resume(
            user_id=user_id,
            filename=file.filename,
            raw_text=text,
            summary=data.get("summary", ""),
            skills=data.get("skills", []),
            experience_years=data.get("experience_years", 0)
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)
        db.close()

        return {
            "resume_id": resume.id,
            "analysis": data
        }

    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


print("Resume Service Loaded Successfully")