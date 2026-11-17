import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

PREF_FILE = os.path.join(DATA_DIR, "seating_preferences.json")

def load_seating_prefs():
    if not os.path.exists(PREF_FILE):
        return {}
    with open(PREF_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_seating_prefs(data):
    # Salvamento seguro (atômico + trava + backup) via data_manager
    from utils.data_manager import save_json
    save_json("seating_preferences.json", data)
