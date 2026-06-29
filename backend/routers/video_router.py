"""
视频资源接口

功能：
- GET  /api/videos/recommend         — 智能推荐视频（LLM关键词提取 + 多级匹配）
- GET  /api/videos/list              — 视频列表（支持按科目、知识点筛选）
- GET  /api/videos/proxy-image       — 代理下载 B 站图床图片（绕过防盗链）
- POST /api/videos/crawl             — 爬取视频资源（显式 mock，仅返回开发提示）
- POST /api/videos/click             — 记录用户视频点击（用于个性化推荐）
- GET  /api/videos/my-clicked        — 获取用户点击过的视频历史
"""
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, Body, Depends, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from dependencies import get_current_user
from models import KnowledgePoint, User, VideoViewLog
from services.video_service import (
    recommend_videos,
    recommend_videos_v2,
    recommend_wangdao_for_knowledge_point,
)
from utils.response import success


router = APIRouter(prefix="/api/videos", tags=["videos"])

# 图片代理缓存目录
_PROXY_IMG_DIR = Path(__file__).resolve().parent.parent / "frontend" / "covers"
_PROXY_IMG_DIR.mkdir(parents=True, exist_ok=True)
_PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}
# 只允许代理 B 站图床域名（安全白名单）
_ALLOWED_HOSTS = {"i0.hdslb.com", "i1.hdslb.com", "i2.hdslb.com", "bimp.hdslb.com"}


@router.get("/recommend")
def recommend(
    subject: str = Query("", description="科目"),
    knowledge_point: str = Query("", description="知识点"),
    knowledge_point_id: int | None = Query(default=None, description="知识点ID"),
    scene: str = Query("", description="推荐场景"),
    question_text: str = Query("", description="题目原文，用于LLM提取关键词"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    智能推荐视频（增强版）
    - 有 question_text → 使用 LLM 提取关键词 + 融合评分
    - 无 question_text → 退化为规则匹配
    """
    # 通过 knowledge_point_id 查出完整信息
    point_keywords = ""
    point_content = ""
    point_mistakes = ""
    if knowledge_point_id:
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if point:
            subject = subject or point.subject
            knowledge_point = knowledge_point or (point.section or point.name)
            point_keywords = point.keywords or ""
            point_content = point.content or ""
            point_mistakes = point.common_mistakes or ""

    # 知识点详情页场景：用知识点名称+关键词+正文+易错点拼接为搜索文本，走 v2 接口
    kp_search_text = ""
    if knowledge_point and not question_text:
        parts = [knowledge_point]
        if point_keywords:
            parts.append(point_keywords)
        if point_content:
            parts.append(point_content[:300])  # 取正文前300字，避免过长
        if point_mistakes:
            parts.append(point_mistakes[:200])
        kp_search_text = " ".join(parts)

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
    elif kp_search_text and knowledge_point_id:
        # 知识点详情页场景：规则匹配 DB 中的王道对应知识点视频
        # （无匹配时不强凑，避免混入不相关内容）
        result = recommend_wangdao_for_knowledge_point(
            db,
            knowledge_point_id=knowledge_point_id,
            limit=limit,
        )
        return success({
            "items": result.get("items", []),
            "subject": result.get("subject", subject),
            "knowledge_point": result.get("knowledge_point", knowledge_point),
            "wangdao_matched": result.get("wangdao_matched", 0),
            "wangdao_passed": result.get("wangdao_passed", 0),
            "total_returned": result.get("total_returned", 0),
            "min_score": result.get("min_score", 50),
            "max_count": result.get("max_count", 5),
            "source_priority": result.get("source_priority", "wangdao_db"),
            "scene": "knowledge_point",
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


@router.get("/proxy-image")
def proxy_image(url: str = Query(..., description="B站图床图片URL")):
    """代理下载 B 站图床图片，绕过 Referer 防盗链。

    缓存到 frontend/covers/proxy_{hash}.jpg，首次请求下载，后续直接读本地。
    前端用法: <img src="/api/videos/proxy-image?url=https://i0.hdslb.com/...">
    """
    # 安全校验：只允许 B 站图床域名
    parsed = urlparse(url)
    if parsed.hostname not in _ALLOWED_HOSTS:
        return Response(status_code=403, content="Forbidden host")
    if not url.startswith("https://"):
        return Response(status_code=400, content="Only https allowed")

    # 用 URL hash 作为缓存文件名
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    cache_path = _PROXY_IMG_DIR / f"proxy_{url_hash}.jpg"

    # 缓存命中 → 直接返回本地文件
    if cache_path.exists():
        return FileResponse(str(cache_path), media_type="image/jpeg")

    # 下载
    try:
        r = requests.get(url, headers=_PROXY_HEADERS, timeout=15)
        r.raise_for_status()
        cache_path.write_bytes(r.content)
        return FileResponse(str(cache_path), media_type="image/jpeg")
    except Exception:
        # 下载失败 → 返回 404，前端 onerror 会显示 fallback
        return Response(status_code=404, content="Image not found")
