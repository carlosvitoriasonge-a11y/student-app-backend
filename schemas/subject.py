from pydantic import BaseModel, Field
from typing import List, Optional, Union

class SubjectBase(BaseModel):
    subject_group: Optional[str] = Field(
        None,
        description="教科（例：英語、国語、数学）。任意。未設定の場合は空のまま扱う。"
    )
    name: str = Field(..., description="科目名（例：コミュニケーション英語Ⅰ）")
    credits: int = Field(..., ge=0, description="単位数")
    required_attendance: int = Field(..., ge=0, description="認定に必要な最低出席日数")
    required_reports: int = Field(..., ge=0, description="必要なレポート数")
    type: str = Field(..., pattern="^(required|optional)$", description="必須科目 or 任意科目")
    grade: int = Field(..., ge=1, le=3, description="学年（1〜3）") # ← AQUI
    teacher_ids: List[Union[int, str]] = Field(default_factory=list, description="担当教員のIDリスト")
    course: str = Field( "全", description="コース（例：全・水・集）。未設定の場合は「全」。")


class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: str
    grade: Optional[int] = None
