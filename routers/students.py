from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from schemas.student import StudentCreate, StudentUpdate, StudentOut
from utils.data import load_data, save_data
from utils.id_generator import generate_student_id

import os
import json
import csv
import io
import hashlib
import openpyxl
from io import BytesIO

# =========================================================
# COURSE MAPS (ADICIONADO)
# =========================================================

COURSE_REVERSE_MAP = {
    "全": "z",
    "水": "w",
    "集": "s",
}

COURSE_LABEL_MAP = {
    "z": "全",
    "w": "水",
    "s": "集",
}

def normalize_course(course):
    return COURSE_REVERSE_MAP.get(course, course)

# =========================================================

router = APIRouter()

def find_photo(student_id: str):
    photos_dir = "photos"
    for ext in ["jpg", "jpeg", "png"]:
        filename = f"{student_id}.{ext}"
        path = os.path.join(photos_dir, filename)
        if os.path.exists(path):
            return filename
    return None

# ---------------------------------------------------------
# コース別の名簿ダウンロード
# ---------------------------------------------------------
@router.get("/classlist/export")
def download_all_classes(grade: str, course: str | None = None):
    data = load_data()

    students = [
        s for s in data
        if s.get("grade") == grade and (
            course is None or normalize_course(s.get("course")) == course
        )
    ]

    if not students:
        raise HTTPException(status_code=404, detail="該当する生徒がいません")

    class_names = sorted({
        s.get("class_name")
        for s in students
        if s.get("class_name") not in [None, ""]
    })

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    for cname in class_names:
        sheet = wb.create_sheet(title=f"{grade}年_{course or '全コース'}_{cname}")
        sheet.append(["出席番号", "名前", "性別", "コース"])

        class_students = sorted(
            [s for s in students if s.get("class_name") == cname],
            key=lambda x: x.get("kana", "")
        )

        for s in class_students:
            sheet.append([
                s.get("attend_no") or "",
                s.get("name") or "",
                s.get("gender") or "",
                COURSE_LABEL_MAP.get(normalize_course(s.get("course")), s.get("course") or ""),
            ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    course_code_map = {
        "全": "z",
        "水": "w",
        "集": "s",
        None: "ALL"
    }
    course_code = course_code_map.get(course, "ALL")

    filename = f"{grade}_{course_code}_classes.xlsx"

    return Response(
        content=stream.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ---------------------------------------------------------
# 在校生一覧
# ---------------------------------------------------------
@router.get("/", response_model=list[StudentOut])
def list_students(grade: str | None = None):
    data = load_data()

    for s in data:
        if s.get("attend_no") is not None:
            s["attend_no"] = str(s["attend_no"])

    if grade:
        return [s for s in data if s["grade"] == grade]

    return data

# ---------------------------------------------------------
# フィルター
# ---------------------------------------------------------
@router.get("/filter")
def filter_students(
    grade: str,
    course: str | None = None,
    gender: str | None = None,
    class_name: str | None = None
):
    data = load_data()

    course_map = {
        "full": "全",
        "wednesday": "水",
        "intensive": "集",
        "s": "全",
        "w": "水",
        "z": "集",
    }

    gender_map = {
        "male": "男",
        "female": "女"
    }

    course_jp = course_map.get(course, course) if course else None
    gender_jp = gender_map.get(gender, gender) if gender else None

    results = []

    for s in data:
        if s.get("grade") != grade:
            continue
        if course_jp and normalize_course(s.get("course")) != normalize_course(course_jp):
            continue
        if gender_jp and s.get("gender") != gender_jp:
            continue
        if class_name and s.get("class_name") != class_name:
            continue
        results.append(s)

    return results

# ---------------------------------------------------------
# 在校生検索
# ---------------------------------------------------------
@router.get("/search")
def search_students(keyword: str):
    data = load_data()
    keyword = keyword.lower()

    return [
        s for s in data
        if keyword in s["name"].lower()
        or keyword in s["kana"].lower()
        or keyword in s["id"].lower()
    ]

# ---------------------------------------------------------
# CSV テンプレート
# ---------------------------------------------------------
@router.get("/template_csv")
def download_template_csv():
    template_path = os.path.join("data", "student_template.csv")

    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="テンプレートが存在しません")

    with open(template_path, "rb") as f:
        content = f.read()

    bom = b'\xef\xbb\xbf'
    return StreamingResponse(
        io.BytesIO(bom + content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_template.csv"}
    )

# ---------------------------------------------------------
# 卒業生一覧
# ---------------------------------------------------------
@router.get("/graduates")
def list_graduates(year: int | None = None):
    path = "data/graduates.json"
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        grads = json.load(f)

    if year is not None:
        grads = [g for g in grads if g.get("graduated_year") == year]

    grads.sort(key=lambda g: g.get("id", ""))
    return grads

# ---------------------------------------------------------
# 卒業生検索
# ---------------------------------------------------------
@router.get("/graduates/search")
def search_graduates(keyword: str):
    path = "data/graduates.json"
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        grads = json.load(f)

    keyword = keyword.lower()

    return [
        g for g in grads
        if keyword in g["name"].lower()
        or keyword in g["kana"].lower()
        or keyword in g["id"].lower()
    ]

# ---------------------------------------------------------
# 卒業生個別
# ---------------------------------------------------------
@router.get("/graduates/{student_id}")
def get_graduate(student_id: str):
    student_id = student_id.lower()

    path = "data/graduates.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No graduates data")

    with open(path, "r", encoding="utf-8") as f:
        grads = json.load(f)

    for s in grads:
        if s["id"].lower() == student_id:
            return s

    raise HTTPException(status_code=404, detail="Graduate not found")

# ---------------------------------------------------------
# CSV 一括登録
# ---------------------------------------------------------
@router.post("/import_csv")
async def import_students_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSVファイルをアップロードしてください")

    raw_bytes = await file.read()
    csv_hash = hashlib.sha256(raw_bytes).hexdigest()

    hash_path = "data/last_import_hash.txt"

    if os.path.exists(hash_path):
        with open(hash_path, "r", encoding="utf-8") as f:
            last_hash = f.read().strip()
        if last_hash == csv_hash:
            raise HTTPException(status_code=400, detail="同じCSVがすでにアップロードされています")

    # Lê CSV do Numbers corretamente (UTF-8 + BOM + quebras internas)
    text = raw_bytes.decode("utf-8-sig")
    stream = io.StringIO(text)

    reader = csv.DictReader(stream, delimiter=",", quotechar='"')


    students = load_data()
    new_students = []

    mapping = {
        "ID（新入生なら空欄）": "id",
        "名前": "name",
        "ふりがな": "kana",
        "性別": "gender",
        "生年月日(例：2007/01/10)": "birth_date",
        "入学年月日(例：2026/04/01)": "admission_date",
        "出身中学校": "junior_high",
        "中学校の卒業年月日": "junior_high_grad_date",
        "〒": "postal_code",
        "住所１（番地まで）": "address1",
        "住所２（アパート・マンション名など）": "address2",
        "電話番号": "phone",
        "電話ラベル（父、母、自宅）": "phone_label",
        "保護者名１": "guardian1",
        "保護者名１ふりがな": "guardian1_kana",
        "保護者住所": "guardian_address",
        "家庭（緊急）連絡先①": "emergency1",
        "ラベル①（例:父）": "emergency1label",
        "家庭（緊急）連絡先②": "emergency2",
        "ラベル②": "emergency2label",
        "つながりやすい時間帯": "contact_time",
        "備考①": "note1",
        "備考②": "note2",
        "通学方法": "commute"
    }

    for row in reader:
        converted = {}

        for k, v in row.items():
            if "コース" in k:
                converted["course"] = v.strip()
                continue
            if k in mapping:
                converted[mapping[k]] = v.strip()

        raw_course = converted.get("course", "").strip()

        if "全" in raw_course:
            course_code = "s"
            converted["course"] = "全"
        elif "水" in raw_course:
            course_code = "w"
            converted["course"] = "水"
        elif "集" in raw_course:
            course_code = "z"
            converted["course"] = "集"
        else:
            raise HTTPException(status_code=400, detail=f"コースが判別できません: {raw_course}")

        admission_date = converted.get("admission_date", "")
        year = admission_date[:4]

        raw_id = converted.get("id", "").strip().lower()

        if raw_id:
            converted["id"] = raw_id
        else:
            converted["id"] = generate_student_id(year, course_code)

        if not converted.get("grade"):
            converted["grade"] = "1"

        converted["class_name"] = converted.get("class_name", "")

        new_students.append(converted)

    students.extend(new_students)
    save_data(students)

    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(csv_hash)

    return {"added": len(new_students)}

# ---------------------------------------------------------
# 生徒登録（個別）
# ---------------------------------------------------------
@router.post("/", response_model=StudentOut)
def create_student(student: StudentCreate):
    data = load_data()
    new_id = generate_student_id(student.year, student.course)
    new_student = student.dict()
    new_student["id"] = new_id.lower()
    data.append(new_student)
    save_data(data)
    return new_student

# ---------------------------------------------------------
# 生徒編集
# ---------------------------------------------------------
@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: str, student: StudentUpdate):
    student_id = student_id.lower()

    data = load_data()
    for s in data:
        if s["id"].lower() == student_id:
            for k, v in student.dict().items():
                if v is not None:
                    s[k] = v
            save_data(data)

            photo = find_photo(s["id"])
            s["photo"] = photo

            return s

    raise HTTPException(status_code=404, detail="Student not found")

# ---------------------------------------------------------
# 生徒削除
# ---------------------------------------------------------
@router.delete("/{student_id}")
def delete_student(student_id: str):
    student_id = student_id.lower()

    data = load_data()
    new_data = [s for s in data if s["id"].lower() != student_id]

    if len(new_data) == len(data):
        raise HTTPException(status_code=404, detail="Student not found")

    save_data(new_data)
    return {"status": "deleted"}

# ---------------------------------------------------------
# 学年一覧
# ---------------------------------------------------------
@router.get("/grades")
def get_grades():
    data = load_data()
    grades = sorted({s.get("grade") for s in data if s.get("grade")})
    return grades

# ---------------------------------------------------------
# クラス一覧
# ---------------------------------------------------------
@router.get("/classes/{grade}")
def get_classes(grade: str):
    data = load_data()
    classes = sorted({
        s.get("class_name")
        for s in data
        if s.get("grade") == grade and s.get("class_name") not in [None, ""]
    })

    if not classes:
        return {"message": "クラス分けはまだされていません"}

    return classes

# ---------------------------------------------------------
# 生徒個別取得（動的ルート）
# ---------------------------------------------------------
@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: str):
    student_id = student_id.lower()

    data = load_data()
    for s in data:
        if s["id"].lower() == student_id:

            if s.get("attend_no") is not None:
                s["attend_no"] = str(s["attend_no"])

            photo = find_photo(s["id"])
            s["photo"] = photo

            return s

    raise HTTPException(status_code=404, detail="Student not found")
