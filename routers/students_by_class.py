from fastapi import APIRouter
from utils.data import load_data


router = APIRouter()

@router.get("/students/by_class")
def get_students_by_class(course: str, grade: str, class_name: str):
    students = load_data()

    result = [
        s for s in students
        if s.get("course") == course
        and str(s.get("grade")) == str(grade)
        and s.get("class_name") == class_name
    ]

    return result
