from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import requests
import time

DATABASE_URL = "sqlite:///./checker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Database model — defines what a check result looks like in the database
class CheckResult(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    status_code = Column(Integer, nullable=True)
    is_up = Column(Boolean)
    response_time_ms = Column(Integer, nullable=True)
    checked_at = Column(DateTime, default=datetime.now)
    error = Column(String, nullable=True)

# Create the table if it doesn't exist yet
Base.metadata.create_all(bind=engine)


app = FastAPI()

#This wil allow the frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#This will define what a request to the body looks like
class URLRequest(BaseModel):
    url: str

HEADERS = {
    "User-Agent": "Mozilla/5.0 (url-checker-web)"
}

def check_url(url: str):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5, headers=HEADERS)
        elapsed_ms = round((time.time() - start_time) * 1000)
        status_code = response.status_code
        return {
            "url": url,
            "status_code": status_code,
            "is_up": status_code == 200,
            "response_time_ms": elapsed_ms,
            "checked_at": datetime.now().isoformat(),
            "error": None
        }
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        return {
            "url": url,
            "status_code": None,
            "is_up": False,
            "response_time_ms": None,
            "checked_at": datetime.now().isoformat(),
            "error": error_message
        }
    
def save_result(result: dict):
    db = SessionLocal()
    try:
        check = CheckResult(
            url=result["url"],
            status_code=result["status_code"],
            is_up=result["is_up"],
            response_time_ms=result["response_time_ms"],
            checked_at=datetime.fromisoformat(result["checked_at"]),
            error=result["error"]
        )
        db.add(check)
        db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "URL Checker API is running"}

@app.post("/check")
def check(request: URLRequest):
    result = check_url(request.url)
    save_result(result)
    return result

@app.get("/history")
def history():
    db = SessionLocal()
    try:
        checks = db.query(CheckResult).order_by(CheckResult.checked_at.desc()).limit(50).all()
        return [
            {
                "url": c.url,
                "status_code": c.status_code,
                "is_up": c.is_up,
                "response_time_ms": c.response_time_ms,
                "checked_at": c.checked_at.isoformat(),
                "error": c.error
            }
            for c in checks
        ]
    finally:
        db.close()