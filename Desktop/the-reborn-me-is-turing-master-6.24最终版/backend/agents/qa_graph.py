from __future__ import annotations

import contextvars
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Literal

from langgraph.graph import StateGraph
from sqlalchemy.orm import Session

from agents.graph_state import QAState
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import KnowledgeMastery
from prompts.qa_prompt import QA_SYSTEM_PROMPT, QA_USER_TEMPLATE
from services.chroma_service import query_documents
from services.knowledge_heuristics import infer_all
from services.llm_service import LLMResult, chat_completion
from services.rag_service import retrieve_knowledge as mysql_retrieve_knowledge, retrieve_user_memory

logger = logging.getLogger("qa_graph")

_FOLLOWUP_TRIGGERS = {
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
_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()





def detect_intent(state: QAState) -> dict:
    question = state.get("question", "")
    q_lower = question.strip().lower()

    is_followup = False
    if len(question) < 10:
        is_followup = True
    elif any(w in q_lower for w in _FOLLOWUP_TRIGGERS):
        is_followup = True
    elif question.startswith(("那", "这")):
        is_followup = True

    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")

    if is_followup and not subject:
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

    if not subject:
        inferred = infer_all(question)
        subject = inferred["subject"] or "408"
        knowledge_point = knowledge_point or inferred["knowledge_point"]

    if not knowledge_point:
        knowledge_point = infer_all(question).get("knowledge_point", "")

    step = _make_step("detect_intent", question, f"subject={subject}, kp={knowledge_point}, followup={is_followup}", "success", time.time())
    logger.info("intent: subject=%s kp=%s followup=%s", subject, knowledge_point, is_followup)
    return {
        "subject": subject,
        "knowledge_point": knowledge_point,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def load_history(state: QAState) -> dict:
    history = state.get("history", [])
    step = _make_step("load_history", f"history_size={len(history)}", f"loaded {len(history)} messages", "success", time.time())
    return {
        "history": history,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_knowledge(state: QAState) -> dict:
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
    items = result.get("items", [])
    fallback = result.get("fallback", False)

    retrieved = []
    chroma_score_max = 0.0
    if items:
        for item in items:
            score = item.get("score", 0)
            chroma_score_max = max(chroma_score_max, score)
            meta = item.get("metadata", {})
            retrieved.append({
                "subject": meta.get("subject", subject),
                "knowledge_point": meta.get("knowledge_point", knowledge_point),
                "content": item.get("text", ""),
                "score": score,
            })

    needs_mysql = not items or chroma_score_max < _CHROMA_SCORE_THRESHOLD
    if needs_mysql and db:
        mysql_items = mysql_retrieve_knowledge(db, question, limit=3)
        if mysql_items:
            existing_ids = {r["content"][:80] for r in retrieved}
            for m in mysql_items:
                if m.get("content", "")[:80] not in existing_ids:
                    retrieved.append(m)
                    existing_ids.add(m.get("content", "")[:80])

    out = f"ChromaDB: {len(items)} items, max_score={chroma_score_max:.2f}" + (f", MySQL: {len([r for r in retrieved if r.get('source','chromadb')!='chromadb'])}" if db else "")
    step = _make_step("retrieve_knowledge", f"query={question[:40]}", out, "success", time.time())
    return {
        "retrieved_knowledge": retrieved,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_memory(state: QAState) -> dict:
    user_id = state.get("user_id", 0)
    db = _get_db()
    memories = []
    if db and user_id:
        memories = retrieve_user_memory(db, user_id, state.get("question", ""), limit=3)
    out = f"memories={len(memories)}" if memories else "no memories"
    step = _make_step("retrieve_memory", f"user_id={user_id}", out, "success", time.time())
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
    step = _make_step("load_mastery", f"kp={state.get('knowledge_point','')}", f"mastery={mastery}", "success", time.time())
    return {
        "mastery": mastery,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def generate_answer(state: QAState) -> dict:
    question = state.get("question", "")
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    retrieved = state.get("retrieved_knowledge", [])
    memories = state.get("memories_used", [])
    mastery = state.get("mastery", {})
    history = state.get("history", [])

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
    )

    prompt = QA_USER_TEMPLATE.format(
        question=question,
        history_section=history_section,
        knowledge_text=knowledge_text,
        memory_text=memory_text,
        mastery_text=mastery_text,
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
            llm = LLMResult(content=fallback_answer, used_llm=False, error=f"LLM timed out after {_NODE_TIMEOUT}s")

    step_status = "success" if llm.used_llm else "degraded"
    step_out = "已调用大模型生成回答" if llm.used_llm else "大模型不可用，已降级本地回答"
    step = _make_step("generate_answer", f"question='{question[:30]}'", step_out, step_status, time.time())
    suggested = ["生成专项题", "加入复习计划", f"更多 {knowledge_point} 练习"]

    return {
        "answer": {
            "content": llm.content.replace("\n", "<br>"),
            "subject": subject,
            "knowledge_point": knowledge_point,
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
    if open_count > close_count + 5:
        return False
    return True


def validate_answer(state: QAState) -> dict:
    answer = state.get("answer", {})
    content = answer.get("content", "")
    valid = _is_valid_content(content)
    reason = "valid" if valid else "invalid content, triggering fallback"
    step = _make_step("validate_answer", f"content_len={len(content)}", reason, "success" if valid else "warning", time.time())
    return {
        "_answer_valid": valid,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_answer(state: QAState) -> dict:
    subject = state.get("subject", "408")
    knowledge_point = state.get("knowledge_point", "综合")
    retrieved = state.get("retrieved_knowledge", [])
    content = retrieved[0]["content"][:300] if retrieved else "建议先复习该知识点的基础概念，再做针对性练习。"

    fallback_text = (
        f"<b>定位：</b>{subject} · {knowledge_point}<br>"
        f"<b>说明：</b>{content}<br>"
        f"<b>建议：</b>复习该知识点后，做 1-2 道中等难度题目巩固理解。"
    )
    step = _make_step("fallback_answer", f"subject={subject}, kp={knowledge_point}", "模板回答已生成", "success", time.time())
    return {
        "answer": {"content": fallback_text, "subject": subject, "knowledge_point": knowledge_point},
        "llm_used": False,
        "llm_error": "answer validation failed, fallback triggered",
        "suggested_followups": ["复习知识点", "生成专项题", "查看解析"],
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def should_fallback(state: QAState) -> Literal["fallback_answer", "end"]:
    if not state.get("_answer_valid", True):
        return "fallback_answer"
    return "end"


def _build_qa_graph() -> StateGraph:
    workflow = StateGraph(QAState)

    for name, fn in [
        ("detect_intent", detect_intent),
        ("load_history", load_history),
        ("retrieve_knowledge", retrieve_knowledge),
        ("retrieve_memory", retrieve_memory),
        ("load_mastery", load_mastery),
        ("generate_answer", _with_timeout(generate_answer)),
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
    workflow.add_conditional_edges("validate_answer", should_fallback, {"fallback_answer": "fallback_answer", "end": "__end__"})

    return workflow.compile()


def get_qa_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_qa_graph()
    return _GRAPH
