from __future__ import annotations

from sqlalchemy.orm import Session

from agents.mistake_graph import get_mistake_graph, set_db
from models import Mistake, UserMemory
from services.llm_service import chat_json_with_fallback_models
from services.mastery_service import recalculate_mastery
from services.chroma_service import upsert_document
from config import settings


def confirm_cause(
    db: Session,
    user_id: int,
    answer_record_id: int,
    error_types: list[str],
    user_note: str,
    evidence_source: str,
    agent_suggested_types: list[str] | None = None,
) -> dict:
    """确认错因，写入错题本、长期记忆并更新掌握度。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        answer_record_id: 答题记录 ID。
        error_types: 错因类型列表。
        user_note: 用户备注。
        evidence_source: 证据来源。
        agent_suggested_types: Agent 建议的错因类型（可选）。

    Returns:
        dict: 包含 mistake_id, mastery_status, agent_steps, llm_used, llm_error。
    """
    set_db(db)
    initial_state = {
        "user_id": user_id,
        "answer_record_id": answer_record_id,
        "error_types": error_types or agent_suggested_types or [],
        "user_note": user_note,
        "evidence_source": evidence_source,
        "agent_suggested_types": agent_suggested_types or [],
        "mistake_id": None,
        "memory_id": None,
        "similar_mistakes": [],
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }

    result = get_mistake_graph().invoke(initial_state)

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
        "mistake_id": result.get("mistake_id"),
        "message": f"已写入错题、长期记忆和知识点掌握状态。",
        "mastery_status": result.get("mastery_status", ""),
        "weak_score": result.get("weak_score", 0),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "agent_steps": steps_out,
    }


def analyze_ocr_text(
    db: Session,
    user_id: int,
    text: str,
    subject: str,
    knowledge_point: str,
    user_answer: str = "",
) -> dict:
    """分析 OCR 识别文本，推断答案、生成错因并写入系统。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        text: OCR 识别文本。
        subject: 科目。
        knowledge_point: 知识点。
        user_answer: 用户填写的答案。

    Returns:
        dict: 包含 mistake_id, memory_id, analysis, llm_used, llm_error。
    """
    fallback = {
        "subject": subject,
        "knowledge_point": knowledge_point,
        "question_summary": text[:120],
        "correct_answer": "AI 未能可靠推断标准答案，请根据题目条件人工校对。",
        "answer_explanation": "OCR 文本信息不足或大模型暂不可用，系统已先保存错题并等待后续校正。",
        "is_correct": False if user_answer else None,
        "possible_causes": ["审题错误", "知识点掌握不稳", "答案待校对"],
        "error_type": "OCR 导入待确认",
        "error_reason": "已导入 OCR 错题，标准答案由 Agent 推断失败或待人工校对。",
        "suggestion": "先校对 OCR 文本和自己的答案，再围绕该知识点完成同类训练。",
        "memory_content": f"OCR 导入错题涉及 {knowledge_point}，需要校对题干并复盘自己的作答过程。",
    }
    llm = chat_json_with_fallback_models(
        [
            {
                "role": "system",
                "content": (
                    "你是考研 408 OCR 错题分析 Agent。根据 OCR 题干和用户答案，"
                    "自行推断标准答案、判断用户是否答错、分析错因并生成复习建议。只输出合法 JSON。"
                ),
            },
            {
                "role": "user",
                "content": f"""
OCR 识别文本：{text}
前端初步科目：{subject}
前端初步知识点：{knowledge_point}
用户答案：{user_answer or "未填写"}

请输出：
{{
  "subject": "可修正后的科目",
  "knowledge_point": "可修正后的知识点",
  "question_summary": "用一句话概括题目",
  "correct_answer": "你推断出的标准答案，含必要单位或选项",
  "answer_explanation": "推导或解析过程",
  "is_correct": false,
  "possible_causes": ["可能错因1", "可能错因2"],
  "error_type": "最主要错因类型",
  "error_reason": "结合用户答案和标准答案的具体错因分析",
  "suggestion": "可执行复习建议",
  "memory_content": "适合写入长期学习记忆的一句话"
}}
""",
            },
        ],
        fallback,
        models=[settings.siliconflow_model, "Qwen/Qwen2.5-14B-Instruct"],
    )
    data = llm.data or fallback
    resolved_subject = data.get("subject") or subject
    resolved_point = data.get("knowledge_point") or knowledge_point
    correct_answer = data.get("correct_answer") or fallback["correct_answer"]
    answer_explanation = data.get("answer_explanation") or fallback["answer_explanation"]
    possible_causes = data.get("possible_causes") or fallback["possible_causes"]
    error_type = data.get("error_type") or "OCR 导入待确认"
    error_reason = data.get("error_reason") or fallback["error_reason"]
    suggestion = data.get("suggestion") or fallback["suggestion"]
    memory_content = data.get("memory_content") or fallback["memory_content"]
    mistake = Mistake(
        user_id=user_id,
        subject=resolved_subject,
        knowledge_point=resolved_point,
        error_type=error_type,
        error_reason=(
            f"从图片识别到题目：{text[:300]}"
            f"\n用户答案：{user_answer or '未填写'}"
            f"\nAgent 推断标准答案：{correct_answer}"
            f"\n答案解析：{answer_explanation}"
            f"\n错因分析：{error_reason}"
        ),
        suggestion=suggestion,
        input_type="PaddleOCR",
    )
    db.add(mistake)
    db.flush()
    memory = UserMemory(
        user_id=user_id,
        memory_type="weak_point",
        subject=resolved_subject,
        knowledge_point=resolved_point,
        content=memory_content,
        evidence=f"ocr_mistake:{mistake.id}",
    )
    db.add(memory)
    db.flush()

    upsert_document(
        "mistake_summary",
        f"ocr_mistake_{mistake.id}",
        f"[{resolved_subject}/{resolved_point}] OCR 错因：{error_type}。分析：{error_reason}。建议：{suggestion}",
        {
            "subject": resolved_subject,
            "knowledge_point": resolved_point,
            "error_type": error_type,
            "mistake_id": mistake.id,
            "source": "ocr",
        },
    )

    mastery = recalculate_mastery(db, user_id, resolved_subject, resolved_point)
    db.flush()
    return {
        "mistake_id": mistake.id,
        "memory_id": memory.id,
        "recognized_text": text,
        "analysis": {
            "subject": resolved_subject,
            "knowledge_point": resolved_point,
            "question_summary": data.get("question_summary") or fallback["question_summary"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "answer_explanation": answer_explanation,
            "is_correct": data.get("is_correct"),
            "possible_causes": possible_causes,
            "error_type": error_type,
            "error_reason": error_reason,
            "suggestion": mistake.suggestion,
            "mastery_status": mastery.final_status,
        },
        "message": "已提交错题分析 Agent，并写入错题、长期记忆和知识点掌握状态。",
        "llm_used": llm.used_llm,
        "llm_model": (llm.data or {}).get("_llm_model") if isinstance(llm.data, dict) else "",
        "llm_error": llm.error,
    }
