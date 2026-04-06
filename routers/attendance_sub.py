from fastapi import APIRouter
import os
import json

from utils.date import school_year

router = APIRouter()


def attendance_sub_path(class_id: str, date: str) -> str:
    """
    Caminho do arquivo de attendance de aulas.
    Exemplo: attendance_sub/全-1-1組-2025.json
    """
    sy = school_year(date)
    os.makedirs("attendance_sub", exist_ok=True)
    return f"attendance_sub/{class_id}-{sy}.json"

@router.get("")
def get_attendance_sub(date: str, course: str, grade: str, class_name: str):
    """
    Suporta:
    - class_name="1組" → retorna só essa turma
    - class_name="ALL" → retorna TODAS as turmas reais do 学年
    """

    # ==========================
    # 学年集会: class_name=ALL
    # ==========================
    if class_name == "ALL":
        from utils.data import load_data
        all_students = load_data()

        # pegar todas as classes reais
        class_names = sorted({
            s.get("class_name")
            for s in all_students
            if s.get("course") == course and str(s.get("grade")) == str(grade)
        })

        result = {"classes": {}}

        for cn in class_names:
            class_id = f"{course}-{grade}-{cn}"
            path = attendance_sub_path(class_id, date)

            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result["classes"][class_id] = {date: data.get(date, {})}
            else:
                result["classes"][class_id] = {date: {}}

        return result

    # ==========================
    # Turma normal
    # ==========================
    class_id = f"{course}-{grade}-{class_name}"
    path = attendance_sub_path(class_id, date)

    if not os.path.exists(path):
        return {"classes": {}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "classes": {
            class_id: {
                date: data.get(date, {})
            }
        }
    }


@router.post("/save")
def save_attendance_sub(payload: dict):
    """
    Salva a presença de UMA aula (um período) dentro do arquivo do ano letivo.
    Agora suporta múltiplas classes (学年集会).
    """
    date = payload["date"]
    period = payload["period"]
    subject = payload["subject"]
    classes = payload["classes"]

    # ⭐ Agora iteramos TODAS as classes enviadas pelo Svelte
    for class_id, info in classes.items():
        students = info["students"]
        path = attendance_sub_path(class_id, date)

        # Se todos os alunos estão 未記録 → apagar o período
        if all(status == "未記録" for status in students.values()):
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # remove o período
                if date in data and period in data[date]:
                    del data[date][period]

                # se o dia ficou vazio → remove o dia
                if date in data and len(data[date]) == 0:
                    del data[date]

                # se o arquivo ficou vazio → remove o arquivo
                if len(data) == 0:
                    os.remove(path)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

            continue  # passa para a próxima classe

        # carrega arquivo existente ou cria novo
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # garante que a data existe
        if date not in data:
            data[date] = {}

        # salva o período
        data[date][period] = {
            "subject": subject,
            "subject_id": payload["subject_id"],
            "students": students
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}
