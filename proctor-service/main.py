import os
import cv2
import uuid
import numpy as np
import mediapipe as mp
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import quote_plus

load_dotenv()

SAVE_DIR = os.getenv("SAVE_DIR", "violations")
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")

os.makedirs(SAVE_DIR, exist_ok=True)

user = os.getenv("POSTGRES_USER", "postgres")
password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
db_name = os.getenv("POSTGRES_DB", "violation_db")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ProctorViolation(Base):
    __tablename__ = "proctor_violations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)

    reason = Column(String)
    image_path = Column(String)
    confidence = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)


class TabSwitchEvent(Base):
    __tablename__ = "tab_switch_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer)
    user_id = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)


class AudioAlert(Base):
    __tablename__ = "audio_alerts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer)
    user_id = Column(Integer)

    reason = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# CONSTANTS 
PHONE_CLASS_ID = 67

RESTRICTED_OBJECTS = {
    PHONE_CLASS_ID: "Mobile Phone"
}

# FASTAPI APP
app = FastAPI(title="AI Proctor Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading YOLO Model")
yolo_model = YOLO(YOLO_MODEL)

print("Loading Face Detection")
face_detector = mp.solutions.face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5
)

print("Loading Face Mesh")
face_mesh = mp.solutions.face_mesh.FaceMesh(
    refine_landmarks=True
)

print("Proctor Service Loaded Successfully")
def save_violation_image(frame, reason):
    filename = f"{reason}_{uuid.uuid4().hex[:8]}.jpg"
    path = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(path, frame)
    return path


def save_violation_db(session_id, user_id, reason, image_path, confidence=0):
    db = SessionLocal()
    try:
        row = ProctorViolation(
            session_id=session_id,
            user_id=user_id,
            reason=reason,
            image_path=image_path,
            confidence=confidence
        )
        db.add(row)
        db.commit()
    finally:
        db.close()


def save_tab_switch_db(session_id, user_id):
    db = SessionLocal()
    try:
        row = TabSwitchEvent(
            session_id=session_id,
            user_id=user_id
        )
        db.add(row)
        db.commit()
    finally:
        db.close()


def save_audio_alert_db(session_id, user_id, reason):
    db = SessionLocal()
    try:
        row = AudioAlert(
            session_id=session_id,
            user_id=user_id,
            reason=reason
        )
        db.add(row)
        db.commit()
    finally:
        db.close()

def detect_faces(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detector.process(rgb)

    if not results.detections:
        return 0

    return len(results.detections)

def detect_objects(frame):
    detections = []

    results = yolo_model(frame)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if cls in RESTRICTED_OBJECTS:
                detections.append({
                    "label": RESTRICTED_OBJECTS[cls],
                    "confidence": conf
                })

    return detections
def detect_looking_away(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return False

    landmarks = results.multi_face_landmarks[0].landmark

    left_eye = landmarks[33]
    right_eye = landmarks[263]
    nose = landmarks[1]

    center_x = (left_eye.x + right_eye.x) / 2
    deviation = abs(nose.x - center_x)

    return deviation > 0.08

@app.get("/")
def home():
    return {"message": "Proctor Service Running"}

@app.post("/analyze-frame")
async def analyze_frame(
    session_id: int = Form(...),
    user_id: int = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()

    npimg = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    alerts = []
    snapshots = []

    # FACE CHECK
    face_count = detect_faces(frame)

    if face_count == 0:
        reason = "No face detected"
        path = save_violation_image(frame, "no_face")
        save_violation_db(session_id, user_id, reason, path)

        alerts.append(reason)
        snapshots.append(path)

    elif face_count > 1:
        reason = "Multiple faces detected"
        path = save_violation_image(frame, "multiple_faces")
        save_violation_db(session_id, user_id, reason, path)

        alerts.append(reason)
        snapshots.append(path)

    # RESTRICTED OBJECT DETECTION
    objects = detect_objects(frame)

    for obj in objects:
        reason = f"{obj['label']} detected"
        path = save_violation_image(
            frame,
            obj["label"].replace(" ", "_").lower()
        )

        save_violation_db(
            session_id,
            user_id,
            reason,
            path,
            obj["confidence"]
        )

        alerts.append(reason)
        snapshots.append(path)

    if detect_looking_away(frame):
        reason = "Candidate looking away"
        path = save_violation_image(frame, "looking_away")
        save_violation_db(session_id, user_id, reason, path)

        alerts.append(reason)
        snapshots.append(path)

    return {
        "status": "ok",
        "alerts": alerts,
        "snapshots": snapshots
    }

@app.post("/tab-switch")
def tab_switch(
    session_id: int = Form(...),
    user_id: int = Form(...)
):
    save_tab_switch_db(session_id, user_id)
    return {"status": "logged"}

@app.post("/audio-alert")
def audio_alert(
    session_id: int = Form(...),
    user_id: int = Form(...),
    reason: str = Form(...)
):
    save_audio_alert_db(session_id, user_id, reason)
    return {"status": "logged"}

# GET ALL VIOLATIONS
@app.get("/violations")
def get_violations():
    db = SessionLocal()
    try:
        rows = db.query(ProctorViolation).all()
        return rows
    finally:
        db.close()

# GET TAB SWITCH EVENTS
@app.get("/tab-switch-events")
def get_tab_switch_events():
    db = SessionLocal()
    try:
        rows = db.query(TabSwitchEvent).all()
        return rows
    finally:
        db.close()

# GET AUDIO ALERTS
@app.get("/audio-alerts")
def get_audio_alerts():
    db = SessionLocal()
    try:
        rows = db.query(AudioAlert).all()
        return rows
    finally:
        db.close()