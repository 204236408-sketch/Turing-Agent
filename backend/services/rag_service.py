from sqlalchemy.orm import Session
from models import KnowledgePoint, UserMemory


def retrieve_knowledge(db: Session, query: str, limit: int = 5) -> list[dict]:
    normalized = query.lower()
    forced_point = None
    if any(key in normalized for key in ["lru", "fifo", "opt", "clock", "页面", "缺页", "置换"]):
        forced_point = "页面置换算法"
    elif any(key in normalized for key in ["tcp", "udp", "time_wait", "握手", "挥手"]):
        forced_point = "传输层"
    elif any(key in normalized for key in ["二叉树", "遍历", "前序", "中序", "后序"]):
        forced_point = "树与二叉树"

    if forced_point:
        item = db.query(KnowledgePoint).filter(KnowledgePoint.name == forced_point).first()
        if item:
            return [
                {
                    "subject": item.subject,
                    "knowledge_point": item.name,
                    "content": item.content,
                    "common_mistakes": item.common_mistakes,
                }
            ]

    words = [w for w in query.replace("，", " ").replace("。", " ").split() if w]
    items = db.query(KnowledgePoint).all()
    scored = []
    for item in items:
        text = f"{item.subject} {item.name} {item.content} {item.keywords}"
        score = sum(1 for word in words if word in text)
        if item.name in query:
            score += 3
        if score:
            scored.append((score, item))
    if not scored:
        scored = [(1, item) for item in items[:limit]]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "subject": item.subject,
            "knowledge_point": item.name,
            "content": item.content,
            "common_mistakes": item.common_mistakes,
        }
        for _, item in scored[:limit]
    ]


def retrieve_user_memory(db: Session, user_id: int, query: str = "", limit: int = 5) -> list[dict]:
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
