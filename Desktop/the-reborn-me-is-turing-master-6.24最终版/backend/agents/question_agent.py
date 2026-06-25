from __future__ import annotations

from sqlalchemy.orm import Session

from agents.question_graph import get_question_graph, set_db


def generate_questions(
    db: Session,
    user_id: int,
    mode: str,
    subject: str,
    knowledge_point: str,
    difficulty: str,
    question_type: str,
    count: int,
    recommendation_reason: str = "",
) -> dict:
    """生成考题，支持自由出题和智能推荐出题。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        mode: 模式（自由出题/智能推荐）。
        subject: 科目。
        knowledge_point: 知识点。
        difficulty: 难度。
        question_type: 题型。
        count: 题目数量。
        recommendation_reason: 推荐原因（智能推荐模式）。

    Returns:
        dict: 包含 session_id, questions, agent_steps, llm_used, llm_error。
    """
    set_db(db)
    initial_state = {
        "user_id": user_id,
        "mode": mode,
        "subject": subject,
        "knowledge_point": knowledge_point,
        "difficulty": difficulty,
        "question_type": question_type,
        "count": count,
        "context": [],
        "questions": [],
        "session_id": None,
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }

    result = get_question_graph().invoke(initial_state)

    steps_out = []
    for s in result.get("agent_steps", []):
        steps_out.append({
            "name": s.get("name", ""),
            "input_summary": s.get("input_summary", ""),
            "output_summary": s.get("output_summary", ""),
            "duration_ms": s.get("duration_ms", 0),
            "status": s.get("status", ""),
        })

    return {
        "session_id": result.get("session_id"),
        "config": result.get("config", ""),
        "questions": result.get("questions", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "agent_steps": steps_out,
    }
