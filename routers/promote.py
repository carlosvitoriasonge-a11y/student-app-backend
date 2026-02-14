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

# -----------------------------
# FIND HOMEROOM TEACHER
# -----------------------------
def find_teacher(teachers, grade, class_name, course):
    for t in teachers:
        for h in t.get("homerooms", []):
            if (
                str(h["grade"]) == str(grade)
                and h["class_name"] == class_name
                and h["course"] == course
            ):
                return t["name"]
    return None


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
# PROMOTE ROUTE
# -----------------------------
@router.post("/promote")
def promote_students(payload: dict):
    grade = str(payload.get("grade"))
    promote_ids = payload.get("promote_ids", [])

    students = load_data()
    graduates = load_graduates()
    teachers = load_teachers()

    promoted = 0
    stayed = 0
    graduated = 0

    new_students = []

    # prefix map
    prefix_map = {
        "1": "1st_year",
        "2": "2nd_year",
        "3": "3rd_year"
    }

    for s in students:
        s_grade = str(s["grade"])

        # 学年違い → そのまま残す
        if s_grade != grade:
            new_students.append(s)
            continue

        # prefix for this student's current year
        prefix = prefix_map[grade]

        # find homeroom teacher
        teacher_name = find_teacher(
            teachers,
            s_grade,
            s.get("class_name", ""),
            s.get("course", "")
        )


        # -----------------------------
        # CHECK IF STUDENT WAS SUSPENDED THIS YEAR (休学)
        # -----------------------------
        this_year = datetime.now().year

        # Japanese school year: April 1 → March 31
        start_of_year = datetime(this_year - 1, 4, 1)
        end_of_year = datetime(this_year, 3, 31)

        was_suspended_this_year = False

        for entry in s.get("suspension_history", []):
            start = datetime.fromisoformat(entry["start"])
            end = datetime.fromisoformat(entry["end"]) if entry["end"] else datetime.max

            # If suspension overlaps the school year
            if start <= end_of_year and end >= start_of_year:
                was_suspended_this_year = True
                break

        if was_suspended_this_year:
            this_year = datetime.now().year
            nendo_num = this_year - 1
            nendo = f"{nendo_num}年度"

            s[f"{prefix}_nendo"] = nendo
            s[f"{prefix}_{nendo_num}_status"] = "休学"

            # salvar presença mesmo em 休学
            calculate_attendance_for_year(
                s,
                prefix,
                s.get("course", ""),
                s.get("grade", ""),
                s.get("class_name", ""),
                nendo_num
            )

            new_students.append(s)
            continue




        # -----------------------------
        # PROMOTED OR GRADUATED
        # -----------------------------
        if s["id"] in promote_ids:

            # ★ SAVE CLASS / NUMBER / TEACHER FOR THIS YEAR

            this_year = datetime.now().year 
            nendo = f"{this_year - 1}年度"

        
            s[f"{prefix}_class"] = s.get("class_name", "")
            s[f"{prefix}_attendance_no"] = s.get("attend_no", "")
            s[f"{prefix}_teacher"] = teacher_name or ""
            s[f"{prefix}_nendo"] = nendo


            # ⭐⭐⭐ COLE AQUI ⭐⭐⭐ 
            # # CALCULAR HISTÓRICO DE PRESENÇA 
            calculate_attendance_for_year( 
                s, 
                prefix, s.get("course", ""), 
                s.get("grade", ""), 
                s.get("class_name", ""), 
                this_year - 1 # nendo numérico 
            ) 
            # ⭐⭐⭐ FIM DA INSERÇÃO ⭐⭐⭐

            # ★ 3年生 → 卒業
            if grade == "3":
                s["graduated_year"] = f"{nendo}3月卒業"

                # 卒業生はクラス情報を消す
                s["class_name"] = ""
                s["attend_no"] = ""

                graduates.append(s)
                graduated += 1

            else:
                # ★ 昇級処理
                s["grade"] = str(int(grade) + 1)

                # 昇級後はクラスと出席番号をリセット
                s["class_name"] = ""
                s["attend_no"] = ""

                promoted += 1
                new_students.append(s)

        # -----------------------------
        # STAYED (REPEATED)
        # -----------------------------
        else:
            this_year = datetime.now().year
            nendo = this_year - 1

            # ★ SAVE REPEATED FLAG
            s[f"{prefix}_{nendo}"] = "repeated"


            calculate_attendance_for_year( 
                s, 
                prefix, 
                s.get("course", ""), 
                s.get("grade", ""), 
                s.get("class_name", ""), 
                nendo 
            )

            stayed += 1
            new_students.append(s)

    # 保存
    save_data(new_students)
    save_graduates(graduates)

    return {
        "promoted": promoted,
        "stayed": stayed,
        "graduated": graduated
    }
