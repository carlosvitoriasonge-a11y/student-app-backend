from fastapi import APIRouter, HTTPException
import os
import json

router = APIRouter()

SAIRISHUU_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "sairishuu.json")
)

# -----------------------------
# Helpers
# -----------------------------
def load_sairishuu():
    if not os.path.exists(SAIRISHUU_FILE):
        return {}
    with open(SAIRISHUU_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sairishuu(data):
    with open(SAIRISHUU_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------
# GET → retornar JSON completo
# -----------------------------
@router.get("/get")
def get_sairishuu():
    return load_sairishuu()

# -----------------------------
# ADD → HYOKA manual = 1
# -----------------------------
@router.post("/add")
def add_sairishuu(payload: dict):
    student_id = payload.get("student_id")
    subject_id = payload.get("subject_id")

    if not student_id or not subject_id:
        raise HTTPException(status_code=400, detail="Missing fields")

    data = load_sairishuu()

    if student_id not in data:
        data[student_id] = {}

    if subject_id not in data[student_id]:
        data[student_id][subject_id] = {
            "status": "pending",
            "done_dates": [],
            "evaluation": None,
            "kanten": None
        }

    save_sairishuu(data)
    return {"status": "added"}

# -----------------------------
# REMOVE → HYOKA manual >= 2
# -----------------------------
@router.post("/remove")
def remove_sairishuu(payload: dict):
    student_id = payload.get("student_id")
    subject_id = payload.get("subject_id")

    if not student_id or not subject_id:
        raise HTTPException(status_code=400, detail="Missing fields")

    data = load_sairishuu()

    if student_id in data and subject_id in data[student_id]:
        del data[student_id][subject_id]

        if len(data[student_id]) == 0:
            del data[student_id]

        save_sairishuu(data)
        return {"status": "removed"}

    return {"status": "not_found"}

# -----------------------------
# ADD_DATE → registrar 1 回 de 再履修
# -----------------------------
@router.post("/add_date")
def add_rishuu_date(payload: dict):
    student_id = payload.get("student_id")
    subject_id = payload.get("subject_id")
    date = payload.get("date")

    if not student_id or not subject_id or not date:
        raise HTTPException(status_code=400, detail="Missing fields")

    data = load_sairishuu()

    if student_id not in data or subject_id not in data[student_id]:
        raise HTTPException(status_code=404, detail="Record not found")

    entry = data[student_id][subject_id]

    if entry["status"] == "passed":
        raise HTTPException(status_code=400, detail="Already completed")

    # adicionar data
    if "done_dates" not in entry:
        entry["done_dates"] = []

    entry["done_dates"].append(date)


    save_sairishuu(data)
    return {"status": "date_added"}

# -----------------------------
# COMPLETE → 再履修 concluído
# -----------------------------
@router.post("/complete")
def complete_sairishuu(payload: dict):
    student_id = payload.get("student_id")
    subject_id = payload.get("subject_id")
    school_year = payload.get("school_year")

    if not student_id or not subject_id or not school_year:
        raise HTTPException(status_code=400, detail="Missing fields")

    data = load_sairishuu()

    if student_id not in data or subject_id not in data[student_id]:
        raise HTTPException(status_code=404, detail="Record not found")

    entry = data[student_id][subject_id]

    entry["status"] = "passed"
    entry["school_year"] = school_year
    entry["evaluation"] = 3
    entry["kanten"] = "BBB"

    save_sairishuu(data)
    return {"status": "completed"}
