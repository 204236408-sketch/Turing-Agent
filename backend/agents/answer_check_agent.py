from __future__ import annotations

from sqlalchemy.orm import Session

from agents.answer_graph import get_answer_graph, set_db


def check_answer(db: Session, user_id: int, question_id: int, user_answer: str) -> dict:
    """批改用户答案，返回判分、反馈和推荐错因。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        question_id: 题目 ID。
        user_answer: 用户提交的答案。

    Returns:
        dict: 包含 is_correct, feedback, suggested_error_types, agent_steps, llm_used, llm_error。
    """
    set_db(db)
    initial_state = {
        "user_id": user_id,
        "question_id": question_id,
        "user_answer": user_answer,
        "question": {},
        "is_correct": False,
        "score": 0.0,
        "feedback": {},
        "recommended_causes": [],
        "answer_record_id": None,
        "mastery": {},
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }

    result = get_answer_graph().invoke(initial_state)

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
        "answer_record_id": result.get("answer_record_id"),
        "is_correct": result.get("is_correct", False),
        "feedback": result.get("feedback", ""),
        "mastery": result.get("mastery", {}),
        "suggested_error_types": result.get("recommended_causes", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "agent_steps": steps_out,
    }
