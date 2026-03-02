"""
Garmin Connect Cloud API
FastAPI wrapper around python-garminconnect library.
"""

import os
import logging
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from garminconnect import Garmin

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TOKEN_DIR = Path(os.getenv("GARMIN_TOKEN_DIR", "~/.garminconnect")).expanduser()
EMAIL = os.getenv("GARMIN_EMAIL", "")
PASSWORD = os.getenv("GARMIN_PASSWORD", "")
API_KEY = os.getenv("API_KEY", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Garmin Connect API",
    description="REST API para acessar dados do Garmin Connect",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Garmin client singleton
# ---------------------------------------------------------------------------
_garmin_client = None


def _login():
    global _garmin_client
    if _garmin_client is not None:
        return _garmin_client

    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    token_file = TOKEN_DIR / "tokens.json"
    client = Garmin(email=EMAIL, password=PASSWORD)

    if token_file.exists():
        try:
            logger.info("Resuming session from saved tokens...")
            client.login(token_file)
            _garmin_client = client
            return client
        except Exception:
            logger.warning("Saved tokens expired - doing full login")

    try:
        client.login()
        client.garth.dump(str(TOKEN_DIR))
        logger.info("Login successful - tokens saved")
    except Exception as exc:
        logger.error("Login failed: %s", exc)
        raise HTTPException(status_code=401, detail=f"Garmin login failed: {exc}")

    _garmin_client = client
    return client


def get_garmin():
    return _login()


# ---------------------------------------------------------------------------
# API Key middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if API_KEY:
        key = request.headers.get("X-API-Key", "")
        if key != API_KEY:
            return JSONResponse(status_code=403, content={"detail": "Invalid API key"})
    return await call_next(request)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Garmin Connect Cloud API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/user/profile")
def user_profile(garmin=Depends(get_garmin)):
    try:
        return garmin.get_user_profile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/settings")
def user_settings(garmin=Depends(get_garmin)):
    try:
        return garmin.get_user_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/today")
def stats_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_stats(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/{day}")
def stats_by_date(day: str, garmin=Depends(get_garmin)):
    try:
        return garmin.get_stats(day)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/heart-rate/today")
def heart_rate_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_heart_rates(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/heart-rate/{day}")
def heart_rate_by_date(day: str, garmin=Depends(get_garmin)):
    try:
        return garmin.get_heart_rates(day)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sleep/today")
def sleep_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_sleep_data(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sleep/{day}")
def sleep_by_date(day: str, garmin=Depends(get_garmin)):
    try:
        return garmin.get_sleep_data(day)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stress/today")
def stress_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_stress_data(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/body-composition/today")
def body_composition_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_body_composition(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/activities")
def activities(start: int = 0, limit: int = 20, garmin=Depends(get_garmin)):
    try:
        return garmin.get_activities(start, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/activities/{activity_id}")
def activity_detail(activity_id: int, garmin=Depends(get_garmin)):
    try:
        return garmin.get_activity(activity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/devices")
def devices(garmin=Depends(get_garmin)):
    try:
        return garmin.get_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/steps/today")
def steps_today(garmin=Depends(get_garmin)):
    try:
        today = date.today()
        return garmin.get_daily_steps(today.isoformat(), today.isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/steps/{start_date}/{end_date}")
def steps_range(start_date: str, end_date: str, garmin=Depends(get_garmin)):
    try:
        return garmin.get_daily_steps(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/spo2/today")
def spo2_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_spo2_data(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hrv/today")
def hrv_today(garmin=Depends(get_garmin)):
    try:
        return garmin.get_hrv_data(date.today().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/personal-records")
def personal_records(garmin=Depends(get_garmin)):
    try:
        return garmin.get_personal_record()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup():
    if EMAIL and PASSWORD:
        try:
            _login()
            logger.info("Garmin client ready")
        except Exception as exc:
            logger.error("Startup login failed: %s", exc)
    else:
        logger.warning("GARMIN_EMAIL / GARMIN_PASSWORD not set")
