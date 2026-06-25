from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models import VideoCrawlLog, VideoResource

logger = logging.getLogger("video_crawler")

BILIBILI_SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
BILIBILI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://search.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://search.bilibili.com",
    "Connection": "keep-alive",
}

PLATFORM_WEIGHTS = {"Bilibili": 1.0, "YouTube": 0.7, "其他": 0.5}
DEFAULT_PLATFORM_WEIGHT = 0.5

CRAWL_COOLDOWN_SECONDS = 3600
MAX_VIDEOS_PER_POINT = 5
MIN_VIDEOS_FOR_SKIP = 3


def _subject_search_keywords(subject: str) -> list[str]:
    mapping = {
        "数据结构": "数据结构",
        "计算机组成原理": "计组",
        "操作系统": "操作系统",
        "计算机网络": "计网",
    }
    return [mapping.get(subject, subject), "408", "考研"]


def _search_bilibili(keyword: str, page: int = 1, limit: int = 10) -> list[dict]:
    try:
        params = {"search_type": "video", "keyword": keyword, "page": page, "page_size": limit}
        resp = requests.get(BILIBILI_SEARCH_URL, params=params, headers=BILIBILI_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            logger.warning("Bilibili API error: code=%s, msg=%s", data.get("code"), data.get("message", ""))
            return []
        result = data.get("data", {})
        videos = []
        for item in (result.get("result", []) or []):
            videos.append({
                "platform": "Bilibili",
                "title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                "url": item.get("arcurl", ""),
                "cover_url": item.get("pic", ""),
                "duration": _format_duration(item.get("duration", "")),
                "author": item.get("author", ""),
                "play_count": item.get("play", 0) or 0,
                "danmaku_count": item.get("video_review", 0) or 0,
                "like_count": item.get("like", 0) or 0,
                "publish_time": item.get("pubdate", 0),
                "tag": item.get("tag", ""),
                "description": item.get("description", ""),
            })
        return videos
    except requests.RequestException as e:
        logger.error("Bilibili search failed: %s", e)
        return []
    except (KeyError, json.JSONDecodeError) as e:
        logger.error("Bilibili parse failed: %s", e)
        return []


def _format_duration(raw: str | int) -> str:
    try:
        seconds = int(raw)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except (ValueError, TypeError):
        return str(raw)


def _relevance_score(video: dict, subject: str, knowledge_point: str) -> float:
    text = f"{video.get('title', '')} {video.get('tag', '')} {video.get('description', '')}".lower()
    score = 0.0
    if knowledge_point.lower() in text:
        score += 0.6
    elif subject.lower() in text:
        score += 0.3
    kp_words = set(re.findall(r"[\w\u4e00-\u9fff]+", knowledge_point))
    if kp_words:
        matched = sum(1 for w in kp_words if w in text)
        score += matched * 0.1
    keywords = {"408", "考研", "计算机", subject[:2]}
    for kw in keywords:
        if kw in text:
            score += 0.05
    return min(score, 1.0)


def _popularity_score(video: dict) -> float:
    play = video.get("play_count", 0) or 0
    likes = video.get("like_count", 0) or 0
    danmaku = video.get("danmaku_count", 0) or 0
    combined = play + likes * 10 + danmaku * 5
    if combined >= 100000:
        return 1.0
    if combined >= 50000:
        return 0.8
    if combined >= 10000:
        return 0.6
    if combined >= 1000:
        return 0.4
    if combined >= 100:
        return 0.2
    return 0.1


def _freshness_score(video: dict) -> float:
    publish = video.get("publish_time", 0)
    if not publish:
        return 0.5
    try:
        pub_time = datetime.fromtimestamp(publish)
        days_ago = (datetime.now() - pub_time).days
        if days_ago <= 30:
            return 1.0
        if days_ago <= 90:
            return 0.8
        if days_ago <= 180:
            return 0.6
        if days_ago <= 365:
            return 0.4
        return 0.2
    except (OSError, ValueError):
        return 0.5


def score_video(video: dict, subject: str, knowledge_point: str) -> float:
    platform = video.get("platform", "其他")
    platform_weight = PLATFORM_WEIGHTS.get(platform, DEFAULT_PLATFORM_WEIGHT)
    relevance = _relevance_score(video, subject, knowledge_point)
    popularity = _popularity_score(video)
    freshness = _freshness_score(video)

    quality = (
        relevance * 0.40
        + popularity * 0.50
        + platform_weight * 0.10
        + freshness * 0.00
    )
    return round(quality, 4)


def deduplicate_videos(videos: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    result = []
    for v in videos:
        url = v.get("url", "").strip()
        title = v.get("title", "").strip()[:50]
        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        result.append(v)
    return result


def _can_crawl(db: Session, subject: str, knowledge_point: str) -> bool:
    existing = _existing_count(db, subject, knowledge_point)
    if existing >= MIN_VIDEOS_FOR_SKIP:
        return False
    last_log = (
        db.query(VideoCrawlLog)
        .filter(
            VideoCrawlLog.subject == subject,
            VideoCrawlLog.knowledge_point == knowledge_point,
            VideoCrawlLog.status == "success",
        )
        .order_by(VideoCrawlLog.crawl_time.desc())
        .first()
    )
    if last_log:
        elapsed = (datetime.utcnow() - last_log.crawl_time).total_seconds()
        if elapsed < CRAWL_COOLDOWN_SECONDS:
            return False
    return True


def _existing_count(db: Session, subject: str, knowledge_point: str) -> int:
    return (
        db.query(VideoResource)
        .filter(
            VideoResource.subject == subject,
            VideoResource.knowledge_point == knowledge_point,
            VideoResource.is_deleted == False,
        )
        .count()
    )


def _log_crawl(db: Session, subject: str, knowledge_point: str, url: str, platform: str, status: str, error_msg: str = "") -> None:
    log = VideoCrawlLog(subject=subject, knowledge_point=knowledge_point, url=url, platform=platform, status=status, error_msg=error_msg)
    db.add(log)
    db.flush()


def crawl_for_point(db: Session, subject: str, knowledge_point: str) -> list[dict]:
    existing = _existing_count(db, subject, knowledge_point)
    if existing >= MAX_VIDEOS_PER_POINT:
        logger.info("Already have %d videos for %s/%s, skip crawl", existing, subject, knowledge_point)
        return []

    if not _can_crawl(db, subject, knowledge_point):
        logger.info("Crawl skipped due to cooldown or sufficient videos for %s/%s", subject, knowledge_point)
        return []

    keywords = _subject_search_keywords(subject)
    keyword = f"{' '.join(keywords)} {knowledge_point}"
    raw = _search_bilibili(keyword, limit=20)
    if not raw:
        logger.warning("Bilibili returned no results for %s", keyword)
        return []

    for v in raw:
        v["score"] = score_video(v, subject, knowledge_point)
        v["subject"] = subject
        v["knowledge_point"] = knowledge_point

    raw.sort(key=lambda v: v["score"], reverse=True)
    deduped = deduplicate_videos(raw)

    new_count = 0
    saved = []
    for v in deduped:
        if existing + new_count >= MAX_VIDEOS_PER_POINT:
            break
        dup = (
            db.query(VideoResource)
            .filter(VideoResource.url == v["url"], VideoResource.is_deleted == False)
            .first()
        )
        if dup:
            continue
        resource = VideoResource(
            subject=subject,
            knowledge_point=knowledge_point,
            title=v["title"],
            platform=v["platform"],
            url=v["url"],
            cover_url=v.get("cover_url", ""),
            duration=v.get("duration", ""),
            reason=_generate_reason(v, subject, knowledge_point),
        )
        db.add(resource)
        db.flush()
        saved.append({
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "platform": resource.platform,
            "score": v["score"],
        })
        _log_crawl(db, subject, knowledge_point, v["url"], v["platform"], "success")
        new_count += 1

    if not saved:
        logger.info("No new unique videos found for %s/%s", subject, knowledge_point)
    return saved


def _generate_reason(video: dict, subject: str, knowledge_point: str) -> str:
    score = video.get("score", 0)
    author = video.get("author", "未知")
    play = video.get("play_count", 0)
    if score >= 0.7:
        return f"优质推荐 · {author} 制作 · 播放 {play} 次 · 与 {knowledge_point} 高度相关"
    if score >= 0.5:
        return f"{author} 讲解 · 播放 {play} 次 · 覆盖 {knowledge_point} 相关内容"
    return f"{author} · 播放 {play} 次 · 与 {knowledge_point} 相关"


def crawl_all_points(db: Session) -> dict:
    from models import KnowledgePoint

    points = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.is_deleted == False)
        .distinct(KnowledgePoint.subject, KnowledgePoint.name)
        .all()
    )
    seen = set()
    results: dict[str, list[dict]] = {}
    total_new = 0
    total_skipped = 0

    for kp in points:
        key = (kp.subject, kp.name)
        if key in seen:
            continue
        seen.add(key)
        existing = _existing_count(db, kp.subject, kp.name)
        if existing >= MAX_VIDEOS_PER_POINT:
            total_skipped += 1
            continue
        if not _can_crawl(db, kp.subject, kp.name):
            total_skipped += 1
            continue
        saved = crawl_for_point(db, kp.subject, kp.name)
        if saved:
            key_str = f"{kp.subject}/{kp.name}"
            results[key_str] = saved
            total_new += len(saved)
        time.sleep(1)

    return {
        "total_points": len(seen),
        "total_new_videos": total_new,
        "total_skipped": total_skipped,
        "results": results,
    }
