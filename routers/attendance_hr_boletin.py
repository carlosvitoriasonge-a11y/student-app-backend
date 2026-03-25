from fastapi import APIRouter
import os, json
from datetime import datetime

router = APIRouter()

ATTENDANCE_MAP = {
    "出席": {"attendance": 1},
    "欠席": {"absence": 1},
    "遅刻": {"attendance": 1, "late": 1},
    "早退": {"attendance": 1, "early": 1},
    "忌引き": {"mourn": 1},
    "出席停止": {"stopped": 1},
    "公欠": {"justified": 1},
    "遅刻と早退": {"attendance": 1, "late": 1, "early": 1}
}

def init_term():
    return {
        "school_days": 0,
        "required_attendance_days": 0,
        "attendance": 0,
        "absence": 0,
        "late": 0,
        "early": 0,
        "mourn": 0,
        "stopped": 0,
        "justified": 0,
        "attendance_rate": 0
    }

def add_status(term, status):
    if status in ATTENDANCE_MAP:
        for k, v in ATTENDANCE_MAP[status].items():
            term[k] += v

def finalize_term(term):
    required = term["school_days"] - term["mourn"] - term["stopped"] - term["justified"]
    required = max(required, 0)
    term["required_attendance_days"] = required

    if required > 0:
        term["attendance_rate"] = round((term["attendance"] / required) * 100, 1)
    else:
        term["attendance_rate"] = 0


@router.get("/hr")
def get_hr_attendance(course: str, grade: str, class_name: str, sy: int):
    """
    Retorna presença HR separada em:
    - zenki (4–9月)
    - koki (10–3月)
    - total
    """

    class_id = f"{course}-{grade}-{class_name}"
    path = f"attendance/{class_id}-{sy}.json"

    if not os.path.exists(path):
        return {"error": "attendance file not found"}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # preparar estrutura
    result = {}

    # inicializar alunos
    # (vamos descobrir os alunos lendo todos os IDs do arquivo)
    all_student_ids = set()
    for entry in data.values():
        if "students" in entry:
            all_student_ids.update(entry["students"].keys())

    for sid in all_student_ids:
        result[sid] = {
            "zenki": init_term(),
            "koki": init_term(),
            "total": init_term()
        }

    # processar cada dia
    for date_str, entry in data.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month

        period = "zenki" if month in [4,5,6,7,8,9] else "koki"

        for sid, status in entry.get("students", {}).items():
            if sid not in result:
                continue

            # zenki/koki
            result[sid][period]["school_days"] += 1
            add_status(result[sid][period], status)

            # total
            result[sid]["total"]["school_days"] += 1
            add_status(result[sid]["total"], status)

    # finalizar cálculos
    for sid in result:
        finalize_term(result[sid]["zenki"])
        finalize_term(result[sid]["koki"])
        finalize_term(result[sid]["total"])

    return result
