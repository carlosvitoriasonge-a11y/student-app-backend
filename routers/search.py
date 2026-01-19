print("### SEARCH ROUTER LOADED ###")

from fastapi import APIRouter
from utils.data import load_data

router = APIRouter()

def to_half_width(s: str) -> str:
    if not s:
        return ""
    table = str.maketrans({
        "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
        "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
        "－": "-", "ー": "-", "―": "-", "−": "-"
    })
    return s.translate(table)

def norm(s: str | None) -> str:
    if not s:
        return ""
    s = to_half_width(s)
    return s.replace("-", "").replace(" ", "").lower()

@router.get("/search")
def search_students(keyword: str):
    print("### SEARCH CALLED:", keyword)

    data = load_data()

    keyword_norm = norm(keyword)
    keyword_lower = keyword.lower()

    results = []
    for s in data:
        if keyword_lower in s.get("name", "").lower():
            results.append(s)
            continue
        if keyword_lower in s.get("kana", "").lower():
            results.append(s)
            continue
        if keyword_lower in s.get("id", "").lower():
            results.append(s)
            continue
        if keyword_norm in norm(s.get("phone", "")):
            results.append(s)
            continue
        if keyword_norm in norm(s.get("emergency1", "")):
            results.append(s)
            continue
        if keyword_norm in norm(s.get("emergency2", "")):
            results.append(s)
            continue

    return results
