from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os

router = APIRouter()

BASE_DIR = Path("data/exams")


def load_exams_file(course, grade, class_, year):
    # NOVO FORMATO DE ARQUIVO
    filename = f"{year}-{course}-{grade}-{class_}.json"
    path = BASE_DIR / filename

    if not path.exists():
        return {}, path

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


def save_exams_file(path, data):
    # garante que a pasta data/exams existe
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/class/{course}/{grade}/{class_}/{year}")
def get_exams(course: str, grade: int, class_: str, year: str, subject_id: str):
    data, _ = load_exams_file(course, grade, class_, year)
    return data.get(subject_id, {})


@router.post("/class/{course}/{grade}/{class_}/{year}/{subject_id}/{exam_key}/{student_id}")
def save_exam_score(course: str, grade: int, class_: str, year: str,
                    subject_id: str, exam_key: str, student_id: str,
                    payload: dict):

    raw = payload.get("score")

    data, path = load_exams_file(course, grade, class_, year)

    # 🔥 1) Se o professor apagou o campo → remover do JSON
    if raw in ("", None):
        if subject_id in data and exam_key in data[subject_id]:
            data[subject_id][exam_key].pop(student_id, None)
        save_exams_file(path, data)
        return {"status": "deleted"}

    # 🔥 2) Caso contrário → salvar normalmente
    score = int(raw)

    if subject_id not in data:
        data[subject_id] = {}

    if exam_key not in data[subject_id]:
        data[subject_id][exam_key] = {}

    data[subject_id][exam_key][student_id] = score

    save_exams_file(path, data)

    return {"status": "ok"}

