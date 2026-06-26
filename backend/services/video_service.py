from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from models import VideoResource
from services.video_crawler_service import _popularity_score, _search_bilibili

logger = logging.getLogger("video_service")

KP_ALIASES: dict[str, set[str]] = {
    "栈、队列和数组": {"栈和队列", "栈", "队列", "数组"},
    "树与二叉树": {"树与二叉树", "二叉树", "树", "树、森林"},
    "进程与线程": {"进程与线程", "进程", "线程", "同步与互斥", "进程同步", "死锁"},
    "内存管理": {"内存管理", "分页", "分页管理", "虚拟内存", "页面置换", "LRU", "FIFO", "页面置换算法"},
    "计算机系统概述": {"计算机系统概述", "概述", "OS概述"},
    "输入输出系统": {"输入输出系统", "I/O", "IO", "输入输出", "IO系统", "总线与 I/O", "总线与IO"},
    "总线": {"总线", "总线与 I/O", "总线与IO"},
    "中央处理器": {"中央处理器", "CPU", "数据通路", "控制器"},
    "数据的表示和运算": {"数据的表示和运算", "数据表示", "运算", "数据表示与运算", "浮点数", "数据通路"},
    "文件管理": {"文件管理", "文件系统", "文件", "目录"},
    "输入输出管理": {"输入输出管理", "I/O管理", "IO管理", "输入输出", "I/O", "IO系统"},
    "传输层": {"传输层", "TCP", "UDP"},
    "计算机网络体系结构": {"计算机网络体系结构", "体系结构", "网络体系结构"},
    "串": {"串", "字符串"},
    "查找": {"查找", "散列"},
    "排序": {"排序"},
    "图": {"图"},
    "线性表": {"线性表", "链表", "顺序表"},
    "存储系统": {"存储系统", "Cache", "主存", "存储器", "高速缓冲", "虚拟存储器"},
    "指令系统": {"指令系统", "指令", "寻址", "CISC", "RISC", "流水线"},
    "物理层": {"物理层", "通信基础", "传输介质"},
    "数据链路层": {"数据链路层", "介质访问", "局域网", "差错控制"},
    "网络层": {"网络层", "IP", "IPv4", "IPv6", "路由"},
    "应用层": {"应用层", "DNS", "万维网", "HTTP", "电子邮件"},
    "绪论": {"绪论", "算法", "算法评价"},
}

_STOP_ENGLISH = {"THE", "AND", "FOR", "NOT", "ARE", "ALL", "CAN", "HAS", "WILL", "MAY", "THIS", "THAT", "WITH", "FROM", "THAN", "ALSO"}


def extract_question_keywords(text: str, knowledge_point: str = "") -> list[str]:
    """从题目文本中提取关键术语，用于视频匹配"""
    if not text:
        return [kp for kp in [knowledge_point] if kp]

    keywords: set[str] = set()
    text_lower = text.lower()

    all_known_terms: set[str] = set()
    for kp, aliases in KP_ALIASES.items():
        all_known_terms.add(kp)
        all_known_terms.update(aliases)
    for term in all_known_terms:
        if len(term) >= 2 and term.lower() in text_lower:
            keywords.add(term)

    subjects = {"数据结构", "计算机组成原理", "操作系统", "计算机网络"}
    for s in subjects:
        if s in text:
            keywords.add(s)

    eng_terms = re.findall(r'\b[A-Za-z][A-Za-z0-9+#.\-/]*\b', text)
    for t in eng_terms:
        if len(t) >= 2 and t.upper() not in _STOP_ENGLISH:
            keywords.add(t)

    if knowledge_point:
        keywords.add(knowledge_point)

    return [k for k in keywords if k]


def _keyword_relevance(text: str, keywords: list[str]) -> float:
    """关键词相关度 (0~1)"""
    if not keywords or not text:
        return 0.5
    text_lower = text.lower()
    matched = sum(1 for kw in keywords if kw.lower() in text_lower)
    return min(matched / len(keywords), 1.0)


def _score_local(v: VideoResource, keywords: list[str]) -> tuple[float, float, str]:
    """本地视频评分: (keyword_relevance, final_score, match_label)"""
    target = f"{v.title or ''} {v.reason or ''} {v.knowledge_point or ''}"
    kw_rel = _keyword_relevance(target, keywords)
    pop = (v.quality_score or 0) / 100.0
    final = kw_rel * 0.50 + pop * 0.50

    kp_match = v.knowledge_point and any(kw.lower() in v.knowledge_point.lower() for kw in keywords)
    title_match = v.title and any(kw.lower() in v.title.lower() for kw in keywords)

    if kp_match:
        label = "exact"
    elif title_match and kw_rel >= 0.4:
        label = "keyword"
    elif kw_rel >= 0.3:
        label = "alias"
    else:
        label = "subject"

    return kw_rel, final, label


def _score_bili(v: dict, keywords: list[str]) -> tuple[float, float, str]:
    """B站视频评分: (keyword_relevance, final_score, match_label)"""
    target = f"{v.get('title', '')} {v.get('description', '')} {v.get('tag', '')}"
    kw_rel = _keyword_relevance(target, keywords)
    pop = _popularity_score(v)
    final = kw_rel * 0.50 + pop * 0.50

    title = v.get("title", "")
    title_match = any(kw.lower() in title.lower() for kw in keywords)

    if kw_rel >= 0.6:
        label = "exact"
    elif title_match and kw_rel >= 0.3:
        label = "keyword"
    elif kw_rel >= 0.15:
        label = "alias"
    else:
        label = "subject"

    return kw_rel, final, label


def _format_item(v: VideoResource | dict, label: str, final_score: float, source: str, subject: str, knowledge_point: str) -> dict:
    if isinstance(v, VideoResource):
        return {
            "id": v.id,
            "title": v.title,
            "platform": v.platform or "Bilibili",
            "url": v.url,
            "cover_url": v.cover_url or "",
            "duration": v.duration or "",
            "author": v.author or "",
            "reason": v.reason or "",
            "subject": v.subject,
            "knowledge_point": v.knowledge_point or "",
            "match_level": label,
            "final_score": round(final_score, 4),
            "source": source,
        }
    return {
        "id": 0,
        "title": v.get("title", ""),
        "platform": "Bilibili",
        "url": v.get("url", ""),
        "cover_url": v.get("cover_url", ""),
        "duration": v.get("duration", ""),
        "author": v.get("author", ""),
        "reason": f"实时搜索 · 匹配关键词" if source == "bilibili" else "",
        "subject": subject,
        "knowledge_point": knowledge_point,
        "match_level": label,
        "final_score": round(final_score, 4),
        "source": source,
    }


def recommend_videos(
    db: Session,
    subject: str = "",
    knowledge_point: str = "",
    question_text: str = "",
    limit: int = 8,
) -> list[dict]:
    keywords = extract_question_keywords(question_text, knowledge_point)
    logger.info("Recommend videos | subject=%s kp=%s keywords=%s", subject, knowledge_point, keywords)

    query = db.query(VideoResource).filter(VideoResource.is_deleted == False)
    if subject:
        query = query.filter(VideoResource.subject == subject)
    local_videos = query.all()

    scored_local: list[tuple[float, str, VideoResource]] = []
    for v in local_videos:
        _, final, label = _score_local(v, keywords)
        scored_local.append((final, label, v))
    scored_local.sort(key=lambda x: -x[0])

    merged: list[dict] = []
    seen_urls: set[str] = set()

    good_threshold = 0.3
    good_local = [x for x in scored_local if x[0] >= good_threshold]

    for final, label, v in scored_local:
        if len(merged) >= limit:
            break
        if v.url in seen_urls:
            continue
        seen_urls.add(v.url)
        merged.append(_format_item(v, label, final, "local", v.subject, v.knowledge_point or ""))

    need_fallback = len(good_local) < limit and keywords and any(kp for kp in keywords if len(kp) >= 2)

    if need_fallback:
        try:
            search_q_keywords = keywords[:4]
            search_query = f"{' '.join(search_q_keywords)} 408 考研"
            logger.info("B站 fallback search: %s", search_query)

            bili_raw = _search_bilibili(search_query, limit=20, order="click")
            if not bili_raw:
                bili_raw = _search_bilibili(search_query, limit=20, order="click", duration=0)

            if bili_raw:
                scored_bili: list[tuple[float, str, dict]] = []
                for v in bili_raw:
                    _, final, label = _score_bili(v, keywords)
                    scored_bili.append((final, label, v))
                scored_bili.sort(key=lambda x: -x[0])

                for final, label, v in scored_bili:
                    if len(merged) >= limit:
                        break
                    url = v.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    merged.append(_format_item(v, label, final, "bilibili", subject, knowledge_point))
        except Exception as e:
            logger.error("B站 fallback failed: %s", e)

    merged.sort(key=lambda x: -x["final_score"])
    return merged[:limit]
