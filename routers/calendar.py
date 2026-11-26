# routers/calendar.py
# Eventos de hoje do Google Calendar (somente leitura, via service account)
#
# Configuração (backend/.env):
#   GOOGLE_SERVICE_ACCOUNT_FILE=/caminho/fora/do/projeto/service-account.json
#   GOOGLE_CALENDAR_ID=eishin1325@gmail.com   (opcional; este é o padrão)
#
# A service account precisa de acesso de leitura ao calendário:
# compartilhar o calendário com o e-mail da service account
# ("Ver detalhes de todos os eventos").
#
# Sem a configuração, o endpoint responde configured=false e a tela
# inicial simplesmente não mostra o cartão — nada quebra.
#
# Substitui a tentativa anterior via OAuth (login do usuário), que nunca
# foi registrada no main.py e exigia login Google de cada usuário.

from fastapi import APIRouter
import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import jwt
import requests

router = APIRouter()

JST = ZoneInfo("Asia/Tokyo")
DEFAULT_CALENDAR_ID = "eishin1325@gmail.com"
TOKEN_URL = "https://oauth2.googleapis.com/token"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CACHE_SECONDS = 300  # 5 minutos

_token_cache = {"access_token": None, "expires_at": 0}
_events_cache = {"date": None, "fetched_at": 0, "events": []}


def _load_service_account():
    """Lê o JSON da service account; None se não estiver configurado."""
    path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _access_token(sa):
    """Token OAuth2 da service account (JWT assinado -> troca no Google)."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    issued = int(now)
    claim = {
        "iss": sa["client_email"],
        "scope": SCOPE,
        "aud": TOKEN_URL,
        "iat": issued,
        "exp": issued + 3600,
    }
    assertion = jwt.encode(claim, sa["private_key"], algorithm="RS256")

    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return data["access_token"]


def _format_event(item):
    """Normaliza um evento do Google para o formato da tela inicial."""
    start = item.get("start", {})
    end = item.get("end", {})
    title = item.get("summary", "(Sem título)")

    # Evento de dia inteiro: start/end vêm como "date" (YYYY-MM-DD),
    # sem "dateTime" — era aqui que a tentativa anterior quebrava.
    if "date" in start:
        return {
            "id": item.get("id"),
            "title": title,
            "all_day": True,
            "start": start["date"],
            "end": end.get("date"),
            "start_time": None,
            "end_time": None,
            "_sort": "0",
        }

    start_dt = datetime.fromisoformat(start["dateTime"]).astimezone(JST)
    end_dt = datetime.fromisoformat(end["dateTime"]).astimezone(JST)
    return {
        "id": item.get("id"),
        "title": title,
        "all_day": False,
        "start": start_dt.date().isoformat(),
        "end": end_dt.date().isoformat(),
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M"),
        "_sort": "1" + start_dt.strftime("%H:%M"),
    }


def _fetch_today_events(sa):
    today = datetime.now(JST).date()

    if (
        _events_cache["date"] == today
        and time.time() - _events_cache["fetched_at"] < CACHE_SECONDS
    ):
        return _events_cache["events"]

    token = _access_token(sa)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID") or DEFAULT_CALENDAR_ID

    start = datetime(today.year, today.month, today.day, tzinfo=JST)
    end = start + timedelta(days=1)

    r = requests.get(
        EVENTS_URL.format(calendar_id=quote(calendar_id, safe="")),
        headers={"Authorization": f"Bearer {token}"},
        params={
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeZone": "Asia/Tokyo",
            "maxResults": 100,
        },
        timeout=15,
    )
    r.raise_for_status()

    events = [_format_event(item) for item in r.json().get("items", [])]
    events.sort(key=lambda e: e["_sort"])
    for e in events:
        del e["_sort"]

    _events_cache["date"] = today
    _events_cache["fetched_at"] = time.time()
    _events_cache["events"] = events
    return events


@router.get("/today")
def today_events():
    today = datetime.now(JST).date().isoformat()

    sa = _load_service_account()
    if sa is None:
        return {"date": today, "configured": False, "events": []}

    try:
        events = _fetch_today_events(sa)
        return {"date": today, "configured": True, "events": events}
    except Exception as e:
        # Não derruba a tela inicial: devolve vazio e o erro para diagnóstico
        return {"date": today, "configured": True, "events": [], "error": str(e)}
