from fastapi import APIRouter
from models.seating import SeatingPreference
from utils.seating_data import load_seating_prefs, save_seating_prefs

router = APIRouter()

PREF_FILE = "data/seating_preferences.json"


@router.get("/preference") 
async def get_preference(course: str, grade: int, class_name: str): 
    prefs = load_seating_prefs() 
    key = f"{course}-{grade}-{class_name}" 
    return {"preferred_layout": prefs.get(key)} 


@router.post("/preference") 
async def save_preference(pref: SeatingPreference): 
    prefs = load_seating_prefs() 
    key = f"{pref.course}-{pref.grade}-{pref.class_name}" 
    prefs[key] = pref.preferred_layout 
    save_seating_prefs(prefs) 
    