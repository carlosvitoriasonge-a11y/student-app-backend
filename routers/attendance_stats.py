import json
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from services.attendance_stats import compute_attendance_stats

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent # pasta routers/ 
ATTENDANCE_DIR = BASE_DIR.parent / "attendance"


def build_filename(course, grade, class_name, school_year):
    safe_class = class_name.replace("/", "_")
    return ATTENDANCE_DIR / f"{course}-{grade}-{safe_class}-{school_year}.json" 
    # → 全-1-1組-2025.json


@router.get("/stats")
def get_attendance_stats(
    course: str = Query(...),
    grade: str = Query(...),
    class_name: str = Query(...),
    school_year: int = Query(...)
):
    filename = build_filename(course, grade, class_name, school_year)

    print(">>> LENDO ARQUIVO:", filename.absolute()) 
    print(">>> EXISTE?", filename.exists())

    if not filename.exists():
        raise HTTPException(status_code=404, detail="Attendance file not found")

    with filename.open("r", encoding="utf-8") as f:
        data = json.load(f)

    stats = compute_attendance_stats(data)

    dailyAttendance = {}
    for date, entry in data.items():
        if "students" not in entry:
            continue
        dailyAttendance[date] = {}

        for student_id, status in entry["students"].items():
            if status not in dailyAttendance[date]:
                dailyAttendance[date][status] = 0

            dailyAttendance[date][status] += 1


    return {
    "course": course,
    "grade": grade,
    "class_name": class_name,
    "school_year": school_year,
    "stats": stats["class_stats"],        # estatística da turma
    "student_stats": stats["students"],    # estatística por aluno
    "dailyAttendance": dailyAttendance   
    }

