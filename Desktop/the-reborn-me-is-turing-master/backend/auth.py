from sqlalchemy.orm import Session
from models import User, UserProfile
from utils.security import create_token, hash_password, verify_password, decode_token
from utils.response import AppError


def register_user(db: Session, email: str, username: str, password: str, nickname: str = "") -> User:
    existed = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existed:
        raise AppError("USER_EXISTS", "邮箱或用户名已存在")
    user = User(
        email=email,
        username=username,
        nickname=nickname or username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, long_profile="偏好结构化解释，适合用错题驱动复习。"))
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, account: str, password: str) -> User:
    user = db.query(User).filter((User.email == account) | (User.username == account)).first()
    if not user or not verify_password(password, user.password_hash):
        raise AppError("AUTH_FAILED", "账号或密码错误", status_code=401)
    return user


def token_for_user(user: User) -> str:
    return create_token({"sub": str(user.id), "username": user.username})


def user_id_from_token(token: str) -> int:
    try:
        return int(decode_token(token)["sub"])
    except Exception as exc:
        raise AppError("INVALID_TOKEN", "登录状态无效或已过期", status_code=401) from exc
