from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json



# ... resto dos imports

# -------------------------------
# students.json のパスを main.py と同じ場所に固定
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.json")
os.makedirs(DATA_DIR, exist_ok=True)


def load_students():
    if not os.path.exists(STUDENTS_FILE):
        return []
    with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_students(students):
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)


# -------------------------------
# ルーターのインポート
# -------------------------------
from routers.students import router as students_router
from routers.classes import router as classes_router
from routers.promote import router as promote_router
from routers.restore import router as restore_router
from routers.demote import router as demote_router
from routers.search import router as search_router
from routers.course_change import router as course_change_router  # ← ★ 追加

app = FastAPI(title="Student Management API")

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
# 写真フォルダの設定
# -------------------------------
DEFAULT_PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
PHOTOS_DIR = os.environ.get("PHOTOS_DIR", DEFAULT_PHOTOS_DIR)
os.makedirs(PHOTOS_DIR, exist_ok=True)

# 静的ファイルとして公開
app.mount("/photos", StaticFiles(directory=PHOTOS_DIR), name="photos")

# -------------------------------
# 写真アップロード API
# -------------------------------
@app.post("/upload_photo/{student_id}")
async def upload_photo(student_id: str, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    filename = f"{student_id}{ext}"
    filepath = os.path.join(PHOTOS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    students = load_students()
    for s in students:
        if s["id"] == student_id:
            s["photo"] = filename
            save_students(students)
            return {"filename": filename}

    raise HTTPException(status_code=404, detail="Student not found")


# -------------------------------
# ルーター登録
# -------------------------------
app.include_router(students_router, prefix="/api/students", tags=["Students"])
app.include_router(search_router, prefix="/api/students", tags=["Search"])
app.include_router(classes_router, prefix="/api/classes", tags=["Classes"])
app.include_router(promote_router, prefix="/api/students", tags=["Promote"])
app.include_router(demote_router, prefix="/api/students", tags=["Demote"])
app.include_router(restore_router, prefix="/api/students/restore", tags=["Restore"])
app.include_router(course_change_router, prefix="/api/students", tags=["CourseChange"])  # ← ★ 追加

# -------------------------------
# 動作確認用
# -------------------------------
@app.get("/")
def root():
    return {"message": "Student Management API is running"}
