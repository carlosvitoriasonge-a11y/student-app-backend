from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os
from datetime import datetime

router = APIRouter()


# ============================================================
# Helpers
# ============================================================

def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_school_year():
    """Retorna o ano escolar japonês (abril–março)."""
    today = datetime.now()
    year = today.year
    if today.month < 4:
        year -= 1
    return f"{year}年"


def get_subject_name(subject_id: str):
    """Procura o nome da matéria no arquivo subjects.json."""
    subjects_path = Path("data/subjects.json")
    if not subjects_path.exists():
        return "不明科目"

    try:
        with open(subjects_path, "r", encoding="utf-8") as f:
            subjects = json.load(f)
            for s in subjects:
                if s.get("id") == subject_id:
                    return s.get("name", "不明科目")
    except:
        pass

    return "不明科目"


# ============================================================
# ⭐ ENDPOINT PRINCIPAL — SALVAR TODAS AS NOTAS ⭐
# ============================================================

@router.post("")
async def save_final_all(payload: dict):
    """
    payload esperado:

    {
      "course": "全",
      "grade": 2,
      "class_name": "3組",
      "subject": "2025-z-056",
      "evaluations": {
        "2026-z-013": { "evaluation": 5, "kanten": "AAA" },
        "2026-z-014": { "evaluation": 4, "kanten": "BBB" }
      }
    }
    """

    course = payload.get("course")
    grade = payload.get("grade")
    class_name = payload.get("class_name")
    subject_id = payload.get("subject")
    evaluations = payload.get("evaluations", {})

    if not (course and grade and class_name and subject_id):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Nome do arquivo: 2025年_2_3組.json
    school_year = get_school_year()
    filename = f"{school_year}_{grade}_{class_name}.json"
    filepath = Path("data/hyoka") / filename

    # Carregar arquivo existente
    data = load_json(filepath)

    # Nome da matéria
    subject_name = get_subject_name(subject_id)

    # Atualizar cada aluno
    for student_id, ev in evaluations.items():
        if student_id not in data:
            data[student_id] = {}

        data[student_id][subject_id] = {
            "subject_name": subject_name,
            "evaluation": ev.get("evaluation"),
            "kanten": ev.get("kanten")
        }

    # Salvar
    save_json(filepath, data)

    return {
        "status": "ok",
        "saved": len(evaluations),
        "file": str(filepath)
    }
