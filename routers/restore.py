from fastapi import APIRouter
from pydantic import BaseModel
from utils.data import load_data, save_data
import json
import os

router = APIRouter()

class RestoreRequest(BaseModel):
    restore_ids: list[str]


@router.post("")
def restore_students(req: RestoreRequest):
    # 在校生データ
    students = load_data()

    # 卒業生データ
    graduates_path = "data/graduates.json"
    if os.path.exists(graduates_path):
        with open(graduates_path, "r", encoding="utf-8") as f:
            graduates_data = json.load(f)
    else:
        graduates_data = []

    restored = []
    new_graduates = []

    for g in graduates_data:
        if g["id"] in req.restore_ids:
            # 復学処理
            g["grade"] = "3"
            g["class"] = ""
            g.pop("attend_no", None)
            g.pop("graduated_year", None)
            restored.append(g)
            students.append(g)
        else:
            new_graduates.append(g)

    # 保存
    save_data(students)
    with open(graduates_path, "w", encoding="utf-8") as f:
        json.dump(new_graduates, f, ensure_ascii=False, indent=2)

    return {
        "status": "completed",
        "restored": len(restored)
    }
