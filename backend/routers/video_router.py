"""
视频资源接口

功能：
- GET  /api/videos/recommend         — 智能推荐视频（LLM关键词提取 + 多级匹配）
- GET  /api/videos/list              — 视频列表（支持按科目、知识点筛选）
- POST /api/videos/crawl             — 爬取视频资源（显式 mock，仅返回开发提示）
- POST /api/videos/click             — 记录用户视频点击（用于个性化推荐）
- GET  /api/videos/my-clicked        — 获取用户点击过的视频历史
"""
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from dependencies import get_current_user
from models import User, VideoViewLog
from services.video_service import recommend_videos, recommend_videos_v2
from utils.response import success


router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.get("/recommend")
def recommend(
    subject: str = Query("", description="科目"),
    knowledge_point: str = Query("", description="知识点"),
    question_text: str = Query("", description="题目原文，用于LLM提取关键词"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    智能推荐视频（增强版）
    - 有 question_text → 使用 LLM 提取关键词 + 融合评分
    - 无 question_text → 退化为规则匹配
    """
    if question_text and len(question_text) > 10:
        # 有题目文本，使用增强版 LLM 关键词提取
        result = recommend_videos_v2(
            db,
            subject=subject,
            knowledge_point=knowledge_point,
            question_text=question_text,
            limit=limit,
            use_llm=True,
        )
        return success({
            "items": result.get("items", []),
            "subject": subject,
            "knowledge_point": knowledge_point,
            "llm_keywords": result.get("llm_keywords", []),
            "keyword_extract_method": result.get("keyword_extract_method", "unknown"),
            "total_candidates": result.get("total_candidates", 0),
            "local_count": result.get("local_count", 0),
            "crawl_count": result.get("crawl_count", 0),
            "cache_hit": result.get("cache_hit", False),
        })
    else:
        # 无题目文本，退化为规则匹配
        items = recommend_videos(db, subject=subject, knowledge_point=knowledge_point, limit=limit)
        return success({"items": items, "subject": subject, "knowledge_point": knowledge_point})


@router.get("/list")
def list_videos(subject: str = "", knowledge_point: str = "", db: Session = Depends(get_db)):
    items = recommend_videos(db, subject=subject, knowledge_point=knowledge_point, limit=20)
    return success({"items": items})


@router.post("/crawl")
def crawl():
    return success({"message": "开发版不爬取外站，已返回本地视频元数据。"})


@router.post("/click")
def record_click(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    记录用户视频点击日志

    payload 字段:
    - video_id: 视频ID（本地视频），爬虫视频可不传
    - video_url: 视频URL
    - video_title: 视频标题
    - question_id: 关联的题目ID
    - subject: 科目
    - knowledge_point: 知识点
    - author: 作者
    - click_position: 在推荐列表中的位置
    - match_level: 匹配等级
    - source: local_seed / realtime_crawl
    """
    log = VideoViewLog(
        user_id=user.id,
        video_id=payload.get("video_id"),
        video_url=payload.get("video_url", "")[:255],
        video_title=payload.get("video_title", "")[:255],
        question_id=payload.get("question_id"),
        subject=payload.get("subject", "")[:64],
        knowledge_point=payload.get("knowledge_point", "")[:128],
        author=payload.get("author", "")[:128],
        click_position=payload.get("click_position", 0),
        match_level=payload.get("match_level", "")[:32],
        source=payload.get("source", "")[:32],
        create_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return success({"logged": True, "log_id": log.id})


@router.get("/my-clicked")
def my_clicked(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取用户最近点击过的视频（用于个性化推荐）"""
    rows = (
        db.query(VideoViewLog)
        .filter(VideoViewLog.user_id == user.id)
        .order_by(VideoViewLog.create_time.desc())
        .limit(limit)
        .all()
    )
    return success({
        "items": [
            {
                "id": r.id,
                "video_id": r.video_id,
                "video_url": r.video_url,
                "video_title": r.video_title,
                "subject": r.subject,
                "knowledge_point": r.knowledge_point,
                "author": r.author,
                "source": r.source,
                "match_level": r.match_level,
                "click_time": r.create_time.isoformat() if r.create_time else "",
            }
            for r in rows
        ]
    })


@router.get("/config")
def video_config():
    """返回视频推荐的可配置项（前端可见）"""
    return success({
        "default_limit": settings.video_recommend_default_limit,
        "max_limit": settings.video_recommend_max_limit,
        "llm_threshold": settings.video_llm_threshold,
        "crawl_enabled": settings.video_crawl_enabled,
        "local_enabled": settings.video_local_enabled,
        "parallel_enabled": settings.video_parallel_enabled,
        "user_click_weight": settings.video_user_click_weight,
    })
