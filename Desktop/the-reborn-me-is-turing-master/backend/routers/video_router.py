import threading
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import VideoResource
from services.video_crawler_service import crawl_for_point
from utils.response import success


router = APIRouter(prefix="/api/videos", tags=["videos"])


def _background_crawl(subject: str, knowledge_point: str) -> None:
    try:
        db = SessionLocal()
        try:
            crawl_for_point(db, subject, knowledge_point)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("video_router").error("background crawl failed: %s", e)


@router.get("/recommend")
@router.get("/list")
def list_videos(
    subject: str = Query(default=""),
    knowledge_point: str = Query(default=""),
    db: Session = Depends(get_db),
):
    query = db.query(VideoResource).filter(VideoResource.is_deleted == False)
    if subject:
        query = query.filter(VideoResource.subject == subject)
    if knowledge_point:
        query = query.filter(VideoResource.knowledge_point == knowledge_point)
    rows = query.order_by(VideoResource.id.desc()).limit(20).all()

    if subject and knowledge_point and len(rows) < 3:
        threading.Thread(target=_background_crawl, args=(subject, knowledge_point), daemon=True).start()

    return success({
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "platform": r.platform,
                "url": r.url,
                "cover_url": r.cover_url,
                "duration": r.duration,
                "reason": r.reason,
                "subject": r.subject,
                "knowledge_point": r.knowledge_point,
            }
            for r in rows
        ]
    })


@router.post("/crawl")
def crawl(
    subject: str = Query(default=""),
    knowledge_point: str = Query(default=""),
    db: Session = Depends(get_db),
):
    if subject and knowledge_point:
        saved = crawl_for_point(db, subject, knowledge_point)
        db.commit()
        return success({
            "message": f"爬取完成，新增 {len(saved)} 个视频",
            "items": saved,
        })
    return success({"message": "请指定 subject 和 knowledge_point 参数"})
