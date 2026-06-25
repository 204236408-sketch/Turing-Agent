import json
from models import Question


def _ensure_list(value):
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return json.loads(value or "[]")
    return []


def question_to_dict(question: Question) -> dict:
    options = _ensure_list(question.options_json)
    hints = _ensure_list(question.hints_json)
    sub_questions = _ensure_list(question.sub_questions_json)
    return {
        "id": question.id,
        "question_id": question.id,
        "meta": f"2026 模拟 · 第 {question.id} 题 · 2 分",
        "subject": question.subject,
        "knowledge_point": question.knowledge_point,
        "difficulty": question.difficulty,
        "question_type": question.question_type,
        "variant_type": question.variant_type,
        "title": question.question_text,
        "question_text": question.question_text,
        "options": options,
        "sub_questions": sub_questions,
        "standard_answer": question.standard_answer,
        "explanation": question.explanation,
        "answer": f"标准答案：{question.standard_answer} · {question.explanation}",
        "hints": hints,
        "hint": hints[0] if hints else "先定位知识点，再按步骤分析。",
        "reason": question.recommend_reason,
        "recommend_reason": question.recommend_reason,
    }
