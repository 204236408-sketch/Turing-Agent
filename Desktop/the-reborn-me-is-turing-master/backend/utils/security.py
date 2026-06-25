import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any
from config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _, salt_b64, digest_b64 = password_hash.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_token(payload: dict[str, Any]) -> str:
    body = {**payload, "exp": int(time.time()) + settings.access_token_expire_minutes * 60}
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = _b64(raw)
    signature = hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_b64(signature)}"


def decode_token(token: str) -> dict[str, Any]:
    encoded, signature = token.split(".", 1)
    expected = hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_unb64(signature), expected):
        raise ValueError("bad signature")
    payload = json.loads(_unb64(encoded).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("expired")
    return payload
