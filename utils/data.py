import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

os.makedirs(DATA_DIR, exist_ok=True)

STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")

def load_data():
    if not os.path.exists(STUDENTS_FILE):
        return []
    with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    for s in data:
        if "status" not in s or not s["status"]:
            s["status"] = "在籍"
            changed = True

        if "suspension_history" not in s:
            s["suspension_history"] = []
            changed = True

    if changed:
        save_data(data)

    return data

def save_data(data):
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
