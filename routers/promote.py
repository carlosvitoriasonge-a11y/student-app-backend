from fastapi import APIRouter, HTTPException
from utils.data import load_data, save_data
import json, os
from datetime import datetime

router = APIRouter()

# -----------------------------
# FILE PATHS
# -----------------------------
GRAD_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "graduates.json")
)

TEACHERS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "teachers.json")
)

# -----------------------------
# LOAD / SAVE HELPERS
# -----------------------------
def load_graduates():
    if not os.path.exists(GRAD_FILE):
        return []
    with open(GRAD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_graduates(data):
    with open(GRAD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_teachers():
    if not os.path.exists(TEACHERS_FILE):
        return []
    with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def process_subject_attendance(class_id: str, nendo: int, student: dict):
    path = f"attendance_sub/{class_id}-{nendo}.json"
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {}

    for date, periods in data.items():
        for period, info in periods.items():
            subject_group = info["subject"]
            status = info["students"].get(student["id"])

            if not status:
                continue

            if subject_group not in stats:
                stats[subject_group] = {
                    "present": 0,
                    "late": 0,
                    "lazy": 0,
                    "forget": 0,
                    "absent": 0,
                    "total": 0
                }

            if status == "出席":
                stats[subject_group]["present"] += 1
                stats[subject_group]["total"] += 1

            elif status == "欠席":
                stats[subject_group]["absent"] += 1

            elif status == "遅刻":
                stats[subject_group]["present"] += 1
                stats[subject_group]["late"] += 1
                stats[subject_group]["total"] += 1

            elif status == "退学・居眠り":
                stats[subject_group]["present"] += 1
                stats[subject_group]["lazy"] += 1
                stats[subject_group]["total"] += 1

            elif status == "忘れ物":
                stats[subject_group]["present"] += 1
                stats[subject_group]["forget"] += 1
                stats[subject_group]["total"] += 1

    for subject_group, counters in stats.items():
        student[subject_group] = counters


# -----------------------------
# FIND HOMEROOM TEACHER
# -----------------------------
def find_teachers(teachers, grade, class_name, course):
    result = []
    for t in teachers:
        for h in t.get("homerooms", []):
            if (
                str(h["grade"]) == str(grade)
                and h["class_name"] == class_name
                and h["course"] == course
            ):
                result.append(t["name"])
    return result


# -----------------------------
# ATTENDANCE HELPERS
# -----------------------------
ATTENDANCE_MAP = {
    "出席": {"attendance": 1},
    "欠席": {"absence": 1},
    "遅刻": {"attendance": 1, "late": 1},
    "早退": {"attendance": 1, "early": 1},
    "忌引き": {"mourn": 1},
    "出席停止": {"stopped": 1},
    "公欠": {"justified": 1},
    "遅刻と早退": {"attendance": 1, "late": 1, "early": 1}
}

def get_attempt_suffix(student, prefix):
    attempts = 0
    for key in student.keys():
        if key.startswith(f"{prefix}_school_days"):
            attempts += 1
    return "" if attempts == 0 else f"({attempts + 1})"

def load_attendance_file(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_attendance_for_year(student, prefix, course, grade, class_name, nendo):
    class_id = f"{course}-{grade}-{class_name}"
    attendance_file = f"attendance/{class_id}-{nendo}.json"

    data = load_attendance_file(attendance_file)

    school_days = 0
    counters = {
        "attendance": 0,
        "absence": 0,
        "late": 0,
        "early": 0,
        "mourn": 0,
        "stopped": 0,
        "justified": 0
    }

    for date, entry in data.items():
        if "students" not in entry:
            continue

        school_days += 1

        status = entry["students"].get(student["id"])
        if not status:
            continue

        if status in ATTENDANCE_MAP:
            for k, v in ATTENDANCE_MAP[status].items():
                counters[k] += v

    required = school_days - counters["mourn"] - counters["stopped"] - counters["justified"]
    required = max(required, 0)

    rate = 0
    if required > 0:
        rate = round((counters["attendance"] / required) * 100, 1)

    suffix = get_attempt_suffix(student, prefix)

    student[f"{prefix}_school_days{suffix}"] = school_days
    student[f"{prefix}_required_attendance_days{suffix}"] = required
    student[f"{prefix}_attendance{suffix}"] = counters["attendance"]
    student[f"{prefix}_absence{suffix}"] = counters["absence"]
    student[f"{prefix}_late{suffix}"] = counters["late"]
    student[f"{prefix}_early{suffix}"] = counters["early"]
    student[f"{prefix}_mourn{suffix}"] = counters["mourn"]
    student[f"{prefix}_stopped{suffix}"] = counters["stopped"]
    student[f"{prefix}_justified{suffix}"] = counters["justified"]
    student[f"{prefix}_attendance_rate{suffix}"] = rate


# -----------------------------
# PROMOTE ROUTE (REWRITTEN)
# -----------------------------
@router.post("/promote")
def promote_students(payload: dict):
    grade = str(payload.get("grade"))

    # normalize promote_ids
    promote_ids = [str(pid).strip() for pid in payload.get("promote_ids", [])]

    students = load_data()
    graduates = load_graduates()
    teachers = load_teachers()

    promoted = 0
    stayed = 0
    graduated = 0

    new_students = []

    prefix_map = {
        "1": "1st_year",
        "2": "2nd_year",
        "3": "3rd_year"
    }

    for s in students:
        s_grade = str(s["grade"])
        sid = str(s["id"]).strip()

        if s_grade != grade:
            new_students.append(s)
            continue

        prefix = prefix_map[grade]

        teacher_names = find_teachers(
            teachers,
            s_grade,
            s.get("class_name", ""),
            s.get("course", "")
        )

        # -----------------------------
        # STATUS DECIDES PROMOTION
        # -----------------------------
        student_status = s.get("status", "在籍")

        if student_status in ["休学", "退学"]:
            this_year = datetime.now().year
            nendo_num = this_year - 1

            s[f"{prefix}_nendo"] = f"{nendo_num}年度"
            s[f"{prefix}_{nendo_num}_status"] = student_status

            calculate_attendance_for_year(
                s,
                prefix,
                s.get("course", ""),
                s.get("grade", ""),
                s.get("class_name", ""),
                nendo_num
            )

            process_subject_attendance(
                f"{s.get('course','')}-{s.get('grade','')}-{s.get('class_name','')}",
                nendo_num,
                s
            )

            stayed += 1
            new_students.append(s)
            continue

        # -----------------------------
        # PROMOTED OR GRADUATED
        # -----------------------------
        if sid in promote_ids:

            this_year = datetime.now().year
            nendo = f"{this_year - 1}年度"

            s[f"{prefix}_class"] = s.get("class_name", "")
            s[f"{prefix}_attendance_no"] = s.get("attend_no", "")
            s[f"{prefix}_teachers"] = teacher_names or ""
            s[f"{prefix}_nendo"] = nendo

            calculate_attendance_for_year(
                s,
                prefix,
                s.get("course", ""),
                s.get("grade", ""),
                s.get("class_name", ""),
                this_year - 1
            )

            process_subject_attendance(
                f"{s.get('course','')}-{s.get('grade','')}-{s.get('class_name','')}",
                this_year - 1,
                s
            )

            if grade == "3":
                s["graduated_year"] = f"{nendo}3月卒業"
                s["class_name"] = ""
                s["attend_no"] = ""
                graduates.append(s)
                graduated += 1

            else:
                s["grade"] = str(int(grade) + 1)
                s["class_name"] = ""
                s["attend_no"] = ""
                promoted += 1
                new_students.append(s)

        else:
            this_year = datetime.now().year
            nendo = this_year - 1

            s[f"{prefix}_{nendo}"] = "repeated"

            calculate_attendance_for_year(
                s,
                prefix,
                s.get("course", ""),
                s.get("grade", ""),
                s.get("class_name", ""),
                nendo
            )

            process_subject_attendance(
                f"{s.get('course','')}-{s.get('grade','')}-{s.get('class_name','')}",
                nendo,
                s
            )

            stayed += 1
            new_students.append(s)

    save_data(new_students)
    save_graduates(graduates)

    # -----------------------------
    # STATS GENERATION (unchanged)
    # -----------------------------
    from routers.attendance_stats_special import get_special_attendance_stats

    this_year = datetime.now().year
    nendo_num = this_year - 1
    nendo = f"{nendo_num}"

    ALL_COURSES = ["全", "水", "集"]

    os.makedirs("data/attendance_stats", exist_ok=True)

    for course in ALL_COURSES:
        class_map = {}
        for s in students:
            if s.get("course") != course:
                continue
            g = str(s.get("grade"))
            c = s.get("class_name", "")
            if c:
                class_id = f"{course}-{g}-{c}"
                class_map.setdefault(class_id, {"course": course, "grade": g, "class_name": c})

        final_stats = {}

        for class_id, info in class_map.items():
            g = info["grade"]
            c = info["class_name"]

            stats = get_special_attendance_stats(
                course=course,
                grade=g,
                class_name=c,
                sy=nendo_num
            )

            if isinstance(stats, dict) and "error" in stats:
                continue

            final_stats[class_id] = stats

        out_path = f"data/attendance_stats/{nendo}_total_attendance_{course}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_stats, f, ensure_ascii=False, indent=2)

        def init_term():
            return {
                "school_days": 0,
                "required_attendance_days": 0,
                "attendance": 0,
                "absence": 0,
                "late": 0,
                "early": 0,
                "mourn": 0,
                "stopped": 0,
                "justified": 0,
                "attendance_rate": 0
            }

        def add_status(term, status):
            if status in ATTENDANCE_MAP:
                for k, v in ATTENDANCE_MAP[status].items():
                    term[k] += v

        def finalize_term(term):
            required = term["school_days"] - term["mourn"] - term["stopped"] - term["justified"]
            required = max(required, 0)
            term["required_attendance_days"] = required

            if required > 0:
                term["attendance_rate"] = round((term["attendance"] / required) * 100, 1)
            else:
                term["attendance_rate"] = 0

        term_stats = {}

        for class_id, info in class_map.items():
            g = info["grade"]
            c = info["class_name"]

            attendance_path = f"attendance/{course}-{g}-{c}-{nendo_num}.json"
            if not os.path.exists(attendance_path):
                continue

            with open(attendance_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            class_result = {}

            for s in students:
                if s.get("course") == course and str(s.get("grade")) == g:
                    sid = s["id"]
                    class_result[sid] = {
                        "first_term": init_term(),
                        "second_term": init_term(),
                        "total": init_term()
                    }

            for date_str, entry in data.items():
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month = dt.month

                period = "first_term" if month in [4, 5, 6, 7, 8, 9] else "second_term"

                for sid, status in entry.get("students", {}).items():
                    if sid not in class_result:
                        continue

                    class_result[sid][period]["school_days"] += 1
                    add_status(class_result[sid][period], status)

                    class_result[sid]["total"]["school_days"] += 1
                    add_status(class_result[sid]["total"], status)

            for sid in class_result:
                finalize_term(class_result[sid]["first_term"])
                finalize_term(class_result[sid]["second_term"])
                finalize_term(class_result[sid]["total"])

            term_stats[class_id] = class_result

        out_path2 = f"data/attendance_stats/{nendo}_term_attendance_{course}.json"
        with open(out_path2, "w", encoding="utf-8") as f:
            json.dump(term_stats, f, ensure_ascii=False, indent=2)

    return {
        "promoted": promoted,
        "stayed": stayed,
        "graduated": graduated
    }
