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
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Input model (what Figma / Make sends) ----------
class InputData(BaseModel):
    user_id: str  # who this recommendation belongs to


# ---------- DB location & query ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "recommendation.db")

# 👇 Adjust these if your sqlite schema is different
SQL_SELECT_LATEST = """
    SELECT temp, humidity, duration
    FROM recommendations
    ORDER BY id DESC
    LIMIT 1;
"""


def read_latest_from_sqlite():
    """
    Open recommendation.db and read the latest temp, humidity, duration.
    """
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

    temp, humidity, duration = row
    return temp, humidity, duration


@app.post("/generate-recommendation")
def generate_recommendation_endpoint(data: InputData):
    """
    1. Read latest sauna recommendation from recommendation.db
    2. Insert {user_id, temp, humidity, duration} into Supabase (daily_recommendations)
    3. Return the same payload as JSON
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

    # Insert into Supabase table
    try:
        supabase.table("daily_recommendations").insert(payload).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase insert error: {e}")

    return payload
