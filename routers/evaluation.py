# routers/evaluation.py

from fastapi import APIRouter
import os, json
from utils.attendance_reader import extract_attendance_numbers
from utils.evaluation import compute_autonomy, evaluate_student
from utils.date import school_year
from datetime import date

router = APIRouter()

# ============================================================
# Helpers
# ============================================================

def path_eval(class_id, subject, sy):
    os.makedirs("evaluation", exist_ok=True)
    return f"evaluation/{class_id}-{subject}-{sy}.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def filter_semester(att, sem):
    if sem == "full":
        return att

    filtered = {}
    for date, periods in att.items():
        month = int(date.split("-")[1])

        if sem == "1" and 4 <= month <= 9:
            filtered[date] = periods

        if sem == "2" and (month >= 10 or month <= 3):
            filtered[date] = periods

    return filtered


# ============================================================
# GET /api/evaluation/class  → avaliação individual dos alunos
# ============================================================

@router.get("/class")
def get_class_evaluation(course: str, grade: int, class_name: str, subject: str):

    class_id = f"{course}-{grade}-{class_name}"
    today = date.today().isoformat()
    sy = school_year(today)

    # ------------------------------------------------------------
    # Subject
    # ------------------------------------------------------------
    subjects = load_json("data/subjects.json")
    subj = next((s for s in subjects if s["id"] == subject), None)

    if not subj:
        return {"error": "subject not found"}

    exam_freq = int(subj.get("exam_frequency", 1))
    required_reports = int(subj.get("required_reports", 0))

    # ------------------------------------------------------------
    # Students (arquivo único)
    # ------------------------------------------------------------
    all_students = load_json("data/students.json")

    # 🔥 Filtro correto baseado no SEU students.json
    students = [
        st for st in all_students
        if st.get("course") == course
        and str(st.get("grade")) == str(grade)
        and st.get("class_name") == class_name
    ]

    # ------------------------------------------------------------
    # Dados da turma
    # ------------------------------------------------------------
    attendance = load_json(f"attendance_sub/{class_id}-{sy}.json")
    REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))

    tasks_1st = load_json(os.path.join(
        REPORTS_DIR,
        f"{sy}-{course}-{grade}-{class_name}-1st.json"
    ))

    tasks_2nd = load_json(os.path.join(
        REPORTS_DIR,
        f"{sy}-{course}-{grade}-{class_name}-2nd.json"
    ))


    eval_path = path_eval(class_id, subject, sy)
    snapshots = load_json(eval_path)

    result = {}

    for st in students:
        sid = st["id"]  # << seu students.json usa "id", não "student_id"

        # ============================================================
        # AUTONOMIA
        # ============================================================
        att1 = filter_semester(attendance, "1")
        nums1 = extract_attendance_numbers(att1, sid)
        auto1 = compute_autonomy(nums1["present"], nums1["total"], nums1["negative"])

        att2 = filter_semester(attendance, "2")
        nums2 = extract_attendance_numbers(att2, sid)
        auto2 = compute_autonomy(nums2["present"], nums2["total"], nums2["negative"])

        autonomy_total = auto1 + auto2  # 0–40

        # ============================================================
        # TASKS
        # ============================================================

        def count_tasks(block):
            if "subjects" not in block:
                return 0
            if subject not in block["subjects"]:
                return 0

            submitted = 0
            for t in block["subjects"][subject].get("tasks", []):
                if sid in t.get("submitted", []):
                    submitted += 1
            return submitted

        sub1 = count_tasks(tasks_1st)
        sub2 = count_tasks(tasks_2nd)
        sub_total = sub1 + sub2

        print("TASK DEBUG:", sid, "sub1=", sub1, "sub2=", sub2, "total=", sub_total)

        # TESTE BRUTO: se entregou pelo menos 1 task, ganha 20 pontos
        # Cálculo real: proporcional ao número de tarefas entregues
        # Número total de tasks criadas (1st + 2nd)
        total_tasks_1 = len(tasks_1st.get("subjects", {}).get(subject, {}).get("tasks", []))
        total_tasks_2 = len(tasks_2nd.get("subjects", {}).get(subject, {}).get("tasks", []))
        total_tasks = total_tasks_1 + total_tasks_2

        # Cálculo real baseado nas tasks atribuídas
        if total_tasks > 0:
            task_percent = (sub_total / total_tasks) * 20
        else:
            task_percent = 0





        # ============================================================
        # PROVAS
        # ============================================================

        EXAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "exams"))

        exams_path = os.path.join(
            EXAMS_DIR,
            f"{sy}-{course}-{grade}-{class_name}.json"
        )

        exams_data = load_json(exams_path)


        exam_total = 0
        exam_count = 0

        subject_exams = exams_data.get(subj["id"], {})

        if exam_freq == 1:
            scores = subject_exams.get("single_exam", {})
            if sid in scores:
                exam_total += scores[sid]
                exam_count = 1

        elif exam_freq == 4:
            exam_keys = ["zenki_chukan", "zenki_kimatsu", "koki_chukan", "koki_kimatsu"]
            for key in exam_keys:
                scores = subject_exams.get(key, {})
                if sid in scores:
                    exam_total += scores[sid]
                    exam_count += 1

        # ============================================================
        # PERCENTUAL DE PROVAS
        # ============================================================
        if exam_count > 0:
            exam_percent = (exam_total / (exam_count * 100)) * 40
        else:
            exam_percent = 0

        # ============================================================
        # AVALIAÇÃO CONTÍNUA
        # ============================================================
        auto_grade = evaluate_student(
            exam_percent=exam_percent,
            task_percent=task_percent,
            autonomy_percent=autonomy_total
        )

        # ============================================================
        # SNAPSHOTS
        # ============================================================
        zenki_snapshot = snapshots.get(sid, {}).get("zenki_snapshot")
        final_snapshot = snapshots.get(sid, {}).get("final_snapshot")
        manual_final = snapshots.get(sid, {}).get("manual_final_grade")

        result[sid] = {
            "continuous": auto_grade,
            "zenki_snapshot": zenki_snapshot,
            "final_snapshot": final_snapshot,
            "final_grade": manual_final if manual_final else final_snapshot
        }

    return result


# ============================================================
# POST /api/evaluation/confirm-semester
# ============================================================

@router.post("/confirm-semester")
def confirm_semester(course: str, grade: int, class_name: str, subject: str, semester: int):

    if semester != 1:
        return {"error": "only semester=1 supported for snapshot"}

    class_id = f"{course}-{grade}-{class_name}"
    today = date.today().isoformat()
    sy = school_year(today)

    current = get_class_evaluation(course, grade, class_name, subject)

    eval_path = path_eval(class_id, subject, sy)
    snapshots = load_json(eval_path)

    for sid, data in current.items():
        if sid not in snapshots:
            snapshots[sid] = {}
        snapshots[sid]["zenki_snapshot"] = data["continuous"]

    save_json(eval_path, snapshots)

    return {"status": "zenki snapshot saved"}


# ============================================================
# POST /api/evaluation/finalize
# ============================================================

@router.post("/finalize")
def finalize_evaluation(course: str, grade: int, class_name: str, subject: str):

    class_id = f"{course}-{grade}-{class_name}"
    today = date.today().isoformat()
    sy = school_year(today)

    current = get_class_evaluation(course, grade, class_name, subject)

    eval_path = path_eval(class_id, subject, sy)
    snapshots = load_json(eval_path)

    for sid, data in current.items():
        if sid not in snapshots:
            snapshots[sid] = {}
        snapshots[sid]["final_snapshot"] = data["continuous"]

    save_json(eval_path, snapshots)

    return {"status": "final snapshot saved"}
