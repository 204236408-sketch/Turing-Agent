from typing import Any
from fastapi import Request


class AppError(Exception):
    def __init__(self, code: str, message: str, detail: Any = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)


def success(data: Any = None, message: str = "success") -> dict:
    return {"ok": True, "message": message, "data": data if data is not None else {}}


def failure(code: str, message: str, request_id: str, detail: Any = None) -> dict:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "detail": detail if detail is not None else [],
            "request_id": request_id,
        },
    }


def request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "")
