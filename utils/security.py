import os
from fastapi import HTTPException

def check_password(password: str):
    correct_password = os.environ.get("ADMIN_PASSWORD")

    if correct_password is None:
        raise HTTPException(
            status_code=500,
            detail="管理者パスワード未設定です"
        )

    if password != correct_password:
        raise HTTPException(
            status_code=403,
            detail="正しくないパスワードです"
        )
