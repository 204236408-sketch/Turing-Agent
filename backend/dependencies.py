from __future__ import annotations

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

<<<<<<< HEAD
from database import get_db
from models import User
from auth import user_id_from_token
=======
from auth import user_id_from_token
from config import settings
from database import get_db
from models import User
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
from services.chroma_service import ChromaService
from utils.response import AppError


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
<<<<<<< HEAD
    if authorization and authorization.lower().startswith("bearer "):
        user_id = user_id_from_token(authorization.split(" ", 1)[1])
=======
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AppError("UNAUTHORIZED", "缺少或无效的登录凭证", status_code=401)

        user_id = user_id_from_token(token.strip())
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppError("USER_NOT_FOUND", "用户不存在", status_code=401)
        return user

<<<<<<< HEAD
    demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
    if demo:
        return demo
    raise AppError("DEMO_USER_MISSING", "演示用户未初始化", status_code=500)
=======
    if settings.allow_demo_auth_fallback:
        demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
        if demo:
            return demo
        raise AppError("DEMO_USER_MISSING", "演示用户未初始化", status_code=500)

    raise AppError("UNAUTHORIZED", "请先登录后再访问该接口", status_code=401)
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)


def get_chroma(request: Request) -> ChromaService:
    return request.app.state.chroma
