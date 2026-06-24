from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import VideoResource
from utils.response import success


router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("/recommend")
@router.get("/list")
def list_videos(subject: str = "", knowledge_point: str = "", db: Session = Depends(get_db)):
    query = db.query(VideoResource)
    if subject:
        query = query.filter(VideoResource.subject == subject)
    if knowledge_point:
        query = query.filter(VideoResource.knowledge_point == knowledge_point)
    rows = query.limit(20).all()
    return success({"items": [{"id": r.id, "title": r.title, "platform": r.platform, "url": r.url, "reason": r.reason} for r in rows]})


@router.post("/crawl")
def crawl():
    return success({"message": "开发版不爬取外站，已返回本地视频元数据。"})


@router.post("/view/{video_id}")
def view(video_id: int):
    return success({"video_id": video_id, "viewed": True})
