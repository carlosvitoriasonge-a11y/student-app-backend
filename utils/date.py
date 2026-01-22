from datetime import datetime

def school_year(date_str: str) -> str:
    y, m, _ = map(int, date_str.split("-"))
    return str(y if m >= 4 else y - 1)

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
