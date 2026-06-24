from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth import authenticate_user, register_user, token_for_user
from database import get_db
from dependencies import get_current_user
from models import User
from schemas import LoginRequest, RegisterRequest
from utils.response import success


router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_payload(user: User) -> dict:
    return {"id": user.id, "email": user.email, "username": user.username, "nickname": user.nickname}


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload.email, payload.username, payload.password, payload.nickname)
    return success({"user": user_payload(user), "access_token": token_for_user(user)})


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.account, payload.password)
    return success({"user": user_payload(user), "access_token": token_for_user(user)})


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return success({"user": user_payload(user)})


@router.post("/logout")
def logout():
    return success({"logged_out": True})
