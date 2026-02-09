from pydantic import BaseModel

class SeatingPreference(BaseModel):
    course: str
    grade: int
    class_name: str
    preferred_layout: str
