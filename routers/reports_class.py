from fastapi import APIRouter, HTTPException
from utils.data import load_data

router = APIRouter()

@router.get("/class/{course}/{grade}/{class_name}/reports")
def get_class_reports(course: str, grade: str, class_name: str, subject_id: str):
    data = load_data()

    # filtrar alunos da turma
    students = [
        s for s in data
        if s.get("course") == course
        and s.get("grade") == grade
        and s.get("class_name") == class_name
    ]

    result = []

    for s in students:
        reports = s.get("reports", {})

        # pegar o ano atual do aluno
        year = s["year"]

        # garantir estrutura
        year_block = reports.get(year, {"subjects": {}})
        subj_block = year_block["subjects"].get(subject_id, {
            "required": 0,
            "submitted": 0,
            "items": []
        })

        items = subj_block["items"]
        submitted_count = sum(1 for i in items if i["status"] == "submitted")

        result.append({
            "id": s["id"],
            "name": s["name"],
            "year_key": year,
            "reports": {
                "required": subj_block["required"],
                "submitted": submitted_count,
                "items": items
            }
        })

    return result
