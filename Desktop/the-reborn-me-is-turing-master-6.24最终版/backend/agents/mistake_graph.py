from __future__ import annotations

import contextvars
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Literal

from langgraph.graph import StateGraph
from sqlalchemy.orm import Session

from agents.graph_state import MistakeState
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import AnswerRecord, Mistake, UserMemory
from services.llm_service import LLMResult, chat_json, chat_json_with_fallback_models
from services.mastery_service import recalculate_mastery
from services.chroma_service import upsert_document
from utils.response import AppError

logger = logging.getLogger("mistake_graph")

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()

def load_answer_record(state: MistakeState) -> dict:
    db = _get_db()
    start = time.time()
    answer_record_id = state.get("answer_record_id", 0)
    user_id = state.get("user_id", 0)

    record = db.query(AnswerRecord).filter(
        AnswerRecord.id == answer_record_id,
        AnswerRecord.user_id == user_id,
    ).first() if db else None

    if not record:
        raise AppError("ANSWER_RECORD_NOT_FOUND", "答题记录不存在", status_code=404)

    meta = f"subject={record.subject}, kp={record.knowledge_point}, correct={record.is_correct}"
    step = _make_step("load_answer_record", f"record_id={answer_record_id}", meta, "success", start)
    return {
        "_record": record,
        "_record_subject": record.subject,
        "_record_kp": record.knowledge_point,
        "_record_user_answer": record.user_answer,
        "_record_std_answer": record.standard_answer,
        "_record_feedback": record.feedback,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def analyze_error(state: MistakeState) -> dict:
    start = time.time()
    error_types = state.get("error_types", [])
    user_note = state.get("user_note", "")
    record = state.get("_record")
    evidence_source = state.get("_evidence_source", "系统出题")

    if not record:
        step = _make_step("analyze_error", "no record", "error: record not loaded", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    error_type = "、".join(error_types) if error_types else "未确认"
    reason = user_note or f"用户确认错因为：{error_type}"

    fallback = {
        "error_reason": reason,
        "suggestion": f"围绕 {record.knowledge_point} 做 3 道同类题，并复述解题规则。",
        "memory_content": f"{record.knowledge_point} 反复出现 {error_type}，复习时要先列规则再计算。",
    }

    prompt = f"""
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
"""

    llm = chat_json_with_fallback_models(
        [
            {"role": "system", "content": "你是考研 408 错题分析与长期记忆 Agent。只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        fallback,
        models=[settings.siliconflow_model, "Qwen/Qwen2.5-14B-Instruct"],
        max_tokens=1800,
    )

    data = llm.data or fallback
    step_status = "success" if llm.used_llm else "degraded"
    step = _make_step("analyze_error", f"error_types={error_type}", f"analysis done", step_status, start)
    return {
        "_error_type": error_type,
        "_error_reason": data.get("error_reason") or reason,
        "_suggestion": data.get("suggestion") or fallback["suggestion"],
        "_memory_content": data.get("memory_content") or fallback["memory_content"],
        "_llm": llm,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def write_mistake(state: MistakeState) -> dict:
    db = _get_db()
    start = time.time()
    record = state.get("_record")
    user_id = state.get("user_id", 0)
    error_type = state.get("_error_type", "未确认")
    error_reason = state.get("_error_reason", "")
    suggestion = state.get("_suggestion", "")
    evidence_source = state.get("_evidence_source", "系统出题")

    if not record:
        step = _make_step("write_mistake", "no record", "error", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    mistake = Mistake(
        user_id=user_id,
        answer_record_id=record.id,
        question_id=record.question_id,
        subject=record.subject,
        knowledge_point=record.knowledge_point,
        error_type=error_type,
        error_reason=error_reason,
        suggestion=suggestion,
        input_type=evidence_source,
    )
    db.add(mistake)
    db.flush()

    out = f"mistake_id={mistake.id}, kp={record.knowledge_point}"
    step = _make_step("write_mistake", f"error_type={error_type}", out, "success", start)
    return {
        "mistake_id": mistake.id,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def write_memory(state: MistakeState) -> dict:
    db = _get_db()
    start = time.time()
    record = state.get("_record")
    user_id = state.get("user_id", 0)
    memory_content = state.get("_memory_content", "")
    mistake_id = state.get("mistake_id", 0)

    if not record:
        step = _make_step("write_memory", "no record", "error", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    memory = UserMemory(
        user_id=user_id,
        memory_type="weak_point",
        subject=record.subject,
        knowledge_point=record.knowledge_point,
        content=memory_content,
        evidence=f"answer_record:{record.id};mistake:{mistake_id}",
    )
    db.add(memory)
    db.flush()

    out = f"memory_id={memory.id}"
    step = _make_step("write_memory", f"content='{memory_content[:30]}'", out, "success", start)
    return {
        "memory_id": memory.id,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def write_chroma_summary(state: MistakeState) -> dict:
    start = time.time()
    record = state.get("_record")
    error_type = state.get("_error_type", "")
    error_reason = state.get("_error_reason", "")
    suggestion = state.get("_suggestion", "")
    mistake_id = state.get("mistake_id", 0)

    if not record:
        step = _make_step("write_chroma_summary", "no record", "error", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    summary_text = f"[{record.subject}/{record.knowledge_point}] 错因：{error_type}。分析：{error_reason}。建议：{suggestion}"
    chroma_result = upsert_document(
        "mistake_summary",
        f"mistake_{mistake_id}",
        summary_text,
        {
            "subject": record.subject,
            "knowledge_point": record.knowledge_point,
            "error_type": error_type,
            "mistake_id": mistake_id,
        },
    )

    stored = chroma_result.get("stored", False)
    status = "success" if stored else "degraded"
    step = _make_step("write_chroma_summary", f"mistake_id={mistake_id}", f"chroma_stored={stored}", status, start)
    return {
        "_chroma_stored": stored,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def recommend_retrain(state: MistakeState) -> dict:
    db = _get_db()
    start = time.time()
    record = state.get("_record")
    user_id = state.get("user_id", 0)

    if not record:
        step = _make_step("recommend_retrain", "no record", "error", "failed", start)
        return {"agent_steps": state.get("agent_steps", []) + [step]}

    mastery = recalculate_mastery(db, user_id, record.subject, record.knowledge_point) if db else None
    status_info = f"mastery={mastery.final_status}, weak_score={mastery.weak_score}" if mastery else "no mastery"

    step = _make_step("recommend_retrain", f"kp={record.knowledge_point}", status_info, "success", start)
    return {
        "mastery_status": mastery.final_status if mastery else "",
        "weak_score": mastery.weak_score if mastery else 0,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _build_mistake_graph() -> StateGraph:
    workflow = StateGraph(MistakeState)

    for name, fn in [
        ("load_answer_record", load_answer_record),
        ("analyze_error", _with_timeout(analyze_error)),
        ("write_mistake", write_mistake),
        ("write_memory", write_memory),
        ("write_chroma_summary", write_chroma_summary),
        ("recommend_retrain", recommend_retrain),
    ]:
        workflow.add_node(name, _safe_node(fn))

    workflow.set_entry_point("load_answer_record")
    workflow.add_edge("load_answer_record", "analyze_error")
    workflow.add_edge("analyze_error", "write_mistake")
    workflow.add_edge("write_mistake", "write_memory")
    workflow.add_edge("write_memory", "write_chroma_summary")
    workflow.add_edge("write_chroma_summary", "recommend_retrain")
    workflow.add_edge("recommend_retrain", "__end__")

    return workflow.compile()


def get_mistake_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_mistake_graph()
    return _GRAPH
