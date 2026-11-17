from fastapi import APIRouter
import json
import os

router = APIRouter()

ARQUIVO = "area_sensivel.json"

@router.get("/ler")
def ler():
    # Se o arquivo não existir, cria um blob vazio
    if not os.path.exists(ARQUIVO):
        blob_vazio = {
            "nonce": "",
            "ciphertext": ""
        }
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(blob_vazio, f, ensure_ascii=False, indent=2)
        return blob_vazio

    # Se existir, devolve o blob criptografado
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/salvar")
def salvar(blob: dict):
    # Sempre salva o blob criptografado
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}
