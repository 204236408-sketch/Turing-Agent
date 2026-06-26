from __future__ import annotations

from sqlalchemy.orm import Session

from agents.qa_graph import get_qa_graph, set_db
from models import ConversationMessage


def answer_question(db: Session, user_id: int, question: str, conversation_id: int | None = None) -> dict:
    """回答用户问题，支持连续追问和 RAG 检索。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        question: 用户提问文本。
        conversation_id: 会话 ID，用于追问场景。

    Returns:
        dict: 包含 answer, subject, knowledge_point, agent_steps, llm_used, llm_error 等。
    """
    history = []
    if conversation_id:
        rows = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.id.desc())
            .limit(6)
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in reversed(rows)]

    set_db(db)
    initial_state = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "question": question,
        "history": history,
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }

    result = get_qa_graph().invoke(initial_state)

    answer = result.get("answer", {})
    steps = result.get("agent_steps", [])

    steps_out = []
    for s in steps:
        steps_out.append({
            "name": s.get("name", ""),
            "input_summary": s.get("input_summary", ""),
            "output_summary": s.get("output_summary", ""),
            "duration_ms": s.get("duration_ms", 0),
            "status": s.get("status", ""),
        })

    return {
        "answer": answer.get("content", ""),
        "subject": answer.get("subject", "408"),
        "knowledge_point": answer.get("knowledge_point", "综合"),
        "retrieved_knowledge": result.get("retrieved_knowledge", []),
        "memories": result.get("memories_used", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "agent_steps": steps_out,
        "suggested_followups": result.get("suggested_followups", []),
    }
