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

            # tenta vários nomes possíveis de ano
            year = (
                e.get("school_year")
                or e.get("year")
                or e.get("exit_year")
                or e.get("graduated_year")
                or ""
            )

            year = str(year)

            if year not in result:
                result[year] = []

            student = e.get("student", {})

            result[year].append({
                "type": event_type,
                "student": {
                    "id": student.get("id", ""),
                    "name": student.get("name", ""),
                    "kana": student.get("kana", ""),
                    "gender": student.get("gender", ""),
                    # preserva campos extras
                    **{k: v for k, v in student.items()
                       if k not in ["id", "name", "kana", "gender"]}
                }
            })

    return result
