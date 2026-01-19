from fastapi import APIRouter
from utils.data import load_data, save_data

router = APIRouter()

@router.post("/demote")
def demote_students(payload: dict):
    demote_ids = payload.get("demote_ids", [])
    data = load_data()

    demoted = 0

    for s in data:
        if s["id"] in demote_ids:
            # 学年を1つ下げる（下限は1）
            current = int(s["grade"])
            new_grade = max(1, current - 1)
            s["grade"] = str(new_grade)

            # 出席番号リセット
            s["attend_no"] = None

            # クラス名は残す（あなたの仕様）
            demoted += 1

    save_data(data)

    return {"demoted": demoted}
