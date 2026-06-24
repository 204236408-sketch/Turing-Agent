from sqlalchemy.orm import Session
from models import AnswerRecord, Mistake, UserMemory
from config import settings
from services.llm_service import chat_json, chat_json_with_fallback_models
from services.mastery_service import recalculate_mastery
from utils.response import AppError


def confirm_cause(
    db: Session,
    user_id: int,
    answer_record_id: int,
    error_types: list[str],
    user_note: str,
    evidence_source: str,
) -> dict:
    record = db.query(AnswerRecord).filter(AnswerRecord.id == answer_record_id, AnswerRecord.user_id == user_id).first()
    if not record:
        raise AppError("ANSWER_RECORD_NOT_FOUND", "答题记录不存在", status_code=404)
    error_type = "、".join(error_types) if error_types else "未确认"
    reason = user_note or f"用户确认错因为：{error_type}"
    fallback = {
        "error_reason": reason,
        "suggestion": f"围绕 {record.knowledge_point} 做 3 道同类题，并复述解题规则。",
        "memory_content": f"{record.knowledge_point} 反复出现 {error_type}，复习时要先列规则再计算。",
    }
    llm = chat_json_with_fallback_models(
        [
            {"role": "system", "content": "你是考研 408 错题分析与长期记忆 Agent。只输出合法 JSON。"},
            {
                "role": "user",
                "content": f"""
科目：{record.subject}
知识点：{record.knowledge_point}
用户答案：{record.user_answer}
标准答案：{record.standard_answer}
批改反馈：{record.feedback}
用户确认错因：{error_type}
用户补充说明：{user_note}

请输出：
{{
  "error_reason": "具体错因分析",
  "suggestion": "可执行复习建议",
  "memory_content": "适合写入长期学习记忆的一句话"
}}
""",
            },
        ],
        fallback,
        models=[settings.siliconflow_model, "Qwen/Qwen2.5-14B-Instruct"],
        max_tokens=1800,
    )
    data = llm.data or fallback
    mistake = Mistake(
        user_id=user_id,
        answer_record_id=record.id,
        question_id=record.question_id,
        subject=record.subject,
        knowledge_point=record.knowledge_point,
        error_type=error_type,
        error_reason=data.get("error_reason") or reason,
        suggestion=data.get("suggestion") or fallback["suggestion"],
        input_type=evidence_source,
    )
    db.add(mistake)
    db.flush()
    db.add(
        UserMemory(
            user_id=user_id,
            memory_type="weak_point",
            subject=record.subject,
            knowledge_point=record.knowledge_point,
            content=data.get("memory_content") or fallback["memory_content"],
            evidence=f"answer_record:{record.id};mistake:{mistake.id}",
        )
    )
    mastery = recalculate_mastery(db, user_id, record.subject, record.knowledge_point)
    return {
        "mistake_id": mistake.id,
        "message": f"已写入错题、长期记忆和 {record.knowledge_point} 的掌握状态。",
        "mastery_status": mastery.final_status,
        "weak_score": mastery.weak_score,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
    }


def analyze_ocr_text(
    db: Session,
    user_id: int,
    text: str,
    subject: str,
    knowledge_point: str,
    user_answer: str = "",
) -> dict:
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
    mastery_seed = recalculate_mastery(db, user_id, resolved_subject, resolved_point)
    mastery_seed.user_mark_status = "不会"
    db.flush()
    mastery = recalculate_mastery(db, user_id, resolved_subject, resolved_point)
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
