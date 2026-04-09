from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter

router = APIRouter()


@router.get("/server_time")
def server_time():
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    return {"server_time": now.strftime("%Y-%m-%d %H:%M:%S")}
