from __future__ import annotations

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from auth import is_token_revoked, user_id_from_token
from config import settings
from database import get_db
from models import User
from services.chroma_service import ChromaService
from utils.response import AppError


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AppError("UNAUTHORIZED", "缺少或无效的登录凭证", status_code=401)

        token = token.strip()
        if is_token_revoked(token):
            raise AppError("TOKEN_REVOKED", "登录状态已注销,请重新登录", status_code=401)
        user_id = user_id_from_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppError("USER_NOT_FOUND", "用户不存在", status_code=401)
        return user

    if settings.allow_demo_auth_fallback:
        demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
        if demo:
            return demo
        raise AppError("DEMO_USER_MISSING", "演示用户未初始化", status_code=500)

    raise AppError("UNAUTHORIZED", "请先登录后再访问该接口", status_code=401)


def get_current_user_optional(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User | None:
    """可选的用户认证 - 用于未登录也能访问但登录后体验更好的接口"""
    if not authorization:
        return None
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return None
        user_id = user_id_from_token(token.strip())
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None


def get_chroma(request: Request) -> ChromaService:
    return request.app.state.chroma
