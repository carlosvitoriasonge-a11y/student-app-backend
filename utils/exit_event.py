import json
import os
from main import DATA_DIR

FILES = {
    "退学": "taigaku.json",
    "転学": "tengaku.json",
    "除籍": "joseki.json"
}

def load_exit_events():
    result = {}

    for event_type, filename in FILES.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue

        with open(path, encoding="utf-8") as f:
            events = json.load(f)

        for e in events:
            year = str(int(e["school_year"]))

            if year not in result:
                result[year] = []

            result[year].append({
                "type": event_type,
                "student": {
                    "id": e["student"]["id"],
                    "name": e["student"]["name"],
                    "kana": e["student"]["kana"],
                    "gender": e["student"]["gender"]
                }
            })

    return result
