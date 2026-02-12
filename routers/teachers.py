from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from schemas.teacher import TeacherCreate, TeacherUpdate, TeacherOut

router = APIRouter()

DATA_PATH = Path("data/teachers.json")


def load_teachers():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_teachers(data):
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/", response_model=list[TeacherOut])
def get_all_teachers():
    return load_teachers()


@router.get("/{teacher_id}", response_model=TeacherOut)
def get_teacher(teacher_id: int):
    teachers = load_teachers()
    teacher = next((t for t in teachers if t["id"] == teacher_id), None)
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    return teacher


@router.post("/", response_model=TeacherOut)
def create_teacher(payload: TeacherCreate):
    teachers = load_teachers()

    new_id = max([t["id"] for t in teachers], default=0) + 1

    new_teacher = {
        "id": new_id,
        **payload.dict()
    }

    teachers.append(new_teacher)
    save_teachers(teachers)

    return new_teacher


@router.put("/{teacher_id}", response_model=TeacherOut)
def update_teacher(teacher_id: int, payload: TeacherUpdate):
    teachers = load_teachers()

    index = next((i for i, t in enumerate(teachers) if t["id"] == teacher_id), None)
    if index is None:
        raise HTTPException(404, "Teacher not found")

    teachers[index] = {
        "id": teacher_id,
        **payload.dict()
    }

    save_teachers(teachers)
    return teachers[index]


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int):
    teachers = load_teachers()

    new_list = [t for t in teachers if t["id"] != teacher_id]

    if len(new_list) == len(teachers):
        raise HTTPException(404, "Teacher not found")

    save_teachers(new_list)
    return {"status": "deleted"}
