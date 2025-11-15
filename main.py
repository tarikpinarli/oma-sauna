# main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from logic import generate_recommendation

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI()

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
    # 1) Call the shared “brain”
    result = generate_recommendation(
        user_id=data.user_id,
        steps=data.steps,
        heart_rate=data.heart_rate,
    )

    print("DEBUG result from generate_recommendation:", result)

    if not isinstance(result, dict):
        # Force into a dict if colleague ever returns a string, etc.
        result = {
            "user_id": data.user_id,
            "steps": data.steps,
            "heart_rate": data.heart_rate,
            "recommendation": str(result),
        }

    # 2) Ensure required keys exist (fallbacks)
    payload = {
        "user_id": result.get("user_id", data.user_id),
        "generated_at": result.get("generated_at"),
        "temperature": result.get("temperature"),
        "suggested_duration": result.get("suggested_duration"),
        "intensity": result.get("intensity"),
        "notes": result.get("notes"),
        "raw_health_data": result.get("raw_health_data"),
        "heart_rate": result.get("heart_rate", data.heart_rate),
        "recommendation": result.get("recommendation"),
        "score": result.get("score"),
        "steps": result.get("steps", data.steps),
    }

    # 3) Insert into Supabase
    supabase.table("daily_recommendations").insert(payload).execute()

    # 4) Return payload as API response
    return payload
