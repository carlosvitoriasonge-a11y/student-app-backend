import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "students.json")

print("Corrigindo students.json...")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    students = json.load(f)

changed = False

for student in students:
    reports = student.get("reports", {})
    for year_key, year_data in reports.items():
        subjects = year_data.get("subjects", {})
        for subject_id, subject_data in subjects.items():
            if "required" not in subject_data:
                subject_data["required"] = 0
                changed = True
                print(f"Corrigido: {student['id']} -> {year_key} -> {subject_id}")

if changed:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)
    print("students.json corrigido com sucesso.")
else:
    print("Nenhuma correção necessária.")
