from fastapi import APIRouter
import os
import json

from utils.date import school_year

router = APIRouter()


def attendance_sub_path(class_id: str, date: str) -> str:
    """
    Caminho do arquivo de attendance de aulas.
    Exemplo: attendance_sub/全-1-1組-2025.json
    """
    sy = school_year(date)
    os.makedirs("attendance_sub", exist_ok=True)
    return f"attendance_sub/{class_id}-{sy}.json"


@router.get("")
def get_attendance_sub(date: str, course: str, grade: str, class_name: str):
    """
    Carrega TODAS as aulas (períodos) de um dia específico.
    Retorna no formato:
    {
        "classes": {
            "全-1-1組": {
                "2025-04-10": {
                    "１限目": { "subject": "...", "students": {...} },
                    "２限目": { ... }
                }
            }
        }
    }
    """
    class_id = f"{course}-{grade}-{class_name}"
    path = attendance_sub_path(class_id, date)

    if not os.path.exists(path):
        return {"classes": {}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # retorna só o dia solicitado
    return {
        "classes": {
            class_id: {
                date: data.get(date, {})
            }
        }
    }


@router.post("/save")
def save_attendance_sub(payload: dict):
    """
    Salva a presença de UMA aula (um período) dentro do arquivo do ano letivo.
    Estrutura:
    {
        "date": "2025-04-10",
        "period": "１限目",
        "subject": "論理表現Ⅰ",
        "classes": {
            "全-1-1組": {
                "students": {...}
            }
        }
    }
    """
    date = payload["date"]
    period = payload["period"]
    subject = payload["subject"]
    classes = payload["classes"]

    class_id = list(classes.keys())[0]
    students = classes[class_id]["students"]

    path = attendance_sub_path(class_id, date)

    # Se todos os alunos estão 未記録 → apagar o período
    if all(status == "未記録" for status in students.values()):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # remove o período
            if date in data and period in data[date]:
                del data[date][period]

            # se o dia ficou vazio → remove o dia
            if date in data and len(data[date]) == 0:
                del data[date]

            # se o arquivo ficou vazio → remove o arquivo
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

    # garante que a data existe
    if date not in data:
        data[date] = {}

    # salva o período
    data[date][period] = {
        "subject": subject,
        "students": students
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}
