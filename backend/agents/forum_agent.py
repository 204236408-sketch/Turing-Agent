"""论坛 AI 小助手核心智能体。

支持：
- P0-1  结构化 JSON 输出（基于 FORUM_AI_PROMPT 真实生效）
- P0-2  RAG 检索（ChromaDB + MySQL 知识库）
- P0-3  用户记忆 + 掌握度注入
- P1-6  LangGraph 多步推理
- P1-7  答案校验（拒绝检测/降级）
- P1-8  反哺 user_memory
- P2-14 追问判定
- P2-15 历史评论上下文

对外暴露：
- ai_answer_for_post(...)
- ai_followup_for_post(...)
- forum_graph 编译对象
"""
from __future__ import annotations

import contextvars
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from agents.graph_state import AgentStep
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import (
    ForumAiAnswer,
    ForumAiAnswerLike,
    ForumAiFollowup,
    ForumComment,
    KnowledgeMastery,
    UserMemory,
)
from prompts.forum_prompt import FORUM_AI_PROMPT
from services.llm_service import LLMResult, chat_completion, chat_json
from services.mastery_service import recalculate_mastery
from services.rag_service import retrieve_user_memory

logger = logging.getLogger("forum_agent")

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None

# 视频链接池（hardcoded，从 FORUM_AI_PROMPT 同步）
SUBJECT_VIDEO_POOL = {
    "数据结构": "https://www.bilibili.com/video/BV1xx411c79H",
    "计算机组成原理": "https://www.bilibili.com/video/BV19E411D78Q",
    "操作系统": "https://www.bilibili.com/video/BV1maJJ6DE2Z",
    "计算机网络": "https://www.bilibili.com/video/BV12mjT63EsS",
}

_REJECTION_PATTERNS = re.compile(
    r"抱歉|对不起|无法回答|不清楚|不知道|我不确定|没有相关信息|无法提供",
    re.IGNORECASE,
)

_FOLLOWUP_HINT_PATTERNS = re.compile(
    r"能否.*?(发|贴|提供|给|补)|请补全|具体.*?(题干|描述)|什么.*?题型|你.*?(学|复习|看)到",
    re.IGNORECASE,
)


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()


# ---------------- 公共工具 ----------------

def _safe_get(d: dict, *keys, default=""):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _detect_subject_kp(post_subject: str, post_kp: str, title: str, content: str) -> tuple[str, str]:
    """优先级：帖子自带 > 启发式推断。"""
    subject = post_subject or ""
    kp = post_kp or ""
    if not subject or not kp:
        try:
            from services.knowledge_heuristics import infer_all
            inferred = infer_all(f"{title}\n{content[:500]}")
            subject = subject or inferred.get("subject", "")
            kp = kp or inferred.get("knowledge_point", "")
        except Exception:
            pass
    if not subject:
        subject = "408"
    return subject, kp


def _build_user_profile(
    db: Session | None,
    user_id: int | None,
    subject: str,
    knowledge_point: str,
) -> dict:
    """组装用户画像：掌握度、近期记忆、常见错因。"""
    profile: dict[str, Any] = {
        "mastery_status": "",
        "weak_score": 0.0,
        "correct_rate": 0.0,
        "recent_memories": [],
        "common_errors": [],
    }
    if not db or not user_id:
        return profile

    try:
        mastery_row = (
            db.query(KnowledgeMastery)
            .filter(
                KnowledgeMastery.user_id == user_id,
                KnowledgeMastery.subject == subject,
                KnowledgeMastery.knowledge_point == knowledge_point,
            )
            .first()
        )
        if mastery_row:
            profile["mastery_status"] = mastery_row.final_status or ""
            profile["weak_score"] = mastery_row.weak_score or 0.0
            total = mastery_row.total_answer_count or 0
            correct = mastery_row.correct_count or 0
            profile["correct_rate"] = round(correct / total, 2) if total else 0.0
    except Exception as e:
        logger.warning("[forum_agent] load mastery failed: %s", e)

    try:
        # 按当前 subject 过滤；不传 query 强制走 MySQL，避免 chroma 弱语义匹配串入无关科目
        memories = retrieve_user_memory(db, user_id, "", limit=8)
        # 优先同 subject 的记忆，跨 subject 不注入
        same_subj = [m for m in memories if (m.get("subject") or "") == subject][:3]
        profile["recent_memories"] = [
            {"content": m.get("content", ""), "type": m.get("type", "")} for m in same_subj
        ]
    except Exception as e:
        logger.warning("[forum_agent] load memory failed: %s", e)

    try:
        weak_mems = (
            db.query(UserMemory)
            .filter(
                UserMemory.user_id == user_id,
                UserMemory.subject == subject,
                UserMemory.memory_type == "weak_point",
                UserMemory.status == "active",
                UserMemory.is_deleted == False,
            )
            .order_by(UserMemory.update_time.desc())
            .limit(3)
            .all()
        )
        profile["common_errors"] = [m.content for m in weak_mems if m.content][:3]
    except Exception as e:
        logger.warning("[forum_agent] load errors failed: %s", e)

    return profile


def _format_kb(retrieved: list[dict]) -> str:
    if not retrieved:
        return "（本次未检索到强相关知识库证据，回答将基于 408 通识与用户画像。）"
    lines = []
    for i, item in enumerate(retrieved, 1):
        subj = item.get("subject", "未知科目")
        kp = item.get("knowledge_point", item.get("section", ""))
        content = item.get("content", "")
        score = item.get("rerank_score", item.get("score", 0))
        source = item.get("source", "unknown")
        lines.append(f"[{i}] ({subj}/{kp}) [score={float(score):.3f}, src={source}]\n{content[:600]}")
    return "\n\n".join(lines)


def _format_weak_kp(profile: dict) -> str:
    mastery = profile.get("mastery_status", "未知")
    correct_rate = profile.get("correct_rate", 0.0)
    weak_score = profile.get("weak_score", 0.0)
    memories = profile.get("recent_memories", [])
    errors = profile.get("common_errors", [])

    parts = [
        f"- 掌握度：{mastery}（正确率 {correct_rate}，weak_score={weak_score}）",
    ]
    if memories:
        parts.append("- 近期记忆：")
        for m in memories[:3]:
            content = m.get("content", "")[:80]
            parts.append(f"  · {content}")
    if errors:
        parts.append("- 常见错因：")
        for e in errors[:3]:
            parts.append(f"  · {e[:80]}")
    return "\n".join(parts)


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "（暂无评论）"
    lines = []
    for i, c in enumerate(comments, 1):
        author = c.get("author", "匿名")
        content = c.get("content", "")
        lines.append(f"{i}. {author}: {content[:200]}")
    return "\n".join(lines)


def _is_rejection(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if _REJECTION_PATTERNS.search(stripped):
        return True
    if len(stripped) < 15:
        return True
    return False


def _is_low_quality_answer(data: dict) -> tuple[bool, str]:
    """校验 LLM 输出的结构化 JSON 是否合格。

    收敛到 4 个核心字段：subject_kp / analysis / easy_trap / extend_exercise。
    """
    if not isinstance(data, dict):
        return True, "answer not dict"
    required = ["analysis", "easy_trap", "extend_exercise"]
    for k in required:
        v = data.get(k, "")
        if not v or not str(v).strip():
            return True, f"missing field: {k}"
        if len(str(v).strip()) < 8:
            return True, f"field {k} too short"
    # 详细解析必须详尽（>= 200 字符的最小护栏；Prompt 要求至少 700 字，由 LLM 自行保证）
    analysis_text = str(data.get("analysis", "")).strip()
    if len(analysis_text) < 200:
        return True, f"analysis too short ({len(analysis_text)} chars)"
    if _is_rejection(analysis_text):
        return True, "rejection in analysis"
    return False, "ok"


def _cautious_answer(post_title: str, subject: str, knowledge_point: str, reason: str) -> dict:
    """谨慎降级回答（LLM 失败时使用），仅含 4 个核心字段。"""
    subj_disp = subject or "408"
    kp = knowledge_point.strip() if knowledge_point else ""
    if kp and kp != subj_disp:
        subject_kp = f"{subj_disp} · {kp}"
    else:
        subject_kp = f"{subj_disp} 综合知识"
    return {
        "subject_kp": subject_kp,
        "analysis": (
            f"针对帖子「{post_title}」，当前知识库没有找到足够可信的证据来直接作答。"
            f"请先明确题目中发生状态变化的时刻，并把每一步列出来：① 问题重述——把题干拆成「输入/操作序列/期望输出」三段；"
            f"② 核心概念——回到 408 教材相应章节，定位到 {subj_disp} {('-' + kp) if kp else ''} 的定义与边界条件；"
            f"③ 解题步骤——按时间/空间顺序推演，每一步标注对应的定理/规则；"
            f"④ 关键公式/原理——列出本类题通用的判别式与记忆口诀；"
            f"⑤ 结论——与题目期望输出核对，确认边界（空、半满、并发冲突等）。"
            f"补全题干后可重新提问，AI 会基于完整证据给出 408 风格的详细解析。"
        ),
        "easy_trap": "1) 在缺乏证据时直接给结论；2) 忽略 408 真题常考的边界条件与例外情况；3) 把「最坏/平均/最好」三种复杂度混为一谈。",
        "extend_exercise": (
            "1) 列出本题涉及的 2 个核心定义并口述其区别；"
            "2) 用一道同知识点中等题（408 真题或王道课后题）独立完成，对照答案逐句纠错。"
        ),
        "need_follow_up": "true",
        "evidence_warning": reason or "evidence insufficient",
    }


# ---------------- LangGraph 节点 ----------------

def detect_intent_node(state: dict) -> dict:
    """节点 1：识别 subject / kp / 是否追问。"""
    start = time.time()
    post = state.get("post", {}) or {}
    title = post.get("title", "")
    content = post.get("content", "")
    subject, kp = _detect_subject_kp(
        post.get("subject", ""),
        post.get("knowledge_point", ""),
        title,
        content,
    )
    is_followup = bool(state.get("followup_question"))
    step = _make_step(
        "detect_intent",
        f"title='{title[:30]}'",
        f"subject={subject}, kp={kp}, followup={is_followup}",
        "success",
        start,
    )
    return {
        "subject": subject,
        "knowledge_point": kp,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def load_history_node(state: dict) -> dict:
    """节点 2：加载历史追问 + 评论上下文。"""
    db = _get_db()
    start = time.time()
    post = state.get("post", {}) or {}
    post_id = post.get("id")
    answer_id = state.get("answer_id")

    history: list[dict] = []
    if db and answer_id:
        rows = (
            db.query(ForumAiFollowup)
            .filter(ForumAiFollowup.answer_id == answer_id)
            .order_by(ForumAiFollowup.create_time)
            .limit(12)  # 6 轮对话 = 12 条 (user+assistant)
            .all()
        )
        for r in rows:
            history.append({"role": r.role or "user", "content": r.content or ""})

    comments: list[dict] = []
    if db and post_id:
        rows = (
            db.query(ForumComment)
            .filter(ForumComment.post_id == post_id, ForumComment.is_deleted == False)
            .order_by(ForumComment.create_time)
            .limit(10)
            .all()
        )
        for r in rows:
            comments.append({"author": "用户", "content": r.content})

    step = _make_step(
        "load_history",
        f"answer_id={answer_id}",
        f"history={len(history)}, comments={len(comments)}",
        "success",
        start,
    )
    return {
        "history": history,
        "comments": comments,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_knowledge_node(state: dict) -> dict:
    """节点 3：RAG 知识库检索（ChromaDB + MySQL）。"""
    db = _get_db()
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    post = state.get("post", {}) or {}
    query = f"{post.get('title', '')}\n{post.get('content', '')[:500]}"

    retrieved: list[dict] = []
    confidence = "low"
    best_score = 0.0

    try:
        from services.hybrid_retriever import hybrid_retrieve
        result = hybrid_retrieve(
            db=db,
            query=query,
            limit=5,
            subject_filter=subject or None,
            kp_filter=knowledge_point or None,
            use_rerank=True,
        )
        for item in result.get("items", []):
            score = float(item.get("rerank_score", item.get("score", 0)))
            if score > best_score:
                best_score = score
            retrieved.append({
                "subject": item.get("subject", subject),
                "knowledge_point": item.get("knowledge_point", knowledge_point),
                "content": item.get("content", ""),
                "score": score,
                "source": item.get("source", "unknown"),
                "source_id": f"S{len(retrieved) + 1}",
            })
    except Exception as e:
        logger.warning("[forum_agent] hybrid_retrieve failed: %s", e)

    if best_score >= 0.45:
        confidence = "high"
    elif best_score >= 0.25:
        confidence = "medium"

    step = _make_step(
        "retrieve_knowledge",
        f"query={query[:40]}",
        f"items={len(retrieved)}, best={best_score:.2f}, conf={confidence}",
        "success" if retrieved else "warning",
        start,
    )
    return {
        "retrieved_knowledge": retrieved,
        "retrieval": {
            "confidence": confidence,
            "best_score": round(best_score, 4),
            "grounded": bool(retrieved) and best_score >= 0.25,
            "sources": [
                {
                    "source_id": item["source_id"],
                    "subject": item["subject"],
                    "knowledge_point": item["knowledge_point"],
                    "score": round(item["score"], 4),
                    "preview": item["content"][:180],
                }
                for item in retrieved[:5]
            ],
        },
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_memory_node(state: dict) -> dict:
    """节点 4：拉取用户记忆、掌握度、常见错因。"""
    db = _get_db()
    start = time.time()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    kp = state.get("knowledge_point", "")
    profile = _build_user_profile(db, user_id if user_id else None, subject, kp)
    step = _make_step(
        "retrieve_memory",
        f"user_id={user_id}",
        f"mastery={profile.get('mastery_status', '未知')}, mem={len(profile.get('recent_memories', []))}",
        "success",
        start,
    )
    return {
        "user_profile": profile,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def generate_answer_node(state: dict) -> dict:
    """节点 5：调用 LLM 生成结构化 JSON。"""
    start = time.time()
    subject = state.get("subject", "408")
    kp = state.get("knowledge_point", "")
    post = state.get("post", {}) or {}
    title = post.get("title", "")
    content = post.get("content", "")
    retrieved = state.get("retrieved_knowledge", [])
    profile = state.get("user_profile", {})
    history = state.get("history", [])
    comments = state.get("comments", [])
    retrieval = state.get("retrieval", {})
    followup = state.get("followup_question", "")

    fallback = _cautious_answer(title, subject, kp, retrieval.get("warning", ""))
    # 即使 retrieval.grounded=False 也尝试调用 LLM（避免用户得到硬编码模板）；
    # 仅在 LLM 失败/拒绝/超时 才回退到 fallback 模板。
    history_section = ""
    if history:
        history_section = "\n\n【历史追问上下文】\n" + "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')[:300]}" for m in history[-6:]
        )
    followup_section = f"\n\n【用户最新追问】\n{followup}" if followup else ""
    grounded_note = "" if retrieval.get("grounded", False) else "\n\n【提示】本次知识库证据较弱，请基于帖子内容与一般 408 知识给出尽可能有用的回答，并明确指出不确定之处。"

    prompt = FORUM_AI_PROMPT.format(
        title=title,
        content=content,
        comment_ctx=_format_comments(comments) + history_section,
        weak_kp=_format_weak_kp(profile),
        kb_data=_format_kb(retrieved) + grounded_note,
    ) + followup_section

    user_prompt = (
        f"现在请严格按 JSON 规范输出针对帖子「{title}」的 AI 回答。\n{prompt}"
    )

    def _call() -> LLMResult:
        return chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是 408 考研官方论坛 AI 助教，深耕四门统考科目，"
                        "结合帖子、评论、用户薄弱点与 408 知识库生成结构化专业回答。"
                        "**严格输出合法 JSON，禁止额外文字、Markdown、注释。**"
                        "**只输出 4 个字段：subject_kp / analysis / easy_trap / extend_exercise，不要输出其他字段。**"
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            fallback,
            temperature=0.3,
            max_tokens=4096,
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_call)
        try:
            llm = future.result(timeout=_NODE_TIMEOUT)
        except FutureTimeout:
            pool.shutdown(wait=False)
            llm = LLMResult(
                content=json.dumps(fallback, ensure_ascii=False),
                used_llm=False,
                error=f"LLM timed out after {_NODE_TIMEOUT}s",
                data=fallback,
            )

    data = llm.data if isinstance(llm.data, dict) else fallback
    # 规范化字段：仅保留 4 个核心字段
    for key in ("subject_kp", "analysis", "easy_trap", "extend_exercise"):
        if not data.get(key):
            data[key] = fallback.get(key, "")
    # 主动剔除多余字段，确保前端只渲染 4 张卡片
    allowed_keys = {"subject_kp", "analysis", "easy_trap", "extend_exercise", "need_follow_up"}
    for extra in list(data.keys()):
        if extra not in allowed_keys:
            data.pop(extra, None)
    if "need_follow_up" not in data:
        data["need_follow_up"] = "false"

    step = _make_step(
        "generate_answer",
        f"title='{title[:30]}'",
        f"LLM={llm.used_llm}, fields={len(data)}",
        "success" if llm.used_llm else "degraded",
        start,
    )
    return {
        "answer": data,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def validate_answer_node(state: dict) -> dict:
    """节点 6：校验答案质量。"""
    start = time.time()
    answer = state.get("answer", {})
    is_low, reason = _is_low_quality_answer(answer)
    valid = not is_low
    step = _make_step(
        "validate_answer",
        f"fields={list(answer.keys())[:6]}",
        f"valid={valid}, reason={reason}",
        "success" if valid else "warning",
        start,
    )
    return {
        "answer_valid": valid,
        "validation_reason": reason,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_answer_node(state: dict) -> dict:
    """节点 7：低质量答案降级。"""
    start = time.time()
    subject = state.get("subject", "408")
    kp = state.get("knowledge_point", "")
    post = state.get("post", {}) or {}
    title = post.get("title", "")
    retrieved = state.get("retrieved_knowledge", [])
    reason = state.get("validation_reason", "")
    if retrieved:
        content = retrieved[0].get("content", "")[:300]
    else:
        content = "建议先复习该知识点的基础概念，再做针对性练习。"

    fallback = _cautious_answer(title, subject, kp, reason or "answer validation failed")
    fallback["analysis"] = (
        f"基于已有证据的简要说明：{content}\n\n"
        f"针对帖子「{title}」的精确回答需要更完整的题干或上下文。"
    )
    step = _make_step(
        "fallback_answer",
        f"reason={reason}",
        "template answer generated",
        "degraded",
        start,
    )
    return {
        "answer": fallback,
        "llm_used": False,
        "llm_error": reason or "fallback",
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def memory_update_node(state: dict) -> dict:
    """节点 8：把 AI 回答提炼的 memory_tip 写回 user_memory。"""
    db = _get_db()
    start = time.time()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    kp = state.get("knowledge_point", "")
    answer = state.get("answer", {}) or {}
    tip = str(answer.get("memory_tip", "")).strip()
    if not db or not user_id or not tip or len(tip) < 5:
        return {"agent_steps": state.get("agent_steps", []) + [
            _make_step("memory_update", "skip", "no tip", "skipped", start)
        ]}
    try:
        memory = UserMemory(
            user_id=user_id,
            memory_type="forum_clarify",
            subject=subject,
            knowledge_point=kp,
            content=f"[论坛AI] {tip}",
            evidence=f"forum_post:{state.get('post', {}).get('id', '')}",
        )
        db.add(memory)
        db.flush()
        # 触发掌握度重算
        if subject and kp:
            try:
                recalculate_mastery(db, user_id, subject, kp)
            except Exception:
                pass
        step = _make_step(
            "memory_update",
            f"tip='{tip[:30]}'",
            f"memory_id={memory.id}",
            "success",
            start,
        )
        return {"memory_id": memory.id, "agent_steps": state.get("agent_steps", []) + [step]}
    except Exception as e:
        logger.warning("[forum_agent] memory_update failed: %s", e)
        return {"agent_steps": state.get("agent_steps", []) + [
            _make_step("memory_update", "fail", str(e), "failed", start)
        ]}


def persist_answer_node(state: dict) -> dict:
    """节点 9：把 AI 回答持久化到 forum_ai_answer 表（P2-11）。"""
    db = _get_db()
    start = time.time()
    user_id = state.get("user_id", 0)
    post = state.get("post", {}) or {}
    post_id = post.get("id")
    answer = state.get("answer", {}) or {}
    retrieval = state.get("retrieval", {})

    if not db or not post_id or not answer:
        return {"agent_steps": state.get("agent_steps", []) + [
            _make_step("persist_answer", "skip", "no post/answer", "skipped", start)
        ]}
    try:
        # 软删旧记录：把同 post 的 active 答案置为 inactive
        db.query(ForumAiAnswer).filter(
            ForumAiAnswer.post_id == post_id, ForumAiAnswer.is_active == True
        ).update({"is_active": False})

        record = ForumAiAnswer(
            post_id=post_id,
            user_id=user_id,
            subject=state.get("subject", ""),
            knowledge_point=state.get("knowledge_point", ""),
            structured_json=json.dumps(answer, ensure_ascii=False),
            analysis=str(answer.get("analysis", "")),
            easy_trap=str(answer.get("easy_trap", "")),
            extend_exercise=str(answer.get("extend_exercise", "")),
            review_plan=str(answer.get("review_plan", "")),
            recommend_questions=str(answer.get("recommend_questions", "")),
            recommend_video=str(answer.get("recommend_video", "")),
            memory_tip=str(answer.get("memory_tip", "")),
            need_follow_up=bool(str(answer.get("need_follow_up", "")).lower() in ("true", "1", "yes")),
            sources_json=json.dumps(retrieval.get("sources", []), ensure_ascii=False),
            retrieval_confidence=str(retrieval.get("confidence", "")),
            agent_steps_json=json.dumps(state.get("agent_steps", [])[-5:], ensure_ascii=False),
            llm_used=bool(state.get("llm_used", False)),
            llm_error=str(state.get("llm_error", "") or "")[:500],
            is_active=True,
        )
        db.add(record)
        db.flush()
        db.commit()
        step = _make_step(
            "persist_answer",
            f"post_id={post_id}",
            f"answer_id={record.id}",
            "success",
            start,
        )
        return {
            "answer_id": record.id,
            "agent_steps": state.get("agent_steps", []) + [step],
        }
    except Exception as e:
        logger.warning("[forum_agent] persist failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return {"agent_steps": state.get("agent_steps", []) + [
            _make_step("persist_answer", "fail", str(e), "failed", start)
        ]}


def followup_decide_node(state: dict) -> dict:
    """节点 10：是否需要追问用户（P2-14）。"""
    start = time.time()
    answer = state.get("answer", {}) or {}
    need = str(answer.get("need_follow_up", "false")).lower() == "true"
    followup_hint = ""
    if need:
        kp = state.get("knowledge_point", "")
        followup_hint = (
            f"为了给出更精准的回答，能否补充 {kp or '本知识点'} 的完整题干、"
            "选项或关键术语？也可以贴出你已尝试的思路。"
        )
    step = _make_step(
        "followup_decide",
        f"need_follow_up={answer.get('need_follow_up', 'false')}",
        f"need={need}",
        "success",
        start,
    )
    return {
        "should_followup": need,
        "followup_hint": followup_hint,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _should_fallback(state: dict) -> Literal["fallback_answer", "memory_update"]:
    if not state.get("answer_valid", True):
        return "fallback_answer"
    return "memory_update"


# ---------------- Graph 构建 ----------------

def _build_forum_graph() -> StateGraph:
    workflow = StateGraph(dict)

    for name, fn in [
        ("detect_intent", detect_intent_node),
        ("load_history", load_history_node),
        ("retrieve_knowledge", retrieve_knowledge_node),
        ("retrieve_memory", retrieve_memory_node),
        ("generate_answer", _with_timeout(generate_answer_node)),
        ("validate_answer", validate_answer_node),
        ("fallback_answer", fallback_answer_node),
        ("memory_update", memory_update_node),
        ("persist_answer", persist_answer_node),
        ("followup_decide", followup_decide_node),
    ]:
        workflow.add_node(name, _safe_node(fn))

    workflow.set_entry_point("detect_intent")
    workflow.add_edge("detect_intent", "load_history")
    workflow.add_edge("load_history", "retrieve_knowledge")
    workflow.add_edge("retrieve_knowledge", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "generate_answer")
    workflow.add_edge("generate_answer", "validate_answer")
    workflow.add_conditional_edges(
        "validate_answer",
        _should_fallback,
        {"fallback_answer": "fallback_answer", "memory_update": "memory_update"},
    )
    workflow.add_edge("fallback_answer", "memory_update")
    workflow.add_edge("memory_update", "persist_answer")
    workflow.add_edge("persist_answer", "followup_decide")
    workflow.add_edge("followup_decide", END)

    return workflow.compile()


def get_forum_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_forum_graph()
    return _GRAPH


# ---------------- 对外 API（兼容老接口） ----------------

def run_forum_graph(
    db: Session,
    post: dict,
    user_id: int = 0,
    followup_question: str = "",
    answer_id: int | None = None,
) -> dict:
    """执行论坛 AI LangGraph，返回完整结果。

    LangGraph 0.3 + StateGraph(dict) 行为：graph.invoke() 返回的是最后一个节点的 updates
    而不是完整 state（与手动 state.update 不同）。改用 graph.stream() 累积所有 updates。
    """
    set_db(db)
    graph = get_forum_graph()
    initial_state: dict = {
        "user_id": user_id,
        "post": post,
        "followup_question": followup_question,
        "answer_id": answer_id,
        "agent_steps": [],
    }
    # 用 stream 累积所有节点 updates，构造完整 final state
    final_state: dict = dict(initial_state)
    for update in graph.stream(initial_state):
        for _node_name, node_updates in update.items():
            if isinstance(node_updates, dict):
                final_state.update(node_updates)
    answer = final_state.get("answer", {}) or {}
    return {
        "answer": answer,
        "answer_id": final_state.get("answer_id"),
        "memory_id": final_state.get("memory_id"),
        "subject": final_state.get("subject", ""),
        "knowledge_point": final_state.get("knowledge_point", ""),
        "retrieval": final_state.get("retrieval", {}),
        "agent_steps": final_state.get("agent_steps", []),
        "llm_used": final_state.get("llm_used", False),
        "llm_error": final_state.get("llm_error", ""),
        "should_followup": final_state.get("should_followup", False),
        "followup_hint": final_state.get("followup_hint", ""),
        "user_profile": final_state.get("user_profile", {}),
    }


def ai_answer_for_post(
    title: str,
    content: str,
    subject: str,
    knowledge_point: str = "",
    author_profile: dict | None = None,
    user_id: int = 0,
    post_id: int | None = None,
) -> dict:
    """兼容老接口的论坛 AI 回答入口。"""
    db = _get_db()
    post = {
        "id": post_id,
        "title": title,
        "content": content,
        "subject": subject,
        "knowledge_point": knowledge_point,
    }
    if db:
        result = run_forum_graph(db, post, user_id=user_id, followup_question="")
        answer = result["answer"]
        # 老接口字段兼容：仅渲染 4 个核心方面（问题定位/详细解析/易错陷阱/举一反三）
        analysis_html = (
            f"<p><b>📍 定位：</b>{escape_html(answer.get('subject_kp', f'{subject} - {knowledge_point}'))}</p>"
            f"<p><b>🔍 详细解析：</b>{escape_html(answer.get('analysis', ''))}</p>"
            f"<p><b>⚠️ 易错陷阱：</b>{escape_html(answer.get('easy_trap', ''))}</p>"
            f"<p><b>🎯 举一反三：</b>{escape_html(answer.get('extend_exercise', ''))}</p>"
        )
        return {
            "answer": analysis_html,
            "structured": answer,
            "answer_id": result["answer_id"],
            "retrieval": result["retrieval"],
            "agent_steps": result["agent_steps"],
            "llm_used": result["llm_used"],
            "llm_error": result["llm_error"],
            "should_followup": result["should_followup"],
            "followup_hint": result["followup_hint"],
        }
    # 无 db 降级
    fallback = (
        f"<p><b>问题定位：</b>{subject} · {knowledge_point or subject}。</p>"
        f"<p><b>建议：</b>先把帖子中的困惑拆成「概念定义、执行流程、边界条件」三块，再用一道同类题验证。</p>"
        f"<p><b>针对帖子：</b>{title} 的核心不是记结论，而是把每一步状态变化写出来。</p>"
    )
    return {
        "answer": fallback,
        "structured": {},
        "llm_used": False,
        "llm_error": "no db",
        "should_followup": False,
        "followup_hint": "",
    }


def ai_followup_for_post(
    db: Session,
    post: dict,
    user_id: int,
    followup_question: str,
    answer_id: int | None,
) -> dict:
    """对历史 AI 回答发起追问。"""
    set_db(db)
    result = run_forum_graph(
        db=db,
        post=post,
        user_id=user_id,
        followup_question=followup_question,
        answer_id=answer_id,
    )
    answer = result.get("answer", {}) or {}
    # 持久化追问历史：用图生成的新 answer_id（如果有），否则用传入的
    post_id = post.get("id") if isinstance(post, dict) else None
    persist_answer_id = result.get("answer_id") or answer_id
    try:
        if persist_answer_id and post_id:
            # 写两条记录：user 追问 + assistant 回答
            user_row = ForumAiFollowup(
                post_id=post_id,
                answer_id=persist_answer_id,
                user_id=user_id,
                role="user",
                content=followup_question,
                structured_json="",
            )
            db.add(user_row)
            db.flush()
            assistant_row = ForumAiFollowup(
                post_id=post_id,
                answer_id=persist_answer_id,
                user_id=user_id,
                role="assistant",
                content=json.dumps(answer, ensure_ascii=False),
                structured_json=json.dumps(answer, ensure_ascii=False),
                parent_id=user_row.id,
            )
            db.add(assistant_row)
            db.commit()
    except Exception as e:
        logger.warning("[forum_agent] save followup failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass

    return {
        "answer": answer,
        "structured": answer,
        "should_followup": result.get("should_followup", False),
        "followup_hint": result.get("followup_hint", ""),
        "agent_steps": result.get("agent_steps", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
    }


# ---------------- 工具函数 ----------------

def escape_html(s: str) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def escape_attr(s: str) -> str:
    return escape_html(s).replace("'", "&#39;")
