from pydantic import BaseModel

class ClassAssignRequest(BaseModel):
    id: str
    class_: str
