import os
import json
from utils.data import load_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_student_id(year: str, course: str, students: list) -> str:
    prefix_map = {
        "z": "z",
        "w": "w",
        "s": "s"
    }

    prefix = prefix_map.get(course)
    if prefix is None:
        raise ValueError(f"不正なコースコードです: {course}")

    prefix_str = f"{year}-{prefix}-"

    # 在校生のIDを抽出（CSVで追加中の新規生徒も含む）
    ids = []
    for s in students:
        sid = s.get("id", "")
        if sid.startswith(prefix_str):
            parts = sid.split("-")
            if len(parts) == 3 and parts[2].isdigit():
                ids.append(int(parts[2]))

    # 卒業生もチェック
    graduates_path = os.path.join(BASE_DIR, "..", "data", "graduates.json")
    if os.path.exists(graduates_path):
        with open(graduates_path, "r", encoding="utf-8") as f:
            grads = json.load(f)
            for g in grads:
                gid = g.get("id", "")
                if gid.startswith(prefix_str):
                    parts = gid.split("-")
                    if len(parts) == 3 and parts[2].isdigit():
                        ids.append(int(parts[2]))

    next_seq = (max(ids) + 1) if ids else 1
    return f"{prefix_str}{next_seq:03d}".lower()
