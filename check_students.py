import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "students.json")

print("Validando students.json...\n")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    students = json.load(f)

errors = []

for student in students:
    sid = student.get("id")
    reports = student.get("reports", {})

    for year_key, year_data in reports.items():
        subjects = year_data.get("subjects", {})

        for subject_id, subject_data in subjects.items():
            # Verifica se o campo "required" existe
            if "required" not in subject_data:
                errors.append(
                    f"[ERRO] Student {sid} | {year_key} | subject {subject_id} está sem 'required'"
                )

            # Verifica se "tasks" existe e é lista
            if "tasks" not in subject_data or not isinstance(subject_data["tasks"], list):
                errors.append(
                    f"[ERRO] Student {sid} | {year_key} | subject {subject_id} tem 'tasks' inválido"
                )

if errors:
    print("\n".join(errors))
    print("\n❌ Students.json contém erros.")
else:
    print("✔ Nenhum erro encontrado. students.json está válido.")

