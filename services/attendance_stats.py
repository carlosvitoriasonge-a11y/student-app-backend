from datetime import datetime

def empty_counts():
    return {
        "attendance": 0,
        "absence": 0,
        "late": 0,
        "early": 0,
        "stopped": 0,
        "mourn": 0,
        "justified": 0,
        "school_days": 0,
        "required_attendance_days": 0,
        "attendance_rate": None,
    }

def accumulate(counts, status):
    s = str(status or "").strip()

    if s == "出席":
        counts["attendance"] += 1

    elif s == "欠席":
        counts["absence"] += 1

    elif s == "遅刻":
        counts["late"] += 1
        counts["attendance"] += 1

    elif s == "早退":
        counts["early"] += 1
        counts["attendance"] += 1

    elif s == "遅刻と早退":
        counts["late"] += 1
        counts["early"] += 1
        counts["attendance"] += 1

    elif s == "出席停止":
        counts["stopped"] += 1

    elif s == "忌引き":
        counts["mourn"] += 1

    elif s == "公欠":
        counts["justified"] += 1

def term_of(date_obj):
    m = date_obj.month
    if 4 <= m <= 9:
        return "first_term"
    if m >= 10 or m <= 3:
        return "second_term"
    return None

def compute_attendance_stats(attendance_json):
    # Estatística da turma
    class_stats = {
        "first_term": empty_counts(),
        "second_term": empty_counts(),
        "total": empty_counts(),
    }

    # Estatística por aluno
    student_stats = {}

    # Dias letivos por termo
    term_days = {
        "first_term": set(),
        "second_term": set(),
    }

    for date_str, day_data in attendance_json.items():
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            continue

        term = term_of(d)
        if term is None:
            continue

        students = (day_data or {}).get("students", {})
        if not isinstance(students, dict):
            continue

        term_days[term].add(date_str)

        for sid, status in students.items():
            # Inicializa stats por aluno se não existir
            if sid not in student_stats:
                student_stats[sid] = {
                    "first_term": empty_counts(),
                    "second_term": empty_counts(),
                    "total": empty_counts(),
                }

            # Acumula na turma
            accumulate(class_stats[term], status)
            accumulate(class_stats["total"], status)

            # Acumula no aluno
            accumulate(student_stats[sid][term], status)
            accumulate(student_stats[sid]["total"], status)

    # Finaliza turma
    def finalize(counts, days):
        counts["school_days"] = len(days)
        counts["required_attendance_days"] = (
            counts["school_days"]
            - counts["mourn"]
            - counts["stopped"]
            - counts["justified"]
        )
        if counts["required_attendance_days"] > 0:
            counts["attendance_rate"] = round(
                counts["attendance"] / counts["required_attendance_days"] * 100, 1
            )

    finalize(class_stats["first_term"], term_days["first_term"])
    finalize(class_stats["second_term"], term_days["second_term"])
    finalize(class_stats["total"], term_days["first_term"] | term_days["second_term"])

    # Finaliza cada aluno
    for sid, stats in student_stats.items():
        finalize(stats["first_term"], term_days["first_term"])
        finalize(stats["second_term"], term_days["second_term"])
        finalize(stats["total"], term_days["first_term"] | term_days["second_term"])

    return {
        "class_stats": class_stats,
        "students": student_stats
    }
