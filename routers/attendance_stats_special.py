from fastapi import APIRouter
import os, json
from datetime import datetime

router = APIRouter()

# ---------------------------------------------------------
# FUNÇÃO AUXILIAR PARA INICIALIZAR GRUPOS  ← MOVIDO PARA CIMA
# ---------------------------------------------------------
def init_group():
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

# ---------------------------------------------------------
# MAPEAMENTO DE MESES → GRUPOS (GRADE 2 E 3)
# ---------------------------------------------------------
def map_month_to_group(grade: str, month: int):
    if grade == "2":
        if month in [4, 5, 7, 8, 9]:
            return "senmon_zenki"
        if month == 6:
            return "koukou_zenki"
        if month in [11, 12, 1, 3]:
            return "senmon_koki"
        if month in [10, 2]:
            return "koukou_koki"

    if grade == "3":
        if month in [4, 5, 7, 8, 9]:
            return "senmon_zenki"
        if month == 6:
            return "koukou_zenki"
        if month in [11, 12, 2, 3]:
            return "senmon_koki"
        if month in [10, 1]:
            return "koukou_koki"

    return None

# ---------------------------------------------------------
# REGRAS DE APLICAÇÃO POR SCHOOL YEAR
# ---------------------------------------------------------
def is_special_target(sy: int, grade: str) -> bool:
    if sy == 2025 and grade in ["2", "3"]:
        return True
    if sy == 2026 and grade in ["2", "3"]:
        return True
    if sy == 2027 and grade == "3":
        return True
    return False

# ---------------------------------------------------------
# CAMINHO DO ARQUIVO DE ATTENDANCE
# ---------------------------------------------------------
def attendance_file_path(course, grade, class_name, sy):
    class_id = f"{course}-{grade}-{class_name}"
    return f"attendance/{class_id}-{sy}.json"

# ---------------------------------------------------------
# MAPA DE STATUS
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# ENDPOINT
# ---------------------------------------------------------
@router.get("/special")
def get_special_attendance_stats(course: str, grade: str, class_name: str, sy: int):

    if not is_special_target(sy, grade):
        return {"error": "Este sistema só se aplica a: sy=2025 (2,3), sy=2026 (2,3), sy=2027 (3)."}

    path = attendance_file_path(course, grade, class_name, sy)
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {}

    for date_str, entry in data.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month

        group = map_month_to_group(grade, month)
        if not group:
            continue

        for sid, status in entry.get("students", {}).items():

            if sid not in stats:
                stats[sid] = {
                    "senmon_zenki": init_group(),
                    "koukou_zenki": init_group(),
                    "senmon_koki": init_group(),
                    "koukou_koki": init_group()
                }

            stats[sid][group]["school_days"] += 1

            if status in ATTENDANCE_MAP:
                for k, v in ATTENDANCE_MAP[status].items():
                    stats[sid][group][k] += v

    for sid, groups in stats.items():
        for g in groups.values():
            required = g["school_days"] - g["mourn"] - g["stopped"] - g["justified"]
            required = max(required, 0)
            g["required_attendance_days"] = required
            g["attendance_rate"] = round((g["attendance"] / required) * 100, 1) if required > 0 else 0

    return stats
