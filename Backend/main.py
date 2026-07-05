from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
from datetime import datetime

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
    

@app.get("/")
def root():
    return {"message": "URL Checker API is running"}

@app.post("/check")
def check(request: URLRequest):
    result = check_url(request.url)
    return result