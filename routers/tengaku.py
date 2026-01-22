from fastapi import APIRouter, HTTPException
import json
import os
from utils.date import school_year, now_iso
from main import load_students, save_students, DATA_DIR

router = APIRouter()

TENGAKU_FILE = os.path.join(DATA_DIR, "tengaku.json")

if not os.path.exists(TENGAKU_FILE):
    with open(TENGAKU_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


@router.post("/tengaku")
def tengaku_student(payload: dict):
    if payload.get("password") != os.environ.get("ADMIN_PASSWORD"):
        raise HTTPException(status_code=403, detail="Invalid password")

    student_id = payload["student_id"]
    date = payload["date"]
    destination_school = payload["destination_school"]

    students = load_students()
    student = next((s for s in students if s["id"] == student_id), None)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    event = {
        "event": "転学",
        "event_date": date,
        "destination_school": destination_school,
        "school_year": school_year(date),
        "timestamp": now_iso(),
        "student": student
    }

    with open(TENGAKU_FILE, encoding="utf-8") as f:
        tengaku = json.load(f)

    tengaku.append(event)

    with open(TENGAKU_FILE, "w", encoding="utf-8") as f:
        json.dump(tengaku, f, ensure_ascii=False, indent=2)

    students = [s for s in students if s["id"] != student_id]
    save_students(students)

    return {"status": "ok"}
