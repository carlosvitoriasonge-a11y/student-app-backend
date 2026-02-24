# utils/attendance_reader.py

def extract_attendance_numbers(attendance_json: dict, student_id: str):
    """
    Lê o JSON cru salvo pelo attendance_sub.py e retorna:
    - total de aulas
    - presenças (出席, 遅刻, 怠学・居眠り, 忘れ物)
    - eventos negativos (遅刻, 怠学・居眠り, 忘れ物)

    未記録 é ignorado completamente.
    欠席 conta como ausência, mas NÃO é negativo.
    """

    total = 0
    present = 0
    negative = 0

    # ✔ Status confirmados por você
    PRESENT_STATUSES = {"出席", "遅刻", "怠学・居眠り", "忘れ物"}
    NEGATIVE_STATUSES = {"遅刻", "怠学・居眠り", "忘れ物"}

    for date, periods in attendance_json.items():
        for period, info in periods.items():

            total += 1  # cada período = 1 aula

            status = info["students"].get(student_id)

            # 未記録 → ignorar completamente
            if not status or status == "未記録":
                continue

            # presença
            if status in PRESENT_STATUSES:
                present += 1

            # comportamento negativo
            if status in NEGATIVE_STATUSES:
                negative += 1

            # 欠席 → não conta como presença, não é negativo
            # (não precisa fazer nada)

    return {
        "total": total,
        "present": present,
        "negative": negative
    }
