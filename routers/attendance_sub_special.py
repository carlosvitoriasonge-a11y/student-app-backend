from fastapi import APIRouter
import os, json
from datetime import datetime
from routers.subjects import get_subjects

router = APIRouter()

# 🔥 matérias que SEMPRE contam o ano inteiro (ignoram regime especial)
ALWAYS_FULL_YEAR_SUBJECT_IDS = {
    "e9c6f011-bada-4559-bb29-702e731da6b7",  # 総合探究 2年
    "d7a30f13-d772-42c1-a12a-8f124c1d4b78"   # 総合探究 3年
}

def init_group():
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

def map_month_to_group(grade: str, month: int):
    if grade == "2":
        if month in [4, 5, 7, 8, 9]:
            return "senmon_zenki"
        if month == 6:
            return "koukou_zenki"
        if month in [11, 12, 1, 3]:
            return "senmon_koki"
        if month in [10, 2]:
            return "koukou_koki"

    if grade == "3":
        if month in [4, 5, 7, 8, 9]:
            return "senmon_zenki"
        if month == 6:
            return "koukou_zenki"
        if month in [11, 12, 2, 3]:
            return "senmon_koki"
        if month in [10, 1]:
            return "koukou_koki"

    return None

def is_special_target(sy: int, grade: str, course: str) -> bool:
    if course != "全":
        return False
    if sy == 2025 and grade in ["2", "3"]:
        return True
    if sy == 2026 and grade in ["2", "3"]:
        return True
    if sy == 2027 and grade == "3":
        return True
    return False

def attendance_sub_file_path(course, grade, class_name, sy):
    class_id = f"{course}-{grade}-{class_name}"
    return f"attendance_sub/{class_id}-{sy}.json"

@router.get("/special_sub")
def get_special_subject_attendance(course: str, grade: str, class_name: str, sy: int):

    special = is_special_target(sy, grade, course)

    path = attendance_sub_file_path(course, grade, class_name, sy)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    subjects = get_subjects(course=course, grade=grade)
    subject_required_map = {s["id"]: s["required_attendance"] for s in subjects}

    stats: dict = {}

    PRESENT_STATUSES = {"出席", "遅刻", "怠学・居眠り", "忘れ物"}

    for date_str, periods in data.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month

        for period, entry in periods.items():
            subject_id = entry.get("subject_id")
            if not subject_id:
                continue

            # 🔥 esta matéria ignora o regime especial?
            subject_is_full_year = subject_id in ALWAYS_FULL_YEAR_SUBJECT_IDS
            special_for_subject = special and not subject_is_full_year

            if special_for_subject:
                group = map_month_to_group(grade, month)
            else:
                group = "zenki" if month in [4, 5, 6, 7, 8, 9] else "koki"

            if not group:
                continue

            students_att = entry.get("students", {})

            for sid, status in students_att.items():

                if sid not in stats:
                    stats[sid] = {}

                if subject_id not in stats[sid]:
                    if special_for_subject:
                        stats[sid][subject_id] = {
                            "senmon_zenki": init_group(),
                            "koukou_zenki": init_group(),
                            "senmon_koki": init_group(),
                            "koukou_koki": init_group()
                        }
                    else:
                        stats[sid][subject_id] = {
                            "zenki": init_group(),
                            "koki": init_group()
                        }

                g = stats[sid][subject_id][group]

                g["school_days"] += 1

                if status in PRESENT_STATUSES:
                    g["attendance"] += 1
                elif status == "欠席":
                    g["absence"] += 1

    for sid in stats.keys():
        for subj_id in subject_required_map.keys():

            subject_is_full_year = subj_id in ALWAYS_FULL_YEAR_SUBJECT_IDS
            special_for_subject = special and not subject_is_full_year

            if subj_id not in stats[sid]:
                if special_for_subject:
                    stats[sid][subj_id] = {
                        "senmon_zenki": init_group(),
                        "koukou_zenki": init_group(),
                        "senmon_koki": init_group(),
                        "koukou_koki": init_group()
                    }
                else:
                    stats[sid][subj_id] = {
                        "zenki": init_group(),
                        "koki": init_group()
                    }

    for sid, subjects_data in stats.items():
        for subj_id, groups in subjects_data.items():

            required = subject_required_map.get(subj_id, 0)

            subject_is_full_year = subj_id in ALWAYS_FULL_YEAR_SUBJECT_IDS
            special_for_subject = special and not subject_is_full_year

            if special_for_subject:
                valid_att = (
                    groups["koukou_zenki"]["attendance"] +
                    groups["koukou_koki"]["attendance"]
                )
            else:
                valid_att = (
                    groups.get("zenki", {}).get("attendance", 0) +
                    groups.get("koki", {}).get("attendance", 0)
                )

            groups["valid_attendance"] = valid_att
            groups["required_attendance_days"] = required
            groups["attendance_rate"] = (
                round((valid_att / required) * 100, 1)
                if required > 0 else 0
            )

    return stats
