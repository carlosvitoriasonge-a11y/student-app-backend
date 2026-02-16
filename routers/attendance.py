# backend/routers/attendance.py

from fastapi import APIRouter
import os
import json

from utils.date import school_year

router = APIRouter()

STUDENTS_FILE = "data/students.json"


# carrega todos os alunos para saber status real (休学, 出席停止, etc)
with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
    ALL_STUDENTS = {s["id"]: s for s in json.load(f)}


def attendance_path(class_id: str, date: str) -> str:
    sy = school_year(date)
    os.makedirs("attendance", exist_ok=True)
    return f"attendance/{class_id}-{sy}.json"


@router.get("")
def get_attendance(date: str, course: str, grade: str, class_name: str):
    class_id = f"{course}-{grade}-{class_name}"
    path = attendance_path(class_id, date)

    if not os.path.exists(path):
        return {"classes": {}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "classes": {
            class_id: data.get(date, {})
        }
    }


@router.post("/save")
def save_attendance(payload: dict):
    date = payload["date"]
    classes = payload["classes"]

    class_id = list(classes.keys())[0]
    students = classes[class_id]["students"]

    # 🔥 FILTRO REAL:
    # remove alunos cujo status REAL é 休学 ou 出席停止
    filtered_students = {}

    for sid, status in students.items():
        student = ALL_STUDENTS.get(sid)

        if student:
            real_status = student.get("status")

            # IGNORA alunos suspensos ou 休学
            if real_status in ["休学", "出席停止"]:
                continue

        filtered_students[sid] = status

    path = attendance_path(class_id, date)

    # Se todos os alunos ativos estão 未記録 → apagar o registro do dia
    if all(status == "未記録" for status in filtered_students.values()):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if date in data:
                del data[date]

            if len(data) == 0:
                os.remove(path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        return {"status": "deleted"}

    # carrega arquivo existente ou cria novo
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # salva apenas alunos ativos
    data[date] = {"students": filtered_students}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}
