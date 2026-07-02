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
    scope: str = "",
    chapter: str = "",
    chapter_id: int | None = None,
    reference_text: str = "",
    reference_answer: str = "",
    source: str = "manual",
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
        scope: 出题范围，point/chapter；为空时自动推断。
        chapter: 章节训练时的章节名。
        chapter_id: 章节训练时的章节 ID。
        reference_text: OCR 错题场景下携带的原始识别文本（用作 LLM 出题参考）
        reference_answer: OCR 错题场景下 Agent 推断的标准答案（用作 LLM 出题参考）
        source: 出题来源 manual/ocr/smart/weak_kp

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
        "scope": scope or "",
        "chapter": chapter or "",
        "chapter_id": chapter_id,
        "prompt_knowledge_point": "",
        "target_points": [],
        "context": [],
        "questions": [],
        "session_id": None,
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
        "reference_text": reference_text or "",
        "reference_answer": reference_answer or "",
        "source": source or "manual",
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
        "all_refused": bool(result.get("all_refused", False)),
        "agent_steps": steps_out,
    }
