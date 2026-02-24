# utils/evaluation.py

def abc_to_num(letter: str) -> int:
    return {"C": 1, "B": 2, "A": 3}[letter]


# -----------------------------
# 1) CONVERSÃO DE PORCENTAGEM → A/B/C
# -----------------------------

def grade_exam(percent: float) -> str:
    """知・技 (exames) — máximo 40%"""
    if percent < 14.4:
        return "C"
    elif percent < 34.4:
        return "B"
    else:
        return "A"


def grade_tasks(percent: float) -> str:
    """思・判・表 (trabalhos) — máximo 20%"""
    if percent < 7.2:
        return "C"
    elif percent < 17.2:
        return "B"
    else:
        return "A"


def grade_autonomy(percent: float) -> str:
    """主体性 (attendance + comportamento) — máximo 40%"""
    if percent < 14.4:
        return "C"
    elif percent < 34.4:
        return "B"
    else:
        return "A"


# -----------------------------
# 2) CÁLCULO DO 5段階評価
# -----------------------------

def final_numeric_grade(exam_letter: str, task_letter: str, autonomy_letter: str) -> int:
    exam = abc_to_num(exam_letter)
    task = abc_to_num(task_letter)
    autonomy = abc_to_num(autonomy_letter)

    result = exam * 0.4 + task * 0.2 + autonomy * 0.4

    if result <= 1.5:
        return 1
    elif result <= 1.9:
        return 2
    elif result <= 2.3:
        return 3
    elif result <= 2.7:
        return 4
    else:
        return 5


# -----------------------------
# 3) FUNÇÃO PRINCIPAL
# -----------------------------

def evaluate_student(exam_percent: float, task_percent: float, autonomy_percent: float):
    """
    exam_percent: 0–40
    task_percent: 0–20
    autonomy_percent: 0–40

    Retorna:
    - 5段階評価 (1~5)
    - 観点別評価 (AAA, ABC, etc.)
    """

    # 1) Converter para A/B/C
    exam_letter = grade_exam(exam_percent)
    task_letter = grade_tasks(task_percent)
    autonomy_letter = grade_autonomy(autonomy_percent)

    # 2) Calcular nota final 1~5
    five_scale = final_numeric_grade(exam_letter, task_letter, autonomy_letter)

    # 3)観点別評価 (na ordem PROVA → TRABALHOS → 主体性)
    kanten = exam_letter + task_letter + autonomy_letter

    return {
        "five_scale": five_scale,   # 5段階評価
        "kanten": kanten,           # AAA / ABC / etc.
        "exam": exam_letter,
        "tasks": task_letter,
        "autonomy": autonomy_letter
    }


def compute_autonomy(present: int, total: int, negative_events: int):
    """
    present: número de presenças (出席 + 遅刻 + 早退)
    total: total de aulas
    negative_events: soma de (遅刻 + 忘れ物 + 怠学)

    Regra A:
    - 欠席 derruba comportamento → comportamento = 0 quando present == 0
    """

    if total == 0:
        return 0

    # 1) Attendance (25%)
    attendance_percent = (present / total) * 25

    # 2) Behavior (15%)
    if present == 0:
        # aluno faltou → comportamento = 0
        behavior_percent = 0
    else:
        behavior_score = max(total - negative_events, 0)
        behavior_percent = (behavior_score / total) * 15

    # 3) Total autonomy (0~40)
    return attendance_percent + behavior_percent
