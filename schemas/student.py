from pydantic import BaseModel
from typing import Optional, Literal

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# -----------------------------
# 1) Item individual de report
# -----------------------------
class ReportItem(BaseModel):
    id: str
    date: str
    status: str = "submitted"   # submitted | accepted | rejected | pending
    comment: Optional[str] = ""


# ---------------------------------------
# 2) Status da matéria dentro de um ano
# ---------------------------------------
class ReportSubjectStatus(BaseModel):
    required: int
    submitted: int = 0
    items: List[ReportItem] = Field(default_factory=list)


# ---------------------------------------
# 3) Estrutura por ano letivo
# ---------------------------------------
class YearReportStatus(BaseModel):
    subjects: Dict[str, ReportSubjectStatus] = Field(default_factory=dict)


class StudentBase(BaseModel):
    name: str
    kana: str
    gender: Literal["男", "女"] | None = None
    course: Literal["全", "水", "集"]
    grade: Optional[str] = None

    birth_date: Optional[str] = None
    admission_date: Optional[str] = None
    junior_high: Optional[str] = None
    junior_high_grad_date: Optional[str] = None
    postal_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None
    phone_label: Optional[str] = None
    guardian1: Optional[str] = None
    guardian1_kana: Optional[str] = None
    guardian_address: Optional[str] = None
    emergency1: Optional[str] = None
    emergency2: Optional[str] = None
    contact_time: Optional[str] = None
    note1: Optional[str] = None
    note2: Optional[str] = None
    commute: Optional[str] = None
    emergency1label: Optional[str] = None
    emergency2label: Optional[str] = None
    attend_no: Optional[str] = None

    class_name: Optional[str] = None
    photo: str | None = None
    transfer_advanced_date: Optional[str] = None
    transfer_date: Optional[str] = None
    previous_school: Optional[str] = None
    course_type: Optional[str] = None
    previous_school_address: Optional[str] = None
    status: Optional[str] = None
    suspension_history: Optional[list] = None

    # ⭐ NOVO CAMPO — reports organizados por ano → matéria
    reports: Dict[str, YearReportStatus] = Field(default_factory=dict)






class StudentCreate(BaseModel):
    # 基本項目
    name: str
    kana: str
    gender: Literal["男", "女"] | None = None
    year: str
    course: Literal["全", "水", "集"]
    grade: Optional[str] = None

    # 追加項目（Svelte と完全一致）
    birth_date: Optional[str] = None
    admission_date: Optional[str] = None
    junior_high: Optional[str] = None
    junior_high_grad_date: Optional[str] = None
    postal_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None
    phone_label: Optional[str] = None
    father: str | None = None 
    mother: str | None = None
    guardian1: Optional[str] = None
    guardian1_kana: Optional[str] = None
    guardian_address: Optional[str] = None
    emergency1: Optional[str] = None
    emergency2: Optional[str] = None
    emergency1label: Optional[str] = None
    emergency2label: Optional[str] = None
    contact_time: Optional[str] = None
    note1: Optional[str] = None
    note2: Optional[str] = None
    commute: Optional[str] = None
    attend_no: Optional[str] = None
    photo: str | None = None
    transfer_advanced_date: Optional[str] = None
    transfer_date: Optional[str] = None
    previous_school: Optional[str] = None
    course_type: Optional[str] = None
    previous_school_address: Optional[str] = None





class StudentUpdate(BaseModel):
    name: Optional[str] = None
    kana: Optional[str] = None
    gender: Optional[Literal["男", "女"]] = None
    course: Optional[Literal["全", "水", "集"]] = None
    grade: Optional[str] = None

    birth_date: Optional[str] = None
    admission_date: Optional[str] = None
    junior_high: Optional[str] = None
    junior_high_grad_date: Optional[str] = None
    postal_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None
    phone_label: Optional[str] = None
    father: str | None = None 
    mother: str | None = None
    guardian1: Optional[str] = None
    guardian1_kana: Optional[str] = None
    guardian_address: Optional[str] = None
    emergency1: Optional[str] = None
    emergency2: Optional[str] = None
    contact_time: Optional[str] = None
    note1: Optional[str] = None
    note2: Optional[str] = None
    commute: Optional[str] = None
    emergency1label: Optional[str] = None
    emergency2label: Optional[str] = None
    attend_no: Optional[str] = None
    class_name: Optional[str] = None
    photo: str | None = None
    transfer_advanced_date: Optional[str] = None
    transfer_date: Optional[str] = None
    previous_school: Optional[str] = None
    course_type: Optional[str] = None
    previous_school_address: Optional[str] = None
    status: Optional[str] = None
    suspension_history: Optional[list] = None


class StudentOut(StudentBase):
    id:str


    name: Optional[str] = None
    kana: Optional[str] = None
    gender: Optional[Literal["男", "女"]] = None
    course: Optional[Literal["全", "水", "集"]] = None
    grade: Optional[str] = None

    birth_date: Optional[str] = None
    admission_date: Optional[str] = None
    junior_high: Optional[str] = None
    junior_high_grad_date: Optional[str] = None
    postal_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None
    phone_label: Optional[str] = None
    father: str | None = None 
    mother: str | None = None
    guardian1: Optional[str] = None
    guardian1_kana: Optional[str] = None
    guardian_address: Optional[str] = None
    emergency1: Optional[str] = None
    emergency2: Optional[str] = None
    contact_time: Optional[str] = None
    note1: Optional[str] = None
    note2: Optional[str] = None
    commute: Optional[str] = None
    emergency1label: Optional[str] = None
    emergency2label: Optional[str] = None
    attend_no: Optional[str] = None
    class_name: Optional[str] = None
    photo: str | None = None
    transfer_advanced_date: Optional[str] = None
    transfer_date: Optional[str] = None
    previous_school: Optional[str] = None
    course_type: Optional[str] = None
    previous_school_address: Optional[str] = None
    status: Optional[str] = None
    suspension_history: Optional[list] = None
