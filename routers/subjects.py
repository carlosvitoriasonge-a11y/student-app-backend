from fastapi import APIRouter, HTTPException
from utils.data_manager import load_json, save_json
from schemas.subject import SubjectCreate, SubjectOut, SubjectBase
import uuid

router = APIRouter()


@router.post("/", response_model=SubjectOut)
def create_subject(subject: SubjectCreate):
    subjects = load_json("subjects.json")

   
    # Gerar código automaticamente (UUID curto ou completo)
   

    # Gerar ID único
    new_id = str(uuid.uuid4())

    # Converter o modelo Pydantic para dict
    new_subject = subject.dict()
    new_subject["id"] = new_id
    

    # Salvar
    subjects.append(new_subject)
    save_json("subjects.json", subjects)

    return new_subject


@router.get("/required", response_model=list[SubjectOut])
def get_required_subjects():
    subjects = load_json("subjects.json")
    return [s for s in subjects if s.get("type") == "required"]


@router.get("/optional", response_model=list[SubjectOut])
def get_optional_subjects():
    subjects = load_json("subjects.json")
    return [s for s in subjects if s.get("type") == "optional"]

@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject_by_id(subject_id: str):
    subjects = load_json("subjects.json")

    for s in subjects:
        if s.get("id") == subject_id:
            return s

    raise HTTPException(status_code=404, detail="Matéria não encontrada.")

@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: str, updated: SubjectBase):
    subjects = load_json("subjects.json")

    # Encontrar a matéria
    for index, s in enumerate(subjects):
        if s.get("id") == subject_id:

        
            # Atualizar mantendo o ID
            subjects[index].update(updated.dict())
            save_json("subjects.json", subjects)
            return subjects[index]

           

    raise HTTPException(status_code=404, detail="Matéria não encontrada.")

@router.delete("/{subject_id}")
def delete_subject(subject_id: str):
    subjects = load_json("subjects.json")

    for index, s in enumerate(subjects):
        if s.get("id") == subject_id:

            # Impedir exclusão de 必須科目
            if s.get("type") == "required":
                raise HTTPException(
                    status_code=403,
                    detail="必須科目 não podem ser deletadas."
                )

            # Deletar
            subjects.pop(index)
            save_json("subjects.json", subjects)

            return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="Matéria não encontrada.")




