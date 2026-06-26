"""
视频资源接口

功能：
- GET  /api/videos/recommend  — 智能推荐视频（按科目+知识点多级匹配）
- GET  /api/videos/list       — 视频列表（支持按科目、知识点筛选）
- POST /api/videos/crawl      — 爬取视频资源（显式 mock，仅返回开发提示）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.video_service import recommend_videos
from utils.response import success


router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("/recommend")
def recommend(
    subject: str = Query("", description="科目"),
    knowledge_point: str = Query("", description="知识点"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    items = recommend_videos(db, subject, knowledge_point, limit)
    return success({"items": items, "subject": subject, "knowledge_point": knowledge_point})


@router.get("/list")
def list_videos(subject: str = "", knowledge_point: str = "", db: Session = Depends(get_db)):
    items = recommend_videos(db, subject, knowledge_point, limit=20)
    return success({"items": items})


@router.post("/crawl")
def crawl():
    return success({"message": "开发版不爬取外站，已返回本地视频元数据。"})
