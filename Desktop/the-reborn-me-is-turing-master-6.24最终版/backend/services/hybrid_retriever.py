from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session
from models import KnowledgePoint
from services.chroma_service import query_documents
from services.reranker_service import rerank
from services.knowledge_heuristics import infer_subject, infer_knowledge_point


def hybrid_retrieve(
    db: Session,
    query: str,
    limit: int = 5,
    subject_filter: str | None = None,
    kp_filter: str | None = None,
    use_rerank: bool = True,
) -> dict:
    inferred_subject = subject_filter or infer_subject(query)
    inferred_kp = kp_filter or infer_knowledge_point(query)

    vector_items = _vector_search(query, limit * 2, inferred_subject, None)
    keyword_items = _keyword_search(db, query, limit * 2, inferred_subject, inferred_kp)

    fused = _fusion_rank(vector_items, keyword_items, top_k=limit * 2)

    if use_rerank and fused:
        fused = rerank(query, fused, top_k=limit)

    return {
        "items": fused[:limit],
        "total_found": len(fused),
        "vector_count": len(vector_items),
        "keyword_count": len(keyword_items),
        "inferred": {"subject": inferred_subject, "knowledge_point": inferred_kp},
    }


def _vector_search(
    query: str, limit: int,
    subject: str | None, kp: str | None,
) -> list[dict]:
    where = {}
    if kp:
        where["knowledge_point"] = kp
    if subject:
        where["subject"] = subject

    result = query_documents("knowledge_base_408", query, limit=limit, where=where if where else None)

    if result.get("fallback") or not result.get("items"):
        return []

    items = []
    for item in result["items"]:
        meta = item.get("metadata", {})
        items.append({
            "id": item.get("id", ""),
            "subject": meta.get("subject", ""),
            "knowledge_point": meta.get("knowledge_point", ""),
            "section": meta.get("section", ""),
            "h1_title": meta.get("h1_title", ""),
            "h2_title": meta.get("h2_title", ""),
            "content": item.get("text", ""),
            "score": item.get("score", 0),
            "source": "chromadb",
            "rerank_score": item.get("score", 0.0),
            "chunk_index": meta.get("chunk_index", 0),
            "total_chunks": meta.get("total_chunks", 1),
        })
    return items


def _keyword_search(
    db: Session, query: str, limit: int,
    subject: str | None, kp: str | None,
) -> list[dict]:
    words = _tokenize(query)
    if not words:
        return []

    db_query = db.query(KnowledgePoint)
    if subject:
        db_query = db_query.filter(KnowledgePoint.subject == subject)
    if kp:
        db_query = db_query.filter(KnowledgePoint.name == kp)

    rows = db_query.all()
    scored = []
    for item in rows:
        text = f"{item.subject} {item.name} {item.content} {item.keywords or ''}"
        score = sum(1 for w in words if w in text)
        if item.name and item.name in query:
            score += 3
        if item.subject and item.subject in query:
            score += 2
        if score:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "subject": item.subject,
            "knowledge_point": item.name,
            "section": item.section or "",
            "content": item.content,
            "score": s / max(s for s, _ in scored) if scored else 0,
            "source": "mysql",
            "rerank_score": 0.0,
        }
        for s, item in scored[:limit]
    ]


def _fusion_rank(
    vector_items: list[dict],
    keyword_items: list[dict],
    top_k: int = 10,
    alpha: float = 0.5,
) -> list[dict]:
    seen_contents: set[str] = set()
    combined: list[dict] = []

    max_v_score = max((x.get("score", 0) for x in vector_items), default=1.0)
    max_k_score = max((x.get("score", 0) for x in keyword_items), default=1.0)

    for item in vector_items + keyword_items:
        content = item.get("content", "")
        key = content[:200]
        if key in seen_contents:
            continue
        seen_contents.add(key)

        v_score = item.get("score", 0) / max_v_score if item["source"] == "chromadb" else 0
        k_score = item.get("score", 0) / max_k_score if item["source"] == "mysql" else 0

        item["fusion_score"] = alpha * v_score + (1 - alpha) * k_score
        combined.append(item)

    combined.sort(key=lambda x: x.get("fusion_score", 0), reverse=True)
    return combined[:top_k]


def _tokenize(query: str) -> list[str]:
    cleaned = re.sub(r'[，。、？；：""''！（）?:;!()]', " ", query)
    return [w for w in cleaned.split() if w]
