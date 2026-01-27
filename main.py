from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
import io

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import psutil

# -------------------------------
# JWT AUTH
# -------------------------------
from auth_jwt import verify_token, create_access_token, create_refresh_token
import jwt
from auth_jwt import SECRET_KEY, ALGORITHM

# -------------------------------
# students.json のパスを main.py と同じ場所に固定
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

from utils.data_manager import load_json, save_json

def load_students():
    return load_json("students.json")

def save_students(students):
    save_json("students.json", students)

APP_SECRET = os.environ.get("APP_SECRET", "default_password")

async def verify_token_header(x_app_key: str = Header(None)):
    return

# -------------------------------
# ルーターのインポート
# -------------------------------
from routers.students import router as students_router
from routers.classes import router as classes_router
from routers.promote import router as promote_router
from routers.restore import router as restore_router
from routers.demote import router as demote_router
from routers.search import router as search_router
from routers.course_change import router as course_change_router
from routers.joseki import router as joseki_router
from routers.tengaku import router as tengaku_router
from routers.taigaku import router as taigaku_router
from routers.exit_list import router as exit_list_router

app = FastAPI(
    title="Student Management API",
    redirect_slashes=True
)

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# LOGIN
# -------------------------------
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME") 
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")

@app.post("/auth/login")
def login(data: LoginRequest):
    if data.username != LOGIN_USERNAME or data.password != LOGIN_PASSWORD: 
        raise HTTPException(status_code=401, detail="パスワードが違います")

    access = create_access_token({"sub": data.username})
    refresh = create_refresh_token({"sub": data.username})

    return {"access_token": access, "refresh_token": refresh}

@app.post("/auth/refresh")
def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")

        new_access = create_access_token({"sub": payload["sub"]})
        return {"access_token": new_access}

    except:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

# -------------------------------
# 写真フォルダの設定
# -------------------------------
DEFAULT_PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
PHOTOS_DIR = os.environ.get("PHOTOS_DIR", DEFAULT_PHOTOS_DIR)
os.makedirs(PHOTOS_DIR, exist_ok=True)

app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")

# -------------------------------
# 写真アップロード API（圧縮 + バリデーション + 古い写真削除）
# -------------------------------
@app.post("/upload_photo/{student_id}", dependencies=[Depends(verify_token)])
async def upload_photo(student_id: str, file: UploadFile = File(...)):
    allowed_ext = [".jpg", ".jpeg", ".png"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail="許可されている画像形式は .jpg .jpeg .png のみです。"
        )

    MAX_SIZE = 5 * 1024 * 1024
    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="ファイルサイズが大きすぎます（最大 5MB まで）。"
        )

    try:
        img = Image.open(io.BytesIO(file_bytes))
    except:
        raise HTTPException(status_code=400, detail="画像ファイルが不正です。")

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    MAX_DIM = 1600
    if max(img.size) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM))

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=80)
    compressed_bytes = output.getvalue()

    filename = f"{student_id}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)

    students = load_students()

    student = next((s for s in students if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    old_photo = student.get("photo")
    if old_photo:
        old_path = os.path.join(PHOTOS_DIR, old_photo)
        if os.path.exists(old_path):
            os.remove(old_path)

    with open(filepath, "wb") as f:
        f.write(compressed_bytes)

    student["photo"] = filename
    save_students(students)

    return {"filename": filename}

# -------------------------------
# ルーター登録 (todas protegidas)
# -------------------------------
app.include_router(exit_list_router, prefix="/api/students", tags=["ExitList"], dependencies=[Depends(verify_token)])
app.include_router(students_router, prefix="/api/students", tags=["Students"], dependencies=[Depends(verify_token)])
app.include_router(search_router, prefix="/api/students", tags=["Search"], dependencies=[Depends(verify_token)])
app.include_router(classes_router, prefix="/api/classes", tags=["Classes"], dependencies=[Depends(verify_token)])
app.include_router(promote_router, prefix="/api/students", tags=["Promote"], dependencies=[Depends(verify_token)])
app.include_router(demote_router, prefix="/api/students", tags=["Demote"], dependencies=[Depends(verify_token)])
app.include_router(restore_router, prefix="/api/students/restore", tags=["Restore"], dependencies=[Depends(verify_token)])
app.include_router(course_change_router, prefix="/api/students", tags=["CourseChange"], dependencies=[Depends(verify_token)])
app.include_router(joseki_router, prefix="/api/students", tags=["Joseki"], dependencies=[Depends(verify_token)])
app.include_router(tengaku_router, prefix="/api/students", tags=["Tengaku"], dependencies=[Depends(verify_token)])
app.include_router(taigaku_router, prefix="/api/students", tags=["Taigaku"], dependencies=[Depends(verify_token)])

@app.get("/api/system/status", dependencies=[Depends(verify_token)])
def system_status():
    disk = shutil.disk_usage("/")
    mem = psutil.virtual_memory()

    return {
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "mem_total": mem.total,
        "mem_used": mem.used,
        "mem_free": mem.available,
    }

# -------------------------------
# 動作確認用
# -------------------------------
@app.get("/")
def root():
    return {"message": "Student Management API is running"}