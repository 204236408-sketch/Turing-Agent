from __future__ import annotations

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import user_id_from_token
from services.chroma_service import ChromaService
from utils.response import AppError


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if authorization and authorization.lower().startswith("bearer "):
        user_id = user_id_from_token(authorization.split(" ", 1)[1])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppError("USER_NOT_FOUND", "用户不存在", status_code=401)
        return user

    demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
    if demo:
        return demo
    raise AppError("DEMO_USER_MISSING", "演示用户未初始化", status_code=500)


def get_chroma(request: Request) -> ChromaService:
    return request.app.state.chroma
