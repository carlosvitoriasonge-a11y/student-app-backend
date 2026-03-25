from fastapi import APIRouter 
from utils.data import load_data 

router = APIRouter()


@router.get("/classes")
def get_class_list(course: str | None = None, grade: str | None = None):
    students = load_data()
    classes = set()

    for s in students:
        # se course foi enviado, filtra
        if course is not None and s.get("course") != course:
            continue

        # se grade foi enviado, filtra
        if grade is not None and str(s.get("grade")) != str(grade):
            continue

        class_name = s.get("class_name")
        if not class_name:
            continue

        key = (s.get("course"), s.get("grade"), class_name)
        classes.add(key)

    return [
        {"course": c, "grade": g, "class_name": cn}
        for (c, g, cn) in classes
    ]
