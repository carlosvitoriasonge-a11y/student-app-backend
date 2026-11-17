import os

from utils.data_manager import load_json, save_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

os.makedirs(DATA_DIR, exist_ok=True)

STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")

def load_data():
    if not os.path.exists(STUDENTS_FILE):
        return []
    data = load_json("students.json")

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
    # Salvamento seguro (atômico + trava + backup) via data_manager
    save_json("students.json", data)
