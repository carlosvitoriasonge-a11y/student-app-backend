from fastapi import APIRouter, HTTPException
from schemas.student import ReportItem
from utils.data import load_data, save_data
import uuid

router = APIRouter()


# -----------------------------
# GET — listar reports do aluno
# -----------------------------
@router.get("/{student_id}")
def get_reports(student_id: str):
    data = load_data()

    student = next((s for s in data if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student.get("reports", {})


# -----------------------------
# POST — adicionar report
# -----------------------------
@router.post("/{student_id}/{year}/{subject_id}")
def add_report(student_id: str, year: str, subject_id: str, item: ReportItem):
    data = load_data()

    student = next((s for s in data if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # cria bloco reports se não existir
    if "reports" not in student:
        student["reports"] = {}

    # cria bloco do ano se não existir
    if year not in student["reports"]:
        student["reports"][year] = {"subjects": {}}

    # cria bloco da matéria se não existir
    if subject_id not in student["reports"][year]["subjects"]:
        student["reports"][year]["subjects"][subject_id] = {
            "required": 0,
            "submitted": 0,
            "items": []
        }

    subject_block = student["reports"][year]["subjects"][subject_id]

    # cria ID se não vier
    new_item = item.dict()
    if not new_item.get("id"):
        new_item["id"] = str(uuid.uuid4())

    subject_block["items"].append(new_item)
    subject_block["submitted"] = len(subject_block["items"])

    save_data(data)

    return {"status": "ok", "item": new_item}


# -----------------------------
# PUT — editar report
# -----------------------------
@router.put("/{student_id}/{year}/{subject_id}/{report_id}")
def update_report(student_id: str, year: str, subject_id: str, report_id: str, item: ReportItem):
    data = load_data()

    student = next((s for s in data if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        subject_block = student["reports"][year]["subjects"][subject_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Report not found")

    for i, rep in enumerate(subject_block["items"]):
        if rep["id"] == report_id:
            updated = item.dict()
            updated["id"] = report_id
            subject_block["items"][i] = updated
            save_data(data)
            return {"status": "ok"}

    raise HTTPException(status_code=404, detail="Report item not found")


# -----------------------------
# DELETE — remover report
# -----------------------------
@router.delete("/{student_id}/{year}/{subject_id}/{report_id}")
def delete_report(student_id: str, year: str, subject_id: str, report_id: str):
    data = load_data()

    student = next((s for s in data if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        subject_block = student["reports"][year]["subjects"][subject_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Report not found")

    before = len(subject_block["items"])
    subject_block["items"] = [r for r in subject_block["items"] if r["id"] != report_id]
    after = len(subject_block["items"])

    if before == after:
        raise HTTPException(status_code=404, detail="Report item not found")

    subject_block["submitted"] = after

    save_data(data)

    return {"status": "ok"}
