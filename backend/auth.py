"""Password hashing and JWT helpers."""

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from config import settings

ALGORITHM = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(subject: str, expires_minutes: int = 30) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        settings.secret_key,
        algorithm=ALGORITHM,
    )

