from fastapi import APIRouter, HTTPException
from utils.data import load_data, save_data
import json, os
from datetime import datetime

router = APIRouter()

# 卒業生ファイルの絶対パス
GRAD_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "graduates.json")
)

def load_graduates():
    if not os.path.exists(GRAD_FILE):
        return []
    with open(GRAD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_graduates(data):
    with open(GRAD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.post("/promote")
def promote_students(payload: dict):
    grade = str(payload.get("grade"))
    promote_ids = payload.get("promote_ids", [])

    students = load_data()
    graduates = load_graduates()

    promoted = 0
    stayed = 0
    graduated = 0

    new_students = []

    for s in students:
        s_grade = str(s["grade"])

        # 対象学年以外はそのまま残す
        if s_grade != grade:
            new_students.append(s)
            continue

        # 昇級 or 卒業対象
        if s["id"] in promote_ids:

            # ★ 3年生 → 卒業処理
            if grade == "3":
                this_year = datetime.now().year
                grad_nendo = f"{this_year - 1}年度"

                s["graduated_year"] = grad_nendo

                # ★ 卒業生はクラス情報を消す（必要）
                s["class_name"] = ""
                s["attend_no"] = ""

                graduates.append(s)
                graduated += 1

            else:
                # ★ 昇級処理
                s["grade"] = str(int(grade) + 1)

                # ★ 昇級後はクラスと出席番号をリセット
                s["class_name"] = ""
                s["attend_no"] = ""

                promoted += 1
                new_students.append(s)

        else:
            # ★ 留年（クラスと出席番号はそのまま）
            stayed += 1
            new_students.append(s)

    # 保存
    save_data(new_students)
    save_graduates(graduates)

    return {
        "promoted": promoted,
        "stayed": stayed,
        "graduated": graduated
    }
