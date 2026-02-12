from pydantic import BaseModel
from typing import List

class Homeroom(BaseModel):
    grade: int
    class_name: str
    course: str  # 全, 水, 集

class TeacherBase(BaseModel):
    name: str
    subjects: List[str] = []
    homerooms: List[Homeroom] = []

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(TeacherBase):
    pass

class TeacherOut(TeacherBase):
    id: int

