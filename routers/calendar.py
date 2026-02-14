from fastapi import APIRouter, HTTPException, Request
import os
import requests
from datetime import datetime

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


@router.get("/callback")
async def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    r = requests.post(token_url, data=data)
    token_data = r.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to get Google token")

    return {
        "google_access_token": token_data["access_token"]
    }


@router.get("/events")
async def get_today_events(request: Request):
    # O token do Google vem do frontend no header X-Google-Token
    google_token = request.headers.get("X-Google-Token")

    if not google_token:
        raise HTTPException(status_code=401, detail="Google access token missing")

    # Intervalo de hoje
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    url = (
        "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        f"?timeMin={start}&timeMax={end}&singleEvents=true&orderBy=startTime"
    )

    headers = {"Authorization": f"Bearer {google_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Google Calendar events")

    data = response.json()

    events = []
    for item in data.get("items", []):
        events.append({
            "id": item.get("id"),
            "summary": item.get("summary", "(Sem título)"),
            "start": item["start"].get("dateTime"),
            "end": item["end"].get("dateTime")
        })

    return events


