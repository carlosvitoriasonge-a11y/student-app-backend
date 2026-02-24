from fastapi import APIRouter
from pydantic import BaseModel
import os, json

router = APIRouter()

# ============================================================
# PATH ABSOLUTO — AGORA O BACKEND SEMPRE LÊ E ESCREVE NO MESMO LUGAR
# ============================================================
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
BASE_DIR = os.path.abspath(BASE_DIR)


class TaskPayload(BaseModel):
    date: str
    label: str = ""


def build_path(course, grade, class_name, year_key):
    # year_key = "2025_1st"
    school_year, semester = year_key.split("_")

    filename = f"{school_year}-{course}-{grade}-{class_name}-{semester}.json"
    return os.path.join(BASE_DIR, filename)



def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# GET — retorna SOMENTE tasks
# ---------------------------------------------------------
@router.get("/class/{course}/{grade}/{class_name}/{year_key}/tasks")
def get_class_tasks(course: str, grade: str, class_name: str,
                    year_key: str, subject_id: str):

    path = build_path(course, grade, class_name, year_key)
    print("GET TASKS FROM:", path)

    report = load_json(path, {"subjects": {}})

    subject = report["subjects"].setdefault(subject_id, {
        "required": 0,
        "tasks": []
    })

    return subject["tasks"]


# ---------------------------------------------------------
# POST — criar nova tarefa
# ---------------------------------------------------------
@router.post("/class/{course}/{grade}/{class_name}/{year_key}/{subject_id}")
def create_task(course: str, grade: str, class_name: str,
                year_key: str, subject_id: str, payload: TaskPayload):

    path = build_path(course, grade, class_name, year_key)
    print("CREATE TASK →", path)

    report = load_json(path, {"subjects": {}})

    subject = report["subjects"].setdefault(subject_id, {
        "required": 0,
        "tasks": []
    })

    subject["tasks"].append({
        "date": payload.date,
        "label": payload.label,
        "submitted": []
    })

    save_json(path, report)
    return {"status": "ok"}


# ---------------------------------------------------------
# POST — toggle checkbox
# ---------------------------------------------------------
@router.post("/toggle/{course}/{grade}/{class_name}/{student_id}/{year_key}/{subject_id}/{task_index}")
def toggle_task(course: str, grade: str, class_name: str,
                student_id: str, year_key: str, subject_id: str, task_index: int):

    path = build_path(course, grade, class_name, year_key)
    print("TOGGLE TASK →", path)

    report = load_json(path, {"subjects": {}})

    subject = report["subjects"].setdefault(subject_id, {
        "required": 0,
        "tasks": []
    })

    tasks = subject["tasks"]

    if task_index >= len(tasks):
        return {"status": "error", "detail": "task_index inválido"}

    submitted = tasks[task_index].setdefault("submitted", [])

    if student_id in submitted:
        submitted.remove(student_id)
    else:
        submitted.append(student_id)

    save_json(path, report)
    return {"status": "ok"}


# ---------------------------------------------------------
# EDITAR LABEL
# ---------------------------------------------------------
@router.post("/edit/{course}/{grade}/{class_name}/{year_key}/{subject_id}/{task_index}")
def edit_task(course: str, grade: str, class_name: str,
              year_key: str, subject_id: str, task_index: int, payload: TaskPayload):

    path = build_path(course, grade, class_name, year_key)
    print("EDIT TASK →", path)

    report = load_json(path, {"subjects": {}})

    subject = report["subjects"].setdefault(subject_id, {
        "required": 0,
        "tasks": []
    })

    tasks = subject["tasks"]

    if task_index >= len(tasks):
        return {"status": "error", "detail": "task_index inválido"}

    tasks[task_index]["label"] = payload.label

    save_json(path, report)
    return {"status": "ok"}


# ---------------------------------------------------------
# DELETE — apagar tarefa
# ---------------------------------------------------------
@router.delete("/delete/{course}/{grade}/{class_name}/{year_key}/{subject_id}/{task_index}")
def delete_task(course: str, grade: str, class_name: str,
                year_key: str, subject_id: str, task_index: int):

    path = build_path(course, grade, class_name, year_key)
    print("DELETE TASK →", path)

    report = load_json(path, {"subjects": {}})

    subject = report["subjects"].setdefault(subject_id, {
        "required": 0,
        "tasks": []
    })

    tasks = subject["tasks"]

    if task_index < 0 or task_index >= len(tasks):
        return {"status": "error", "detail": "task_index inválido"}

    tasks.pop(task_index)

    save_json(path, report)
    return {"status": "ok"}
