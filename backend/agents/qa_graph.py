from __future__ import annotations

import contextvars
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Literal

<<<<<<< HEAD
from langgraph.graph import StateGraph, END
=======
from langgraph.graph import END, StateGraph
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
from sqlalchemy.orm import Session

from agents.graph_state import QAState
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import KnowledgeMastery
from prompts.qa_prompt import QA_SYSTEM_PROMPT, QA_USER_TEMPLATE
from services.chroma_service import query_documents
from services.knowledge_heuristics import infer_all
from services.llm_service import LLMResult, chat_completion
<<<<<<< HEAD
from services.rag_service import retrieve_knowledge as mysql_retrieve_knowledge, retrieve_user_memory
=======
from services.rag_service import retrieve_knowledge as hybrid_retrieve
from services.rag_service import retrieve_user_memory
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)

logger = logging.getLogger("qa_graph")

_FOLLOWUP_TRIGGERS = {
<<<<<<< HEAD
    "为什么", "然后", "所以", "举个例子", "再说一遍", "那呢", "还有", "具体",
    "凭什么", "原理是什么", "底层逻辑", "本质是啥", "关键点在哪", "核心区别",
    "详细说", "拆解一下", "分步骤讲", "逐条分析", "展开说说", "细化讲解",
    "区别在哪", "相同点", "对比一下", "什么时候用A什么时候用B",
    "给道题", "真题示例", "计算演示", "手写步骤", "实操流程",
    "错在哪", "易错点", "怎么避免", "正确思路", "误区是什么",
    "除此之外", "补充一点", "延伸知识", "拓展一下", "另外",
    "没听懂", "重新讲", "换个说法", "通俗点讲", "简单概括",
    "会导致什么", "后果是什么", "最终结果", "因此呢",
    "那如果", "要是换个情况", "反过来呢", "假如",
    "考不考", "分值多少", "怎么考", "答题模板", "背诵要点",
    "怎么理解", "如何实现", "有什么用", "适用场景",
}
_REJECTION_PATTERNS = re.compile(r"抱歉|对不起|无法回答|不清楚|不知道|我不确定|没有相关信息", re.IGNORECASE)

_CHROMA_SCORE_THRESHOLD = 0.5
=======
    "为什么",
    "然后",
    "所以",
    "举个例子",
    "再说一遍",
    "具体",
    "详细",
    "区别",
    "对比",
    "怎么理解",
    "如何实现",
    "还有",
    "补充",
}
_REJECTION_PATTERNS = re.compile(
    r"抱歉|对不起|无法回答|不清楚|不知道|我不确定|没有相关信息",
    re.IGNORECASE,
)

_CHROMA_SCORE_THRESHOLD = 0.5
_LOW_CONFIDENCE_THRESHOLD = 0.25
_MEDIUM_CONFIDENCE_THRESHOLD = 0.45
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()


<<<<<<< HEAD
=======
def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _source_id(index: int) -> str:
    return f"S{index + 1}"


def _normalize_evidence_item(item: dict, index: int, default_subject: str, default_kp: str) -> dict:
    content = str(item.get("content") or item.get("text") or "").strip()
    score = _as_float(item.get("rerank_score", item.get("fusion_score", item.get("score", 0))))
    subject = item.get("subject") or default_subject or "408"
    knowledge_point = item.get("knowledge_point") or item.get("section") or default_kp or ""
    return {
        **item,
        "source_id": item.get("source_id") or _source_id(index),
        "subject": subject,
        "knowledge_point": knowledge_point,
        "content": content,
        "score": score,
        "source": item.get("source", "unknown"),
        "content_preview": content[:180],
    }


def _build_retrieval_meta(items: list[dict], vector_count: int, keyword_count: int, fallback: bool) -> dict:
    best_score = max((_as_float(item.get("score")) for item in items), default=0.0)
    if not items:
        confidence = "none"
        grounded = False
        warning = "未检索到可用知识库证据，回答已进入谨慎降级。"
    elif best_score < _LOW_CONFIDENCE_THRESHOLD:
        confidence = "low"
        grounded = False
        warning = "检索证据相关性较低，回答不会断言超出证据的内容。"
    elif best_score < _MEDIUM_CONFIDENCE_THRESHOLD:
        confidence = "medium"
        grounded = True
        warning = "检索证据可用但置信度中等，建议结合教材或真题再核对。"
    else:
        confidence = "high"
        grounded = True
        warning = ""

    return {
        "confidence": confidence,
        "grounded": grounded,
        "best_score": round(best_score, 4),
        "vector_count": vector_count,
        "keyword_count": keyword_count,
        "fallback": fallback,
        "warning": warning,
        "sources": [
            {
                "source_id": item.get("source_id"),
                "source": item.get("source"),
                "subject": item.get("subject"),
                "knowledge_point": item.get("knowledge_point"),
                "score": round(_as_float(item.get("score")), 4),
                "preview": item.get("content_preview", ""),
            }
            for item in items[:5]
        ],
    }


>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
def detect_intent(state: QAState) -> dict:
    question = state.get("question", "")
    q_lower = question.strip().lower()

    is_followup = False
    if len(question) < 10:
        is_followup = True
<<<<<<< HEAD
    elif any(w in q_lower for w in _FOLLOWUP_TRIGGERS):
        is_followup = True
    elif question.startswith(("那", "这")):
=======
    elif any(word in q_lower for word in _FOLLOWUP_TRIGGERS):
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        is_followup = True

    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")

    if is_followup and not subject:
<<<<<<< HEAD
        history = state.get("history", [])
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("subject"):
                subject = msg["subject"]
                knowledge_point = msg.get("knowledge_point", "")
                break
        else:
            for msg in reversed(history):
                if msg.get("role") == "user":
                    inferred = infer_all(msg.get("content", ""))
                    if inferred["subject"]:
                        subject = inferred["subject"]
                        knowledge_point = inferred["knowledge_point"]
                        break
=======
        for msg in reversed(state.get("history", [])):
            content = msg.get("content", "")
            if msg.get("role") in {"user", "assistant"} and content:
                inferred = infer_all(content)
                if inferred["subject"]:
                    subject = inferred["subject"]
                    knowledge_point = knowledge_point or inferred["knowledge_point"]
                    break
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)

    if not subject:
        inferred = infer_all(question)
        subject = inferred["subject"] or "408"
        knowledge_point = knowledge_point or inferred["knowledge_point"]

    if not knowledge_point:
        knowledge_point = infer_all(question).get("knowledge_point", "")

<<<<<<< HEAD
    step = _make_step("detect_intent", question, f"subject={subject}, kp={knowledge_point}, followup={is_followup}", "success", time.time())
    logger.info("intent: subject=%s kp=%s followup=%s", subject, knowledge_point, is_followup)
=======
    step = _make_step(
        "detect_intent",
        question,
        f"subject={subject}, kp={knowledge_point}, followup={is_followup}",
        "success",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return {
        "subject": subject,
        "knowledge_point": knowledge_point,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def load_history(state: QAState) -> dict:
    history = state.get("history", [])
<<<<<<< HEAD
    step = _make_step("load_history", f"history_size={len(history)}", f"loaded {len(history)} messages", "success", time.time())
=======
    step = _make_step(
        "load_history",
        f"history_size={len(history)}",
        f"loaded {len(history)} messages",
        "success",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return {
        "history": history,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


<<<<<<< HEAD
=======
def retrieve_seed_questions(state: QAState) -> list[dict]:
    question = state.get("question", "")
    subject = state.get("subject", "")
    result = query_documents("seed_questions_vector", question, limit=2, where={"subject": subject} if subject else None)
    out = []
    for item in result.get("items", []):
        if not isinstance(item, dict):
            continue
        meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        out.append({
            "question_text": item.get("text", ""),
            "subject": meta.get("subject", subject),
            "knowledge_point": meta.get("knowledge_point", ""),
            "score": item.get("score", 0),
        })
    return out


>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
def retrieve_knowledge_node(state: QAState) -> dict:
    question = state.get("question", "")
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    db = _get_db()

    where = {}
    if subject:
        where["subject"] = subject
    if knowledge_point:
        where["knowledge_point"] = knowledge_point

    result = query_documents("knowledge_base_408", question, limit=3, where=where if where else None)
    chroma_items = result.get("items", [])
<<<<<<< HEAD
    fallback = result.get("fallback", False)

    retrieved = []
    chroma_score_max = 0.0
    if chroma_items:
        for item in chroma_items:
            if not isinstance(item, dict):
                continue
            score = item.get("score", 0)
            chroma_score_max = max(chroma_score_max, score)
            meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
            retrieved.append({
=======
    fallback = bool(result.get("fallback", False))

    retrieved: list[dict] = []
    chroma_score_max = 0.0
    for item in chroma_items:
        if not isinstance(item, dict):
            continue
        score = _as_float(item.get("score"))
        chroma_score_max = max(chroma_score_max, score)
        meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
        retrieved.append(
            {
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
                "subject": meta.get("subject", subject),
                "knowledge_point": meta.get("knowledge_point", knowledge_point),
                "content": item.get("text", ""),
                "score": score,
                "source": "chromadb",
<<<<<<< HEAD
            })

    needs_mysql = not chroma_items or chroma_score_max < _CHROMA_SCORE_THRESHOLD
    mysql_count = 0
    if needs_mysql and db:
        mysql_result = mysql_retrieve_knowledge(db, question, limit=3)
        mysql_items = mysql_result.get("items", []) if isinstance(mysql_result, dict) else []
        if mysql_items:
            existing_ids = {r.get("content", "")[:80] for r in retrieved}
            for m in mysql_items:
                if not isinstance(m, dict):
                    continue
                content = m.get("content", "")
                if content[:80] not in existing_ids:
                    m["source"] = m.get("source", "mysql")
                    retrieved.append(m)
                    existing_ids.add(content[:80])
                    mysql_count += 1

    out = f"ChromaDB: {len(chroma_items)} items, max_score={chroma_score_max:.2f}" + (f", MySQL: {mysql_count}" if db else "")
    step = _make_step("retrieve_knowledge", f"query={question[:40]}", out, "success", time.time())
    return {
        "retrieved_knowledge": retrieved,
=======
            }
        )

    mysql_count = 0
    needs_keyword_fallback = not chroma_items or chroma_score_max < _CHROMA_SCORE_THRESHOLD
    if needs_keyword_fallback and db:
        keyword_result = hybrid_retrieve(
            db,
            question,
            limit=3,
            subject_filter=subject or None,
            kp_filter=knowledge_point or None,
        )
        existing = {item.get("content", "")[:120] for item in retrieved}
        for item in keyword_result.get("items", []):
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or "")
            if content[:120] in existing:
                continue
            item["source"] = item.get("source", "mysql")
            retrieved.append(item)
            existing.add(content[:120])
            mysql_count += 1

    seed = retrieve_seed_questions(state)
    normalized = [
        _normalize_evidence_item(item, index, subject, knowledge_point)
        for index, item in enumerate(retrieved)
        if str(item.get("content") or item.get("text") or "").strip()
    ]
    retrieval = _build_retrieval_meta(normalized, len(chroma_items), mysql_count, fallback)
    step = _make_step(
        "retrieve_knowledge",
        f"query={question[:40]}",
        (
            f"ChromaDB: {len(chroma_items)} items, max_score={chroma_score_max:.2f}, "
            f"MySQL: {mysql_count}, confidence={retrieval['confidence']}"
        ),
        "success" if retrieval["grounded"] else "warning",
        time.time(),
    )
    return {
        "retrieved_knowledge": normalized,
        "seed_questions": seed,
        "retrieval": retrieval,
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_memory(state: QAState) -> dict:
    user_id = state.get("user_id", 0)
    db = _get_db()
<<<<<<< HEAD
    memories = []
    if db and user_id:
        memories = retrieve_user_memory(db, user_id, state.get("question", ""), limit=3)
    out = f"memories={len(memories)}" if memories else "no memories"
    step = _make_step("retrieve_memory", f"user_id={user_id}", out, "success", time.time())
=======
    memories = retrieve_user_memory(db, user_id, state.get("question", ""), limit=3) if db and user_id else []
    step = _make_step(
        "retrieve_memory",
        f"user_id={user_id}",
        f"memories={len(memories)}" if memories else "no memories",
        "success",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return {
        "memories_used": memories,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def load_mastery(state: QAState) -> dict:
    db = _get_db()
    mastery = {}
    if db and state.get("user_id") and state.get("subject") and state.get("knowledge_point"):
        row = (
            db.query(KnowledgeMastery)
            .filter(
                KnowledgeMastery.user_id == state["user_id"],
                KnowledgeMastery.subject == state["subject"],
                KnowledgeMastery.knowledge_point == state["knowledge_point"],
            )
            .first()
        )
        if row:
            mastery = {
                "status": row.final_status,
                "correct_rate": round(row.correct_count / max(row.total_answer_count, 1), 2),
                "weak_score": row.weak_score,
            }
<<<<<<< HEAD
    step = _make_step("load_mastery", f"kp={state.get('knowledge_point','')}", f"mastery={mastery}", "success", time.time())
=======
    step = _make_step(
        "load_mastery",
        f"kp={state.get('knowledge_point', '')}",
        f"mastery={mastery}",
        "success",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return {
        "mastery": mastery,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


<<<<<<< HEAD
=======
def _format_knowledge_text(retrieved: list[dict]) -> str:
    return "\n\n".join(
        (
            f"[{item.get('source_id', 'S?')}] "
            f"({item.get('subject', '')}/{item.get('knowledge_point', '')}; "
            f"source={item.get('source', 'unknown')}; score={_as_float(item.get('score')):.3f})\n"
            f"{item.get('content', '')}"
        )
        for item in retrieved
    )


def _cautious_answer(question: str, subject: str, knowledge_point: str, warning: str) -> str:
    kp = knowledge_point or "综合知识"
    return (
        f"<b>检索结论：</b>当前知识库没有找到足够可信的证据来直接回答“{question}”。<br>"
        f"<b>已定位：</b>{subject} / {kp}。<br>"
        f"<b>风险提示：</b>{warning or '证据不足，避免生成没有来源支撑的结论。'}<br>"
        "<b>建议：</b>请补充完整题干、选项或关键术语；也可以先查看该知识点的基础定义、典型题型和易错点。"
    )


>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
def generate_answer_node(state: QAState) -> dict:
    question = state.get("question", "")
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    retrieved = state.get("retrieved_knowledge", [])
<<<<<<< HEAD
=======
    retrieval = state.get("retrieval", {})
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    memories = state.get("memories_used", [])
    mastery = state.get("mastery", {})
    history = state.get("history", [])

<<<<<<< HEAD
    knowledge_text = "\n".join([f"[{r.get('subject','')}/{r.get('knowledge_point','')}] {r.get('content','')}" for r in retrieved])
    memory_text = "\n".join([m.get("content", "") for m in memories]) if memories else "暂无强相关长期记忆。"
    mastery_text = f"掌握度: {mastery.get('status','未知')}, 正确率: {mastery.get('correct_rate',0)}" if mastery else "暂无掌握度数据。"
    history_lines = [f"{m.get('role','')}: {m.get('content','')}" for m in history[-4:]]
    history_section = f"\n近期对话：\n" + "\n".join(history_lines) if history_lines else ""

    fallback_answer = (
        f"<b>定位：</b>{subject} · {knowledge_point}。<br>"
        f"<b>解释：</b>{retrieved[0]['content'][:200] if retrieved else '先明确概念，再按题目条件逐步推导。'}<br>"
        f"<b>结合你的画像：</b>{memory_text}<br>"
        "建议立刻做 1 道同知识点中等难度选择题，把理解转成可检验的结果。"
=======
    if not retrieval.get("grounded", False):
        content = _cautious_answer(question, subject, knowledge_point, retrieval.get("warning", ""))
        step = _make_step(
            "generate_answer",
            f"question='{question[:30]}'",
            "low-confidence retrieval, cautious answer returned",
            "degraded",
            time.time(),
        )
        return {
            "answer": {
                "content": content,
                "subject": subject,
                "knowledge_point": knowledge_point,
                "sources": retrieval.get("sources", []),
                "retrieval_confidence": retrieval.get("confidence", "unknown"),
            },
            "suggested_followups": ["补充完整题干", "查看相关知识点", "生成基础诊断题"],
            "llm_used": False,
            "llm_error": retrieval.get("warning", "low-confidence retrieval"),
            "agent_steps": state.get("agent_steps", []) + [step],
        }

    knowledge_text = _format_knowledge_text(retrieved)
    memory_text = "\n".join([m.get("content", "") for m in memories]) if memories else "暂无强相关长期记忆。"
    mastery_text = (
        f"掌握度：{mastery.get('status', '未知')}，正确率：{mastery.get('correct_rate', 0)}"
        if mastery
        else "暂无掌握度数据。"
    )
    history_lines = [f"{m.get('role', '')}: {m.get('content', '')}" for m in history[-4:]]
    history_section = "\n近期对话：\n" + "\n".join(history_lines) if history_lines else ""

    seed_qs = state.get("seed_questions", [])
    similar_qs_text = ""
    if seed_qs:
        lines = []
        for i, sq in enumerate(seed_qs[:2]):
            lines.append(f"题目 {i + 1}: {sq.get('question_text', '')[:200]}")
        similar_qs_text = "\n".join(lines)

    first_source = retrieved[0].get("source_id", "S1") if retrieved else "S1"
    fallback_answer = (
        f"<b>定位：</b>{subject} / {knowledge_point}<br>"
        f"<b>说明：</b>{retrieved[0]['content'][:220] if retrieved else '当前只有有限证据。'} [{first_source}]<br>"
        f"<b>结合你的画像：</b>{memory_text}<br>"
        "<b>建议：</b>做 1 道同知识点中等难度题，把理解转成可检验结果。"
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    )

    prompt = QA_USER_TEMPLATE.format(
        question=question,
        history_section=history_section,
<<<<<<< HEAD
        knowledge_text=knowledge_text,
        memory_text=memory_text,
        mastery_text=mastery_text,
=======
        knowledge_text=(
            f"{knowledge_text}\n\n"
            f"检索置信度：{retrieval.get('confidence', 'unknown')}。"
            "回答必须以 [S1]、[S2] 这样的编号证据为依据；证据不足时要明确提示，不要补编。"
        ),
        memory_text=memory_text,
        mastery_text=mastery_text,
        similar_questions=similar_qs_text or "暂无强相关种子题。",
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            chat_completion,
            [
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            fallback_answer,
        )
        try:
            llm = future.result(timeout=_NODE_TIMEOUT)
        except FutureTimeout:
            pool.shutdown(wait=False)
            logger.error("[timeout] generate_answer: LLM timed out after %ds", _NODE_TIMEOUT)
<<<<<<< HEAD
            llm = LLMResult(content=fallback_answer, used_llm=False, error=f"LLM timed out after {_NODE_TIMEOUT}s")

    step_status = "success" if llm.used_llm else "degraded"
    step_out = "已调用大模型生成回答" if llm.used_llm else "大模型不可用，已降级本地回答"
    step = _make_step("generate_answer", f"question='{question[:30]}'", step_out, step_status, time.time())
=======
            llm = LLMResult(
                content=fallback_answer,
                used_llm=False,
                error=f"LLM timed out after {_NODE_TIMEOUT}s",
            )

    step = _make_step(
        "generate_answer",
        f"question='{question[:30]}'",
        "LLM answer generated from numbered evidence" if llm.used_llm else "LLM unavailable, evidence fallback used",
        "success" if llm.used_llm else "degraded",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    suggested = ["生成专项题", "加入复习计划", f"更多 {knowledge_point} 练习"]

    return {
        "answer": {
            "content": llm.content.replace("\n", "<br>"),
            "subject": subject,
            "knowledge_point": knowledge_point,
<<<<<<< HEAD
=======
            "sources": retrieval.get("sources", []),
            "retrieval_confidence": retrieval.get("confidence", "unknown"),
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        },
        "suggested_followups": suggested,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _is_valid_content(content: str) -> bool:
    if not content or len(content) < 10:
        return False
    stripped = content.strip()
    if not stripped or all(c in " \n\r\t<>/\\," for c in stripped):
        return False
    if _REJECTION_PATTERNS.search(stripped):
        return False
    open_count = stripped.count("<")
    close_count = stripped.count(">")
<<<<<<< HEAD
    if open_count > close_count + 5:
        return False
    return True
=======
    return open_count <= close_count + 5
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)


def validate_answer(state: QAState) -> dict:
    answer = state.get("answer", {})
    content = answer.get("content", "")
    valid = _is_valid_content(content)
<<<<<<< HEAD
    reason = "valid" if valid else "invalid content, triggering fallback"
    step = _make_step("validate_answer", f"content_len={len(content)}", reason, "success" if valid else "warning", time.time())
=======
    retrieval = state.get("retrieval", {})

    if valid and retrieval.get("grounded") and not answer.get("sources"):
        valid = False
        reason = "answer missing retrieval sources, triggering fallback"
    else:
        reason = "valid" if valid else "invalid content, triggering fallback"

    step = _make_step(
        "validate_answer",
        f"content_len={len(content)}",
        reason,
        "success" if valid else "warning",
        time.time(),
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return {
        "answer_valid": valid,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_answer(state: QAState) -> dict:
    subject = state.get("subject", "408")
    knowledge_point = state.get("knowledge_point", "综合")
    retrieved = state.get("retrieved_knowledge", [])
<<<<<<< HEAD
    content = retrieved[0]["content"][:300] if retrieved else "建议先复习该知识点的基础概念，再做针对性练习。"

    fallback_text = (
        f"<b>定位：</b>{subject} · {knowledge_point}<br>"
        f"<b>说明：</b>{content}<br>"
        f"<b>建议：</b>复习该知识点后，做 1-2 道中等难度题目巩固理解。"
    )
    step = _make_step("fallback_answer", f"subject={subject}, kp={knowledge_point}", "模板回答已生成", "success", time.time())
    return {
        "answer": {"content": fallback_text, "subject": subject, "knowledge_point": knowledge_point},
=======
    retrieval = state.get("retrieval", {})
    content = retrieved[0]["content"][:300] if retrieved else "建议先复习该知识点的基础概念，再做针对性练习。"
    source = retrieved[0].get("source_id", "S1") if retrieved else ""

    fallback_text = (
        f"<b>定位：</b>{subject} / {knowledge_point}<br>"
        f"<b>说明：</b>{content}{f' [{source}]' if source else ''}<br>"
        "<b>建议：</b>复习该知识点后，做 1-2 道中等难度题目巩固理解。"
    )
    step = _make_step(
        "fallback_answer",
        f"subject={subject}, kp={knowledge_point}",
        "template answer generated from retrieval evidence",
        "success",
        time.time(),
    )
    return {
        "answer": {
            "content": fallback_text,
            "subject": subject,
            "knowledge_point": knowledge_point,
            "sources": retrieval.get("sources", []),
            "retrieval_confidence": retrieval.get("confidence", "unknown"),
        },
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        "llm_used": False,
        "llm_error": "answer validation failed, fallback triggered",
        "suggested_followups": ["复习知识点", "生成专项题", "查看解析"],
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def should_fallback(state: QAState) -> Literal["fallback_answer", "end"]:
    if not state.get("answer_valid", True):
        return "fallback_answer"
    return "end"


def _build_qa_graph() -> StateGraph:
    workflow = StateGraph(QAState)

    for name, fn in [
        ("detect_intent", detect_intent),
        ("load_history", load_history),
        ("retrieve_knowledge", retrieve_knowledge_node),
        ("retrieve_memory", retrieve_memory),
        ("load_mastery", load_mastery),
        ("generate_answer", _with_timeout(generate_answer_node)),
        ("validate_answer", validate_answer),
        ("fallback_answer", fallback_answer),
    ]:
        workflow.add_node(name, _safe_node(fn))

    workflow.set_entry_point("detect_intent")
    workflow.add_edge("detect_intent", "load_history")
    workflow.add_edge("load_history", "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "load_mastery")
    workflow.add_edge("load_mastery", "generate_answer")
    workflow.add_edge("generate_answer", "validate_answer")
<<<<<<< HEAD
    workflow.add_conditional_edges("validate_answer", should_fallback, {"fallback_answer": "fallback_answer", "end": END})
=======
    workflow.add_conditional_edges(
        "validate_answer",
        should_fallback,
        {"fallback_answer": "fallback_answer", "end": END},
    )
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    workflow.add_edge("fallback_answer", END)

    return workflow.compile()


def get_qa_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_qa_graph()
    return _GRAPH
