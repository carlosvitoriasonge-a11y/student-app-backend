from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.data import load_data, save_data

router = APIRouter()

# ============================================================
# 既存の API（出席番号振り直し）
# ============================================================

class RenumberRequest(BaseModel):
    grade: str
    class_name: str


@router.post("/renumber")
def renumber_attendance_numbers(req: RenumberRequest):
    data = load_data()

    target_students = [
        s for s in data
        if s.get("grade") == req.grade and s.get("class_name") == req.class_name
    ]

    if not target_students:
        raise HTTPException(
            status_code=404,
            detail=f"{req.grade}年 {req.class_name} に該当する生徒がいません"
        )

    target_students_sorted = sorted(target_students, key=lambda x: x.get("kana", ""))

    for i, s in enumerate(target_students_sorted, start=1):
        s["attend_no"] = i

    id_to_student = {s["id"]: s for s in target_students_sorted}
    for idx, s in enumerate(data):
        sid = s.get("id")
        if sid in id_to_student:
            data[idx] = id_to_student[sid]

    save_data(data)

    return {
        "status": "renumbered",
        "grade": req.grade,
        "class_name": req.class_name,
        "students": target_students_sorted,
    }


# ============================================================
# 新規 API ①：クラス分けプレビュー（保存しない）
# ============================================================

class PreviewRequest(BaseModel):
    grade: str
    course: str
    class_name: str
    student_ids: list[str]


@router.post("/preview")
def preview_class_assignment(req: PreviewRequest):
    data = load_data()

    # 対象生徒を抽出
    selected = [s for s in data if s["id"] in req.student_ids]

    if not selected:
        raise HTTPException(status_code=404, detail="選択された生徒が見つかりません")

    # 読み仮名順に並べ替え
    sorted_students = sorted(selected, key=lambda x: x.get("kana", ""))

    # 出席番号付与
    for i, s in enumerate(sorted_students, start=1):
        s["attend_no"] = i

    # 男女カウント（日本語対応）
    male = sum(1 for s in sorted_students if s.get("gender") == "男")
    female = sum(1 for s in sorted_students if s.get("gender") == "女")

    return {
        "class_name": req.class_name,
        "students": sorted_students,
        "male": male,
        "female": female,
        "total": len(sorted_students)
    }



# ============================================================
# 新規 API ②：クラス登録（1クラスずつ保存）
# ============================================================

class CommitRequest(BaseModel):
    class_name: str
    students: list[dict]  # {id, attend_no}


@router.post("/commit")
def commit_class(req: CommitRequest):
    data = load_data()

    id_map = {s["id"]: s for s in data}

    for entry in req.students:
        sid = entry["id"]
        if sid not in id_map:
            raise HTTPException(status_code=404, detail=f"ID {sid} が存在しません")

        id_map[sid]["class_name"] = req.class_name
        id_map[sid]["attend_no"] = entry["attend_no"]

    save_data(list(id_map.values()))

    return {
        "status": "saved",
        "class_name": req.class_name,
        "count": len(req.students)
    }


# ============================================================
# 新規 API ③：単一クラス（wednesday / intensive）用
# ============================================================

class SingleClassRequest(BaseModel):
    grade: str
    course: str


@router.post("/single")
def assign_single_class(req: SingleClassRequest):
    data = load_data()

    targets = [
        s for s in data
        if s.get("grade") == req.grade and s.get("course") == req.course
    ]

    if not targets:
        raise HTTPException(status_code=404, detail="該当する生徒がいません")

    # 読み仮名順
    sorted_students = sorted(targets, key=lambda x: x.get("kana", ""))

    # 出席番号付与
    for i, s in enumerate(sorted_students, start=1):
        s["class_name"] = "1組"
        s["attend_no"] = i

    save_data(data)

    return {
        "status": "ok",
        "assigned": [
            {"id": s["id"], "attend_no": s["attend_no"]}
            for s in sorted_students
        ]
    }
