from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session
from models import UserMemory
from services.hybrid_retriever import hybrid_retrieve


@dataclass
class RAGContext:
    knowledge_chunks: list[dict] = field(default_factory=list)
    user_memories: list[dict] = field(default_factory=list)
    formatted_context: str = ""
    total_chars: int = 0
    retrieval_info: dict = field(default_factory=dict)


def retrieve_knowledge(
    db: Session,
    query: str,
    limit: int = 5,
    subject_filter: str | None = None,
    kp_filter: str | None = None,
    use_rerank: bool = True,
) -> dict:
    return hybrid_retrieve(
        db=db,
        query=query,
        limit=limit,
        subject_filter=subject_filter,
        kp_filter=kp_filter,
        use_rerank=use_rerank,
    )


def build_rag_context(
    db: Session,
    query: str,
    user_id: int | None = None,
    max_chunks: int = 5,
    max_memories: int = 3,
    max_context_chars: int = 3000,
    use_rerank: bool = True,
) -> RAGContext:
    retrieval = hybrid_retrieve(
        db=db, query=query, limit=max_chunks, use_rerank=use_rerank,
    )
    context = RAGContext(
        knowledge_chunks=retrieval["items"],
        retrieval_info=retrieval,
    )

    if user_id:
        context.user_memories = retrieve_user_memory(db, user_id, query, limit=max_memories)

    parts = []
    if context.knowledge_chunks:
        parts.append("【知识库参考】")
        for i, item in enumerate(context.knowledge_chunks, 1):
            subj = item.get("subject", "未知科目")
            kp = item.get("knowledge_point", item.get("section", ""))
            content = item.get("content", "")
            score = item.get("rerank_score", item.get("score", 0))
            source = item.get("source", "?")
            parts.append(f"[{i}] ({subj}/{kp}) [score={score:.3f}, src={source}]\n{content[:600]}")

    if context.user_memories:
        parts.append("\n【用户记忆】")
        for item in context.user_memories:
            parts.append(f"- {item.get('content', '')[:300]}")

    formatted = "\n\n".join(parts)
    if len(formatted) > max_context_chars:
        formatted = formatted[:max_context_chars] + "\n...(truncated)"

    context.formatted_context = formatted
    context.total_chars = len(formatted)
    return context


def retrieve_user_memory(
    db: Session, user_id: int,
    query: str = "", limit: int = 5,
) -> list[dict]:
    rows = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id, UserMemory.status == "active")
        .order_by(UserMemory.update_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "type": row.memory_type,
            "subject": row.subject,
            "knowledge_point": row.knowledge_point,
            "content": row.content,
            "evidence": row.evidence,
        }
        for row in rows
    ]
