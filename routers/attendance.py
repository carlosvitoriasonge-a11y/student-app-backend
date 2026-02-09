# backend/routers/attendance.py

from fastapi import APIRouter
import os
import json

from utils.date import school_year

router = APIRouter()


def attendance_path(class_id: str, date: str) -> str:
    """
    Retorna o caminho do arquivo JSON baseado no ano letivo japonês.
    Exemplo: attendance/全-1-1組-2025.json
    """
    sy = school_year(date)
    os.makedirs("attendance", exist_ok=True)
    return f"attendance/{class_id}-{sy}.json"


@router.get("")
def get_attendance(date: str, course: str, grade: str, class_name: str):
    """
    Carrega a presença de um dia específico.
    Retorna apenas o dia solicitado, no formato que o frontend espera.
    """
    class_id = f"{course}-{grade}-{class_name}"
    path = attendance_path(class_id, date)

    if not os.path.exists(path):
        return {"classes": {}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # retorna só o dia solicitado
    return {
        "classes": {
            class_id: data.get(date, {})
        }
    }


@router.post("/save")
def save_attendance(payload: dict):
    """
    Salva a presença de um dia específico dentro do arquivo do ano letivo.
    """
    date = payload["date"]
    classes = payload["classes"]

    # classes = { "全-1-1組": { "students": {...} } }
    class_id = list(classes.keys())[0]
    students = classes[class_id]["students"]

    path = attendance_path(class_id, date)

    # carrega arquivo existente ou cria novo
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # salva apenas o dia
    data[date] = {"students": students}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}
