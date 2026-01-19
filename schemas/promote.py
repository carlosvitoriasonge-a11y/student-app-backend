from pydantic import BaseModel

class PromoteRequest(BaseModel):
    ids: list[str]
