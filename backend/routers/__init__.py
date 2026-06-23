"""API router registration."""

from fastapi import APIRouter

from . import (
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

api_router = APIRouter()

for router in (
    auth_router.router,
    profile_router.router,
    home_router.router,
    knowledge_router.router,
    mastery_router.router,
    qa_router.router,
    conversation_router.router,
    question_router.router,
    answer_router.router,
    mistake_router.router,
    ocr_router.router,
    video_router.router,
    forum_router.router,
    memory_router.router,
    report_router.router,
):
    api_router.include_router(router)

