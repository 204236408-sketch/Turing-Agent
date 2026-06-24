from sqlalchemy.orm import Session
from models import AnswerRecord, Question
from services.llm_service import chat_json
from services.mastery_service import recalculate_mastery
from utils.response import AppError


def _text_fill_match(user: str, std: str) -> bool:
    """Lenient text match for fill / essay questions."""
    import re
    u = re.sub(r"\s+", "", (user or "").lower())
    s = re.sub(r"\s+", "", (std or "").lower())
    if not u or not s:
        return False
    return u in s or s in u


def check_answer(db: Session, user_id: int, question_id: int, user_answer: str) -> dict:
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)
    _vt_map = {"选择题":"choice","填空题":"fill","简答题":"essay","综合题":"comprehensive"}
    vt = _vt_map.get(question.question_type, question.variant_type or "choice")
    if vt == "choice":
        normalized = (user_answer or "").strip().upper()[:1]
        is_correct = normalized == question.standard_answer.upper()
        options_display = question.options_json
    else:
        normalized = (user_answer or "").strip()
        is_correct = _text_fill_match(normalized, question.standard_answer or "")
        options_display = "无选项"
    fallback_feedback = (
        f"批改结果：{'回答正确' if is_correct else '回答错误'}。你的答案：{normalized or '未填写'}；"
        f"标准答案：{question.standard_answer}。{question.explanation}"
    )
    fallback = {
        "feedback": fallback_feedback,
        "suggested_error_types": [] if is_correct else ["概念理解错误", "表达不完整", "知识遗忘"],
    }
    llm = chat_json(
        [
            {"role": "system", "content": "你是考研 408 答题批改 Agent。只输出合法 JSON。"},
            {
                "role": "user",
                "content": f"""
题型：{vt}
题目：{question.question_text}
选项：{options_display}
用户答案：{normalized or '未填写'}
标准答案：{question.standard_answer}
解析：{question.explanation}
判定结果：{'正确' if is_correct else '错误'}

请输出：
{{
  "feedback": "面向学生的批改反馈，包含正误、标准答案、关键原因和下一步建议",
  "suggested_error_types": ["错误时给 1-3 个候选错因，正确则为空数组"]
}}
""",
            },
        ],
        fallback,
    )
    feedback_value = (llm.data or fallback).get("feedback") or fallback_feedback
    if isinstance(feedback_value, dict):
        feedback = "；".join(f"{key}：{value}" for key, value in feedback_value.items())
    elif isinstance(feedback_value, list):
        feedback = "；".join(str(item) for item in feedback_value)
    else:
        feedback = str(feedback_value)
    suggested_error_types = (llm.data or fallback).get("suggested_error_types") or fallback["suggested_error_types"]
    if isinstance(suggested_error_types, str):
        suggested_error_types = [suggested_error_types]
    record = AnswerRecord(
        user_id=user_id,
        question_id=question.id,
        subject=question.subject,
        knowledge_point=question.knowledge_point,
        user_answer=normalized,
        standard_answer=question.standard_answer,
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(record)
    db.flush()
    mastery = recalculate_mastery(db, user_id, question.subject, question.knowledge_point)
    return {
        "answer_record_id": record.id,
        "is_correct": is_correct,
        "feedback": feedback,
        "mastery": {
            "status": mastery.final_status,
            "weak_score": mastery.weak_score,
            "wrong_count": mastery.wrong_count,
        },
        "suggested_error_types": suggested_error_types,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
    }
