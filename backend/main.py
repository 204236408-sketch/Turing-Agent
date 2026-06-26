from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from config import FRONTEND_DIR, settings, validate_security_settings
from database import SessionLocal, init_database
from routers import (
    answer_router,
    auth_router,
    conversation_router,
    forum_router,
    home_router,
    knowledge_router,
    mastery_router,
    memory_router,
    mistake_router,
    ocr_router,
    profile_router,
    qa_router,
    question_router,
    report_router,
    video_router,
)
from services.chroma_service import ChromaService
from services.seed_service import seed_all
from utils.response import AppError, failure, success

chroma: ChromaService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global chroma
    validate_security_settings()
    init_database()
    chroma = ChromaService(settings.chroma_path)
    app.state.chroma = chroma
    with SessionLocal() as db:
        seed_all(db)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

origins = ["*"] if settings.cors_origins == "*" else [item.strip() for item in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=failure(exc.code, exc.message, request.state.request_id, exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=failure("VALIDATION_ERROR", "参数不完整或格式错误", request.state.request_id, exc.errors()),
    )


@app.exception_handler(Exception)
async def unknown_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=failure("INTERNAL_ERROR", "服务器内部异常，请查看日志", request.state.request_id, str(exc)),
    )


@app.get("/api/health")
def health():
    return success(
        {
            "app": settings.app_name,
            "env": settings.app_env,
            "database": settings.active_database_url.split("://", 1)[0],
            "llm": {
                "enabled": settings.llm_enabled,
                "base_url": settings.siliconflow_base_url,
                "model": settings.siliconflow_model,
            },
            "chroma": chroma.status(),
        }
    )


app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(home_router.router)
app.include_router(knowledge_router.router)
app.include_router(mastery_router.router)
app.include_router(qa_router.router)
app.include_router(conversation_router.router)
app.include_router(question_router.router)
app.include_router(answer_router.router)
app.include_router(mistake_router.router)
app.include_router(ocr_router.router)
app.include_router(video_router.router)
app.include_router(forum_router.router)
app.include_router(memory_router.router)
app.include_router(report_router.router)


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
