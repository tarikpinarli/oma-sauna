# main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from logic import generate_recommendation

# ---------- Supabase client ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---------- FastAPI app ----------
app = FastAPI()

# For now: allow everything (you can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    user_id: str
    steps: int
    heart_rate: float


@app.post("/generate-recommendation")
def generate_recommendation_endpoint(data: InputData):
    # 1) Run your Python recommendation logic
    result = generate_recommendation(
        user_id=data.user_id,
        steps=data.steps,
        heart_rate=data.heart_rate,
    )

    print("DEBUG result from generate_recommendation:", result)

    # 2) Normalize result
    score = None
    recommendation = None

    if isinstance(result, dict):
        score = result.get("score")
        recommendation = result.get("recommendation") or str(result)
    else:
        recommendation = str(result)

    # 3) Build payload to save & return
    payload = {
        "user_id": data.user_id,
        "steps": data.steps,
        "heart_rate": data.heart_rate,
        "score": score,
        "recommendation": recommendation,
    }

    # 4) Save to Supabase
    supabase.table("recommendations").insert(payload).execute()

    # 5) Return to caller
    return payload
