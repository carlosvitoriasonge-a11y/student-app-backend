from fastapi import APIRouter
import os, json, inspect
from utils.attendance_reader import extract_attendance_numbers
from utils.evaluation import compute_autonomy, evaluate_student
from utils.date import school_year
from datetime import date

router = APIRouter()

# ============================================================
# Helpers
# ============================================================

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
    for date_str, periods in att.items():
        month = int(date_str.split("-")[1])

        if sem == "1" and 4 <= month <= 9:
            filtered[date_str] = periods

        if sem == "2" and (month >= 10 or month <= 3):
            filtered[date_str] = periods

    return filtered

def filter_by_cutoff(attendance_dict, cutoff_date):
    return {
        d: v for d, v in attendance_dict.items()
        if d <= cutoff_date
    }


# ============================================================
# GET /api/evaluation/class
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
    # Students
    # ------------------------------------------------------------
    all_students = load_json("data/students.json")

    students = [
        st for st in all_students
        if st.get("course") == course
        and str(st.get("grade")) == str(grade)
        and st.get("class_name") == class_name
    ]

    # ------------------------------------------------------------
    # Attendance
    # ------------------------------------------------------------
    attendance_raw = load_json(f"attendance_sub/{class_id}-{sy}.json")

    caller = inspect.stack()[1].function

    if caller == "confirm_semester":
        cutoff_date = f"{sy}-09-30"
        attendance_raw = filter_by_cutoff(attendance_raw, cutoff_date)

    attendance_filtered = {}

    for date_str, periods in attendance_raw.items():
        for period, info in periods.items():
            if info.get("subject_id") == subject:
                if date_str not in attendance_filtered:
                    attendance_filtered[date_str] = {}
                attendance_filtered[date_str][period] = info

    attendance = attendance_filtered


    REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))

    tasks_1st = load_json(os.path.join(
        REPORTS_DIR,
        f"{sy}-{course}-{grade}-{class_name}-1st.json"
    ))

    tasks_2nd = load_json(os.path.join(
        REPORTS_DIR,
        f"{sy}-{course}-{grade}-{class_name}-2nd.json"
    ))

    # ============================================================
    # Procurar snapshot correto (ZENKI SOMENTE)
    # ============================================================

    snapshots = {}
    eval_dir = "evaluation"

    if os.path.exists(eval_dir):
        for fname in os.listdir(eval_dir):
            if not fname.endswith(".json"):
                continue

            full_path = os.path.join(eval_dir, fname)
            data = load_json(full_path)

            if (
                data.get("_subject_id") == subject
                and fname.startswith(f"{class_id}-{subj['subject_group']}-{sy}")
            ):
                snapshots = {
                    sid: {
                        "zenki_snapshot": snap.get("zenki_snapshot"),
                        "manual_final_grade": snap.get("manual_final_grade")
                    }
                    for sid, snap in data.items()
                    if isinstance(snap, dict)
                }
                break

    # ============================================================
    # Processar alunos
    # ============================================================

    result = {}

    for st in students:
        sid = st["id"]

        # AUTONOMIA (corrigido, sem duplicação)
        caller = inspect.stack()[1].function

        att1 = filter_semester(attendance, "1")
        nums1 = extract_attendance_numbers(att1, sid)
        auto1 = compute_autonomy(nums1["present"], nums1["total"], nums1["negative"])

        att2 = filter_semester(attendance, "2")
        nums2 = extract_attendance_numbers(att2, sid)
        auto2 = compute_autonomy(nums2["present"], nums2["total"], nums2["negative"])

        if caller == "confirm_semester":
            autonomy_total = auto1          # ZENKI
        elif caller == "finalize":
            autonomy_total = auto2          # KOKI
        else:
            # continuous = ano inteiro
            nums_full = extract_attendance_numbers(attendance, sid)
            autonomy_total = compute_autonomy(
                nums_full["present"],
                nums_full["total"],
                nums_full["negative"]
            )


        # TASKS
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

        total_tasks_1 = len(tasks_1st.get("subjects", {}).get(subject, {}).get("tasks", []))
        total_tasks_2 = len(tasks_2nd.get("subjects", {}).get(subject, {}).get("tasks", []))
        total_tasks = total_tasks_1 + total_tasks_2

        task_percent = (sub_total / total_tasks) * 20 if total_tasks > 0 else 0

        # PROVAS
        EXAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "exams"))

        exams_path = os.path.join(
            EXAMS_DIR,
            f"{sy}-{course}-{grade}-{class_name}.json"
        )

        exams_data = load_json(exams_path)

        exam_total = 0
        exam_count = 0

        subject_exams = exams_data.get(subject, {})

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

        exam_percent = (exam_total / (exam_count * 100)) * 40 if exam_count > 0 else 0

        # CONTÍNUA
        auto_grade = evaluate_student(
            exam_percent=exam_percent,
            task_percent=task_percent,
            autonomy_percent=autonomy_total
        )

        # SNAPSHOTS
        zenki_snapshot = snapshots.get(sid, {}).get("zenki_snapshot")
        manual_final = snapshots.get(sid, {}).get("manual_final_grade")

        result[sid] = {
            "continuous": auto_grade,
            "zenki_snapshot": zenki_snapshot,
            "final_snapshot": None,
            "final_grade": manual_final,
            "auto1": auto1,   # ← ADICIONE ISTO
            "auto2": auto2    # ← ADICIONE ISTO (opcional mas útil)
        }

    return result


# ============================================================
# POST /api/evaluation/confirm-semester  (ZENKI)
# ============================================================

@router.post("/confirm-semester")
def confirm_semester(course: str, grade: int, class_name: str, subject: str, semester: int):

    if semester != 1:
        return {"error": "only semester=1 supported for snapshot"}

    class_id = f"{course}-{grade}-{class_name}"
    today = date.today().isoformat()
    sy = school_year(today)

    subjects = load_json("data/subjects.json")
    subj = next((s for s in subjects if s["id"] == subject), None)

    current = get_class_evaluation(
        course=course,
        grade=grade,
        class_name=class_name,
        subject=subject
    )


    snapshots = {}
    eval_dir = "evaluation"

    if os.path.exists(eval_dir):
        for fname in os.listdir(eval_dir):
            if not fname.endswith(".json"):
                continue

            full_path = os.path.join(eval_dir, fname)
            data = load_json(full_path)

            if (
                data.get("_subject_id") == subject
                and fname.startswith(f"{class_id}-{subj['subject_group']}-{sy}")
            ):
                snapshots = {
                    sid: {
                        "zenki_snapshot": snap.get("zenki_snapshot"),
                        "manual_final_grade": snap.get("manual_final_grade")
                    }
                    for sid, snap in data.items()
                    if isinstance(snap, dict)
                }
                break

    snapshots["_subject_id"] = subject

    for sid, data in current.items():
        if sid not in snapshots:
            snapshots[sid] = {}
        snapshots[sid]["zenki_snapshot"] = {
            "five_scale": data["continuous"]["five_scale"],
            "kanten": data["continuous"]["kanten"],
            "exam": data["continuous"]["exam"],
            "tasks": data["continuous"]["tasks"],
            "autonomy": data["auto1"]                                 # ← AQUI ESTÁ O ERRO
        }


    save_json(f"evaluation/{class_id}-{subj['subject_group']}-{sy}.json", snapshots)

    return {"status": "zenki snapshot saved"}


# ============================================================
# POST /api/evaluation/finalize  (KOKI)
# ============================================================

@router.post("/finalize")
def finalize_evaluation(course: str, grade: int, class_name: str, subject: str):

    class_id = f"{course}-{grade}-{class_name}"
    today = date.today().isoformat()
    sy = school_year(today)

    current = get_class_evaluation(course, grade, class_name, subject)

    subjects = load_json("data/subjects.json")
    subj = next((s for s in subjects if s["id"] == subject), None)

    snapshots = {}
    eval_dir = "evaluation"

    if os.path.exists(eval_dir):
        for fname in os.listdir(eval_dir):
            if not fname.endswith(".json"):
                continue

            full_path = os.path.join(eval_dir, fname)
            data = load_json(full_path)

            if (
                data.get("_subject_id") == subject
                and fname.startswith(f"{class_id}-{subj['subject_group']}-{sy}")
            ):
                snapshots = {
                    sid: {
                        "zenki_snapshot": snap.get("zenki_snapshot"),
                        "manual_final_grade": snap.get("manual_final_grade")
                    }
                    for sid, snap in data.items()
                    if isinstance(snap, dict)
                }
                break

    snapshots["_subject_id"] = subject

    # ❌ NÃO SALVA MAIS FINAL SNAPSHOT
    # (mantém apenas manual_final_grade se existir)

    save_json(f"evaluation/{class_id}-{subj['subject_group']}-{sy}.json", snapshots)

    return {"status": "final snapshot ignored (disabled)"} 


# ============================================================
# GET /api/evaluation/class/all  (KOKI)
# ============================================================

@router.get("/class/all")
def get_all_class_evaluations(course: str, grade: int, class_name: str):

    today = date.today().isoformat()
    sy = school_year(today)

    subjects = load_json("data/subjects.json")

    subject_list = [
        s for s in subjects
        if s.get("course") == course and str(s.get("grade")) == str(grade)
    ]

    result = {}

    for subj in subject_list:
        subject_id = subj["id"]

        ev = get_class_evaluation(
            course=course,
            grade=grade,
            class_name=class_name,
            subject=subject_id
        )

        result[subject_id] = ev

    return result


# ============================================================
# GET /api/evaluation/hyoka
# ============================================================

@router.get("/hyoka")
def get_hyoka(grade: int, class_name: str):
    today = date.today().isoformat()
    sy = f"{school_year(today)}年"

    filename = f"{sy}_{grade}_{class_name}.json"
    filepath = os.path.join("data", "hyoka", filename)

    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
