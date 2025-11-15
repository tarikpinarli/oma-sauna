# main.py

import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# ---------- Supabase client ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---------- FastAPI app ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Input model ----------
class InputData(BaseModel):
    user_id: str


# ---------- SQLite config ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "recommendation.db")

SQL_SELECT_LATEST = """
    SELECT recommended_temp, recommended_hum, recommended_duration
    FROM recommendations
    ORDER BY rowid DESC
    LIMIT 1;
"""


def read_latest_from_sqlite():
    """Read latest (temp, hum, duration) from recommendation.db."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(SQL_SELECT_LATEST)
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("No rows found in recommendations table")

    recommended_temp, recommended_hum, recommended_duration = row
    return recommended_temp, recommended_hum, recommended_duration


@app.post("/generate-recommendation")
def generate_recommendation_endpoint(data: InputData):
    """
    1. Read latest recommendation from recommendation.db
    2. Insert {user_id, temp, humidity, duration} into Supabase
    3. Return same payload as JSON
    """
    try:
        temp, humidity, duration = read_latest_from_sqlite()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    payload = {
        "user_id": data.user_id,
        "temp": temp,
        "humidity": humidity,
        "duration": duration,
    }

    try:
        supabase.table("daily_recommendations").insert(payload).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert error: {e}")

    return payload
