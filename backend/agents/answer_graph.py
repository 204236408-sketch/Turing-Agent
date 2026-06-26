from __future__ import annotations

import contextvars
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.graph_state import AnswerCheckState
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import AnswerRecord, Question
from services.llm_service import LLMResult, chat_json, chat_completion
from services.mastery_service import recalculate_mastery
from utils.response import AppError

logger = logging.getLogger("answer_graph")

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()

def _text_fill_match(user: str, std: str) -> bool:
    u = re.sub(r"\s+", "", (user or "").lower())
    s = re.sub(r"\s+", "", (std or "").lower())
    if not u or not s:
        return False
    return u in s or s in u


def load_question(state: AnswerCheckState) -> dict:
    db = _get_db()
    start = time.time()
    question_id = state.get("question_id", 0)

    question = db.query(Question).filter(Question.id == question_id).first() if db else None
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)

    meta = f"subject={question.subject}, kp={question.knowledge_point}, type={question.question_type}"
    step = _make_step("load_question", f"question_id={question_id}", meta, "success", start)
    return {
        "question": {
            "id": question.id,
            "subject": question.subject,
            "knowledge_point": question.knowledge_point,
            "question_type": question.question_type,
            "variant_type": question.variant_type,
            "question_text": question.question_text,
            "options_json": question.options_json or [],
            "standard_answer": question.standard_answer,
            "explanation": question.explanation,
        },
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def check_objective_answer(state: AnswerCheckState) -> dict:
    start = time.time()
    user_answer = state.get("user_answer", "")
    question = state.get("question", {})
    if not question:
        step = _make_step("check_objective_answer", "no question", "error: question not loaded", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    vt = question.get("variant_type") or "choice"
    standard = (question.get("standard_answer") or "").strip()

    if vt == "choice":
        normalized = (user_answer or "").strip().upper()[:1]
        is_correct = normalized == standard.upper()
    else:
        normalized = (user_answer or "").strip()
        is_correct = _text_fill_match(normalized, standard)

    out = f"vt={vt}, user='{normalized[:20]}', std='{standard[:20]}', correct={is_correct}"
    step = _make_step("check_objective_answer", f"user_answer='{user_answer[:30]}'", out, "success", start)
    return {
        "normalized_answer": normalized,
        "is_correct": is_correct,
        "score": 1.0 if is_correct else 0.0,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def llm_feedback_node(state: AnswerCheckState) -> dict:
    start = time.time()
    is_correct = state.get("is_correct", False)
    question = state.get("question", {})
    normalized = state.get("normalized_answer", "")

    fallback_text = (
        f"批改结果：{'回答正确' if is_correct else '回答错误'}。你的答案：{normalized or '未填写'}；"
        f"标准答案：{question.get('standard_answer', '')}。{question.get('explanation', '')}"
    )
    fallback = {
        "feedback": fallback_text,
        "suggested_error_types": [] if is_correct else ["概念理解错误", "表达不完整", "知识遗忘"],
    }

    vt = question.get("variant_type") or "choice"
    options_display = question.get("options_json", []) if vt == "choice" else "无选项"

    prompt = f"""
题型：{vt}
题目：{question.get('question_text', '')}
选项：{options_display}
用户答案：{normalized or '未填写'}
标准答案：{question.get('standard_answer', '')}
解析：{question.get('explanation', '')}
判定结果：{'正确' if is_correct else '错误'}

请输出：
{{
  "feedback": "面向学生的批改反馈，包含正误、标准答案、关键原因和下一步建议",
  "suggested_error_types": ["错误时给 1-3 个候选错因，正确则为空数组"]
}}
"""

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            chat_json,
            [
                {"role": "system", "content": "你是考研 408 答题批改 Agent。只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            fallback,
        )
        try:
            llm = future.result(timeout=_NODE_TIMEOUT)
        except FutureTimeout:
            pool.shutdown(wait=False)
            logger.error("[timeout] llm_feedback: LLM timed out after %ds", _NODE_TIMEOUT)
            llm = LLMResult(content="", used_llm=False, error=f"timed out after {_NODE_TIMEOUT}s", data=fallback)

    data = llm.data or fallback
    feedback_value = data.get("feedback") or fallback_text
    if isinstance(feedback_value, dict):
        feedback = "；".join(f"{k}：{v}" for k, v in feedback_value.items())
    elif isinstance(feedback_value, list):
        feedback = "；".join(str(item) for item in feedback_value)
    else:
        feedback = str(feedback_value)

    suggested = data.get("suggested_error_types") or fallback["suggested_error_types"]
    if isinstance(suggested, str):
        suggested = [suggested]

    step_status = "success" if llm.used_llm else "degraded"
    step = _make_step("llm_feedback", f"correct={is_correct}", f"feedback_len={len(feedback)}", step_status, start)
    return {
        "feedback": feedback,
        "suggested_error_types": suggested,
        "llm_result": llm,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def recommend_causes(state: AnswerCheckState) -> dict:
    start = time.time()
    question = state.get("question", {})
    is_correct = state.get("is_correct", False)
    suggested = state.get("suggested_error_types", [])

    db = _get_db()
    user_id = state.get("user_id", 0)
    subject = question.get("subject", "")
    knowledge_point = question.get("knowledge_point", "")

    causes = []
    if not is_correct:
        causes = list(suggested)
        if db and user_id and subject and knowledge_point:
            from models import Mistake
            recent = (
                db.query(Mistake)
                .filter(
                    Mistake.user_id == user_id,
                    Mistake.subject == subject,
                    Mistake.knowledge_point == knowledge_point,
                    Mistake.status == "active",
                )
                .order_by(Mistake.create_time.desc())
                .limit(20)
                .all()
            )
            if recent:
                from collections import Counter
                freq = Counter(m.error_type for m in recent if m.error_type)
                if freq:
                    top = freq.most_common(1)[0][0]
                    if top not in causes:
                        causes.append(top)

    out = f"causes={causes if not is_correct else '[]'}"
    step = _make_step("recommend_causes", f"correct={is_correct}, suggested={suggested}", out, "success", start)
    return {
        "recommended_causes": causes if not is_correct else [],
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def update_answer_record(state: AnswerCheckState) -> dict:
    db = _get_db()
    start = time.time()
    user_id = state.get("user_id", 0)
    question = state.get("question", {})
    is_correct = state.get("is_correct", False)
    normalized = state.get("normalized_answer", "")
    feedback = state.get("feedback", "")

    record = AnswerRecord(
        user_id=user_id,
        question_id=question.get("id", 0),
        subject=question.get("subject", ""),
        knowledge_point=question.get("knowledge_point", ""),
        user_answer=normalized,
        standard_answer=question.get("standard_answer", ""),
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(record)
    db.flush()

    # P2-8: 答题后自动更新题目质量分
    if db and question.get("id"):
        q = db.query(Question).filter(Question.id == question["id"]).first()
        if q:
            q.answer_count = (q.answer_count or 0) + 1
            if is_correct:
                q.correct_answer_count = (q.correct_answer_count or 0) + 1
            # 评分公式：种子题保持 100；其他题按正确率 + 答题数稳定性
            if q.source == "seed":
                q.quality_score = 100
            else:
                acc = (q.correct_answer_count or 0) / max(q.answer_count or 1, 1)
                stability = min(50, (q.answer_count or 0) * 5)  # 答题数越多置信度越高，封顶 50
                q.quality_score = max(0, min(100, int(acc * 50 + stability)))
            # 被答对 ≥ 2 次后可考虑提升为 verified（仅在本来 verify=True 的题，或累计答题 ≥ 3 且全对）
            if not q.is_verified and (q.answer_count or 0) >= 3 and (q.correct_answer_count or 0) == (q.answer_count or 0):
                q.is_verified = True

    out = f"record_id={record.id}, correct={is_correct}"
    step = _make_step("update_answer_record", f"user_id={user_id}", out, "success", start)
    return {
        "answer_record_id": record.id,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def update_mastery(state: AnswerCheckState) -> dict:
    db = _get_db()
    start = time.time()
    user_id = state.get("user_id", 0)
    question = state.get("question", {})
    subject = question.get("subject", "")
    knowledge_point = question.get("knowledge_point", "")

    mastery = recalculate_mastery(db, user_id, subject, knowledge_point) if db and user_id else None
    mastery_info = f"status={mastery.final_status}, weak_score={mastery.weak_score}" if mastery else "no mastery data"
    step = _make_step("update_mastery", f"subject={subject}, kp={knowledge_point}", mastery_info, "success", start)
    return {
        "mastery": {
            "status": mastery.final_status,
            "weak_score": mastery.weak_score,
            "wrong_count": mastery.wrong_count,
        } if mastery else {},
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_check(state: AnswerCheckState) -> dict:
    start = time.time()
    question = state.get("question", {})
    is_correct = state.get("is_correct", False)
    normalized = state.get("normalized_answer", "")

    feedback = (
        f"批改结果：{'回答正确' if is_correct else '回答错误'}。你的答案：{normalized or '未填写'}；"
        f"标准答案：{question.get('standard_answer', '')}。{question.get('explanation', '')}"
    )

    step = _make_step("fallback_check", f"correct={is_correct}", "template feedback used", "success", start)
    return {
        "is_correct": is_correct,
        "score": 1.0 if is_correct else 0.0,
        "feedback": feedback,
        "recommended_causes": [] if is_correct else ["概念理解错误", "知识遗忘"],
        "llm_used": False,
        "llm_error": "LLM feedback degraded, fallback_check used",
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def should_fallback(state: AnswerCheckState) -> Literal["fallback_check", "end"]:
    if not state.get("llm_used", True) and state.get("llm_error", ""):
        return "fallback_check"
    return "end"


def _build_answer_graph() -> StateGraph:
    workflow = StateGraph(AnswerCheckState)

    for name, fn in [
        ("load_question", load_question),
        ("check_objective_answer", check_objective_answer),
        ("llm_feedback", _with_timeout(llm_feedback_node)),
        ("recommend_causes", recommend_causes),
        ("update_answer_record", update_answer_record),
        ("update_mastery", update_mastery),
        ("fallback_check", fallback_check),
    ]:
        workflow.add_node(name, _safe_node(fn))

    workflow.set_entry_point("load_question")
    workflow.add_edge("load_question", "check_objective_answer")
    workflow.add_edge("check_objective_answer", "llm_feedback")
    workflow.add_edge("llm_feedback", "recommend_causes")
    workflow.add_edge("recommend_causes", "update_answer_record")
    workflow.add_edge("update_answer_record", "update_mastery")
    workflow.add_conditional_edges("update_mastery", should_fallback, {
        "fallback_check": "fallback_check",
        "end": END,
    })
    workflow.add_edge("fallback_check", END)

    return workflow.compile()


def get_answer_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_answer_graph()
    return _GRAPH
