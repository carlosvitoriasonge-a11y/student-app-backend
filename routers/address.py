import requests
from fastapi import APIRouter

router = APIRouter()

@router.get("/lookup")
def lookup(zipcode: str):
    url = f"https://api.zipaddress.net/?zipcode={zipcode}"
    res = requests.get(url)
    return res.json()
