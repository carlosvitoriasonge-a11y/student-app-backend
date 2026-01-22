from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.data import load_data, save_data
from utils.security import check_password


COURSE_LABEL_MAP = {
    "z": "全",
    "w": "水",
    "s": "集",
}


router = APIRouter()


class CourseChangeRequest(BaseModel):
    student_id: str
    new_course: str
    password: str


def get_next_attend_no(students, grade, course, exclude_id=None):
    course_label = COURSE_LABEL_MAP[course]
    nums = [
        int(s["attend_no"])
        for s in students
        if s.get("grade") == grade
        and s.get("course") == course_label
        and s.get("id") != exclude_id
        and str(s.get("attend_no", "")).isdigit()
    ]
    return max(nums) + 1 if nums else 1


@router.post("/change_course")
def change_course(req: CourseChangeRequest):
    check_password(req.password)

    if req.new_course not in ("z", "s", "w"):
        raise HTTPException(status_code=400, detail="Invalid course")

    data = load_data()

    student = next((s for s in data if s.get("id") == req.student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.get("course") == COURSE_LABEL_MAP[req.new_course]:
        return {
            "status": "no_change",
            "course": student.get("course"),
            "class_name": student.get("class_name"),
            "attend_no": student.get("attend_no"),
        }

    # -------------------------
    # z → クラスなし（リセット）
    # -------------------------
    if req.new_course == "z":
        student["course"] = COURSE_LABEL_MAP["z"]
        student["class_name"] = ""
        student["attend_no"] = ""

    # -------------------------
    # s / w → クラスあり（自動番号）
    # -------------------------
    else:
        student["course"] = COURSE_LABEL_MAP[req.new_course]
        student["class_name"] = "1組"
        student["attend_no"] = get_next_attend_no(
            data,
            student.get("grade"),
            req.new_course,
            exclude_id=student["id"]
        )

    save_data(data)

    return {
        "status": "ok",
        "course": student["course"],
        "class_name": student["class_name"],
        "attend_no": student["attend_no"],
    }
