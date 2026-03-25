from fastapi import APIRouter
import os, json

router = APIRouter()


def hoshuu_file_path(course, grade, class_name, sy):
    os.makedirs("hoshuu", exist_ok=True)
    return f"hoshuu/{course}-{grade}-{class_name}-{sy}.json"


@router.post("/save")
def save_hoshuu(payload: dict):
    student_id = payload["student_id"]
    subject_id = payload["subject_id"]
    date = payload["date"]
    course = payload["course"]
    grade = payload["grade"]
    class_name = payload["class_name"]
    sy = payload["sy"]

    path = hoshuu_file_path(course, grade, class_name, sy)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if student_id not in data:
        data[student_id] = {}

    if subject_id not in data[student_id]:
        data[student_id][subject_id] = []

    data[student_id][subject_id].append(date)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}


@router.get("/get")
def get_hoshuu(course: str, grade: str, class_name: str, sy: int):
    path = hoshuu_file_path(course, grade, class_name, sy)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
