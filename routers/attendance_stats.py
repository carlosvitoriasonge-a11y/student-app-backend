import json
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from datetime import datetime

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
ATTENDANCE_DIR = BASE_DIR.parent / "attendance"

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

def empty_term():
    return {
        "school_days": 0,
        "attendance": 0,
        "absence": 0,
        "late": 0,
        "early": 0,
        "mourn": 0,
        "stopped": 0,
        "justified": 0
    }

# ---------------------------------------------------------
# FUNÇÃO PRINCIPAL — COMPLETA, FINAL
# ---------------------------------------------------------
def compute_attendance_stats(data: dict):
    dates = sorted(data.keys())
    if not dates:
        return {"class_stats": {}, "students": {}}

    first_date = datetime.strptime(dates[0], "%Y-%m-%d")
    school_year = first_date.year

    start = datetime(school_year, 4, 1)
    end = datetime(school_year + 1, 3, 31)

    class_zenki = empty_term()
    class_koki = empty_term()

    students = {}

    for date_str, entry in data.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        if not (start <= dt <= end):
            continue

        term_class = class_zenki if dt.month <= 9 else class_koki
        term_class["school_days"] += 1

        for sid, status in entry.get("students", {}).items():

            if sid not in students:
                students[sid] = {
                    "zenki": empty_term(),
                    "koki": empty_term()
                }

            term_student = students[sid]["zenki"] if dt.month <= 9 else students[sid]["koki"]
            term_student["school_days"] += 1

            if status in ATTENDANCE_MAP:
                for k, v in ATTENDANCE_MAP[status].items():
                    term_class[k] += v
                    term_student[k] += v

    def finalize(term):
        required = term["school_days"] - term["mourn"] - term["stopped"] - term["justified"]
        required = max(required, 0)
        rate = round(term["attendance"] / required * 100, 1) if required > 0 else 0
        term["required_attendance_days"] = required
        term["attendance_rate"] = rate

    finalize(class_zenki)
    finalize(class_koki)

    class_total = {k: class_zenki[k] + class_koki[k] for k in class_zenki if k not in ["required_attendance_days", "attendance_rate"]}
    finalize(class_total)

    for sid, st in students.items():
        zenki = st["zenki"]
        koki = st["koki"]

        finalize(zenki)
        finalize(koki)

        total = {k: zenki[k] + koki[k] for k in zenki if k not in ["required_attendance_days", "attendance_rate"]}
        finalize(total)

        students[sid] = {
            "zenki": zenki,
            "koki": koki,
            "total": total
        }

    return {
        "class_stats": {
            "zenki": class_zenki,
            "koki": class_koki,
            "total": class_total
        },
        "students": students
    }

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def build_filename(course, grade, class_name, school_year):
    safe_class = class_name.replace("/", "_")
    return ATTENDANCE_DIR / f"{course}-{grade}-{safe_class}-{school_year}.json"

# ---------------------------------------------------------
# /stats — por turma
# ---------------------------------------------------------
@router.get("/stats")
def get_attendance_stats(
    course: str = Query(...),
    grade: str = Query(...),
    class_name: str = Query(...),
    school_year: int = Query(...)
):
    filename = build_filename(course, grade, class_name, school_year)

    if not filename.exists():
        raise HTTPException(status_code=404, detail="Attendance file not found")

    with filename.open("r", encoding="utf-8") as f:
        data = json.load(f)

    stats = compute_attendance_stats(data)

    return {
        "course": course,
        "grade": grade,
        "class_name": class_name,
        "school_year": school_year,
        "stats": {
        "first_term": stats["class_stats"]["zenki"],
        "second_term": stats["class_stats"]["koki"],
        "total": stats["class_stats"]["total"]
    },
    "student_stats": {
        sid: {
            "first_term": st["zenki"],
            "second_term": st["koki"],
            "total": st["total"]
        }
        for sid, st in stats["students"].items()
    }
}
# ---------------------------------------------------------
# /stats/all — para a Svelte
# ---------------------------------------------------------
@router.get("/stats/all")
def get_attendance_stats_all():

    all_students = {}

    for file in ATTENDANCE_DIR.glob("*.json"):

        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        stats = compute_attendance_stats(data)

        for sid, st in stats["students"].items():

            all_students[sid] = {
                "first_term": st["zenki"],
                "second_term": st["koki"],
                "total": st["total"]
            }

    return {"student_stats": all_students}
