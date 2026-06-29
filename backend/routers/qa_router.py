"""
问答聊天接口

功能：
- POST /api/qa/chat        — 同步问答（保留向后兼容）
- GET  /api/qa/chat/stream — SSE 流式问答（打字机 + 步骤提示）
- GET  /api/qa/history     — 获取问答历史会话列表

设计要点：
- 始终走 LLM 流式（chat_completion_stream），让 LLM 主导回答
- 知识库命中时：RAG 检索到的内容作为 LLM 上下文
- 知识库未命中时：提示 LLM 基于自身知识回答（不返回笼统模板）
- LLM 异常时：fallback 到纯文本提示，不阻塞前端
- SSE 用同步生成器 + 队列 + 后台线程（避免 async generator 在 StreamingResponse 中 hang）
"""
import json
import logging
import queue
import threading
import time
from typing import Generator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agents.qa_graph import (
    detect_intent,
    load_mastery,
    retrieve_knowledge_node,
    retrieve_memory,
    set_db,
)
from database import get_db
from dependencies import get_current_user
from models import Conversation, ConversationMessage, User
from prompts.qa_prompt import QA_SYSTEM_PROMPT, QA_USER_TEMPLATE
from schemas import QaChatRequest
from services.llm_service import chat_completion_stream
from services.mastery_service import get_or_create_mastery, recalculate_mastery
from utils.response import success

logger = logging.getLogger("qa_router")

router = APIRouter(prefix="/api/qa", tags=["qa"])


# ---------------- 同步端点（保留向后兼容） ----------------
@router.post("/chat")
def chat(payload: QaChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """同步问答：直接调用 chat_completion_stream 收集完整内容。"""
    conversation = None
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.user_id == user.id,
        ).first()
    if not conversation:
        conversation = Conversation(user_id=user.id, title=payload.question[:30] or "408 问答")
        db.add(conversation)
        db.flush()
    db.add(ConversationMessage(conversation_id=conversation.id, role="user", content=payload.question))
    db.commit()
    conversation_id = conversation.id

    set_db(db)
    state: dict = {
        "user_id": user.id,
        "conversation_id": conversation_id,
        "question": payload.question,
        "history": [],
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }
    try:
        state.update(detect_intent(state))
        state.update(retrieve_knowledge_node(state))
        state.update(retrieve_memory(state))
        state.update(load_mastery(state))

        subject = state.get("subject", "408")
        knowledge_point = state.get("knowledge_point", "综合")
        retrieved = state.get("retrieved_knowledge", [])
        memories = state.get("memories_used", [])
        mastery = state.get("mastery", {})
        retrieval = state.get("retrieval", {})

        knowledge_text = _format_knowledge_text(retrieved) if retrieved else "（知识库无强匹配，请基于自身知识回答）"
        memory_text = "\n".join([m.get("content", "") for m in memories]) if memories else "暂无强相关长期记忆。"
        mastery_text = (
            f"掌握度：{mastery.get('status', '未知')}，正确率：{mastery.get('correct_rate', 0)}"
            if mastery else "暂无掌握度数据。"
        )
        history_rows = state.get("history", [])
        history_lines = [f"{m.get('role', '')}: {m.get('content', '')}" for m in history_rows[-4:]]
        history_section = "\n近期对话：\n" + "\n".join(history_lines) if history_lines else ""
        seed_qs = state.get("seed_questions", [])
        similar_qs_text = ""
        if seed_qs:
            lines = [f"题目 {i + 1}: {sq.get('question_text', '')[:200]}" for i, sq in enumerate(seed_qs[:2])]
            similar_qs_text = "\n".join(lines)

        prompt = QA_USER_TEMPLATE.format(
            question=payload.question,
            history_section=history_section,
            knowledge_text=(
                f"{knowledge_text}\n\n"
                f"检索置信度：{retrieval.get('confidence', 'unknown')}。"
                "若知识库无匹配，请基于 408 统考知识自主回答；证据不足时明确提示。"
            ),
            memory_text=memory_text,
            mastery_text=mastery_text,
            similar_questions=similar_qs_text or "暂无强相关种子题。",
        )
        msgs = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        full_content = "".join(chat_completion_stream(msgs, ""))
        if not full_content.strip():
            full_content = _plain_fallback(payload.question, subject, knowledge_point)
        llm_used = bool(full_content)
    except Exception as e:
        logger.exception("chat error")
        full_content = _plain_fallback(payload.question, "408", "综合")
        subject, knowledge_point, llm_used = "408", "综合", False

    db.add(ConversationMessage(conversation_id=conversation_id, role="assistant", content=full_content))
    try:
        m = get_or_create_mastery(db, user.id, subject, knowledge_point)
        m.qa_count += 1
        recalculate_mastery(db, user.id, subject, knowledge_point)
    except Exception:
        pass
    db.commit()

    return success({
        "conversation_id": conversation_id,
        "subject": subject,
        "knowledge_point": knowledge_point,
        "answer": full_content,
        "agent_steps": state.get("agent_steps", []),
        "retrieved_knowledge": state.get("retrieved_knowledge", []),
        "retrieval": state.get("retrieval", {}),
        "memories_used": state.get("memories_used", []),
        "suggested_followups": ["生成专项题", "加入复习计划", f"更多 {knowledge_point} 练习"],
        "llm_used": llm_used,
    })


# ---------------- SSE 流式端点 ----------------
@router.get("/chat/stream")
def chat_stream(
    question: str = Query(...),
    conversation_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """SSE 流式问答。
    - 同步 generator + Queue + 后台线程，避免 async generator 在 Starlette 中 hang
    - 始终走 LLM 流式
    - 知识库命中：RAG 上下文；未命中：LLM 自主回答
    """
    conversation = None
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        ).first()
    if not conversation:
        conversation = Conversation(user_id=user.id, title=question[:30] or "408 问答")
        db.add(conversation)
        db.flush()
    db.add(ConversationMessage(conversation_id=conversation.id, role="user", content=question))
    db.commit()
    cid = conversation.id
    user_id = user.id

    def _put(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _build_state() -> tuple[dict, list[str]]:
        """运行 graph 检索阶段，返回 (state, step_sse_chunks)。"""
        set_db(db)
        state: dict = {
            "user_id": user_id,
            "conversation_id": cid,
            "question": question,
            "history": [],
            "agent_steps": [],
            "llm_used": False,
            "llm_error": "",
        }
        chunks: list[str] = []
        try:
            t0 = time.time()
            state.update(detect_intent(state))
            chunks.append(_put("step", {
                "name": "意图识别", "status": "success",
                "duration_ms": int((time.time() - t0) * 1000),
                "output": f"学科={state.get('subject')}, 知识点={state.get('knowledge_point')}",
            }))

            t0 = time.time()
            state.update(retrieve_knowledge_node(state))
            chunks.append(_put("step", {
                "name": "检索知识库", "status": "success",
                "duration_ms": int((time.time() - t0) * 1000),
                "chunks": len(state.get("retrieved_knowledge", [])),
                "confidence": state.get("retrieval", {}).get("confidence", "unknown"),
            }))

            t0 = time.time()
            state.update(retrieve_memory(state))
            chunks.append(_put("step", {
                "name": "读取长期记忆", "status": "success",
                "duration_ms": int((time.time() - t0) * 1000),
                "memories": len(state.get("memories_used", [])),
            }))

            t0 = time.time()
            state.update(load_mastery(state))
            chunks.append(_put("step", {
                "name": "加载掌握度", "status": "success",
                "duration_ms": int((time.time() - t0) * 1000),
                "mastery": state.get("mastery", {}),
            }))
        except Exception as e:
            logger.exception("graph stage error")
            chunks.append(_put("step", {"name": "检索阶段", "status": "error", "reason": str(e)}))
        return state, chunks

    def _build_prompt(state: dict) -> list[dict]:
        subject = state.get("subject", "408")
        knowledge_point = state.get("knowledge_point", "综合")
        retrieved = state.get("retrieved_knowledge", [])
        memories = state.get("memories_used", [])
        mastery = state.get("mastery", {})
        retrieval = state.get("retrieval", {})

        if retrieved:
            knowledge_text = _format_knowledge_text(retrieved)
        else:
            knowledge_text = "（知识库无强匹配，请基于 408 统考知识自主回答；不要编造来源。）"

        memory_text = "\n".join([m.get("content", "") for m in memories]) if memories else "暂无强相关长期记忆。"
        mastery_text = (
            f"掌握度：{mastery.get('status', '未知')}，正确率：{mastery.get('correct_rate', 0)}"
            if mastery else "暂无掌握度数据。"
        )
        history_rows = state.get("history", [])
        history_lines = [f"{m.get('role', '')}: {m.get('content', '')}" for m in history_rows[-4:]]
        history_section = "\n近期对话：\n" + "\n".join(history_lines) if history_lines else ""
        seed_qs = state.get("seed_questions", [])
        similar_qs_text = ""
        if seed_qs:
            lines = [f"题目 {i + 1}: {sq.get('question_text', '')[:200]}" for i, sq in enumerate(seed_qs[:2])]
            similar_qs_text = "\n".join(lines)

        prompt = QA_USER_TEMPLATE.format(
            question=question,
            history_section=history_section,
            knowledge_text=(
                f"{knowledge_text}\n\n"
                f"检索置信度：{retrieval.get('confidence', 'unknown')}。"
                "若知识库无匹配证据请基于 408 统考知识自主回答；不要编造来源编号 [Sn]。"
            ),
            memory_text=memory_text,
            mastery_text=mastery_text,
            similar_questions=similar_qs_text or "暂无强相关种子题。",
        )
        return [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], subject, knowledge_point

    def _save_assistant(content: str, subject: str, knowledge_point: str) -> None:
        try:
            db.add(ConversationMessage(conversation_id=cid, role="assistant", content=content))
            m = get_or_create_mastery(db, user_id, subject, knowledge_point)
            m.qa_count += 1
            recalculate_mastery(db, user_id, subject, knowledge_point)
            db.commit()
        except Exception:
            logger.exception("save assistant msg error")
            try:
                db.rollback()
            except Exception:
                pass

    def event_stream() -> Generator[str, None, None]:
        # 阶段 1: 同步运行 graph 检索（立即 yield 给前端）
        try:
            state, step_chunks = _build_state()
        except Exception as e:
            logger.exception("build state error")
            state = {"subject": "408", "knowledge_point": "综合", "retrieved_knowledge": []}
            step_chunks = [_put("step", {"name": "检索阶段", "status": "error", "reason": str(e)})]
        for s in step_chunks:
            yield s

        # 阶段 2: 启动 LLM 流式生成
        msgs, subject, knowledge_point = _build_prompt(state)
        yield _put("step", {"name": "LLM 生成回答", "status": "streaming"})

        q: queue.Queue = queue.Queue()
        full_content_parts: list[str] = []

        def _stream_worker():
            try:
                for tok in chat_completion_stream(msgs, ""):
                    if tok:
                        full_content_parts.append(tok)
                        q.put(("token", tok))
            except Exception as e:
                logger.exception("LLM stream error")
                q.put(("error", str(e)))
            q.put(("__DONE__", None))

        thread = threading.Thread(target=_stream_worker, daemon=True)
        thread.start()

        # 持续从队列读 token
        last_keepalive = time.time()
        while True:
            try:
                kind, val = q.get(timeout=0.05)
            except queue.Empty:
                # 每 15s 发个 keepalive 避免中间代理超时
                if time.time() - last_keepalive > 15:
                    yield ": keepalive\n\n"
                    last_keepalive = time.time()
                continue

            if kind == "__DONE__":
                break
            if kind == "error":
                yield _put("error", {"message": val})
                break
            if kind == "token":
                yield _put("token", {"text": val})

        # 拼装完整回答
        full_content = "".join(full_content_parts)
        if not full_content.strip():
            full_content = _plain_fallback(question, subject, knowledge_point)
            yield _put("token", {"text": full_content})

        # 落库
        _save_assistant(full_content, subject, knowledge_point)

        # done
        yield _put("done", {
            "answer": full_content,
            "conversation_id": cid,
            "subject": subject,
            "knowledge_point": knowledge_point,
            "llm_used": bool(full_content_parts),
            "suggested_followups": [
                f"生成 {knowledge_point} 专项题",
                "加入复习计划",
                f"复习 {knowledge_point} 知识点",
            ],
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------------- 工具函数 ----------------
def _plain_fallback(question: str, subject: str, knowledge_point: str) -> str:
    """当 LLM 不可用时的纯文本兜底（不再返回 HTML 标签）。"""
    kp = knowledge_point or "综合知识"
    return (
        f"已定位问题：{subject} / {kp}。\n"
        f"AI 服务暂时无法直接回答“{question}”，已为你保留本次问题。\n"
        "建议：1) 稍后重试；2) 切换到该知识点的题库或视频继续学习；3) 在论坛发起讨论。"
    )


def _format_knowledge_text(retrieved: list[dict]) -> str:
    return "\n\n".join(
        (
            f"[{item.get('source_id', 'S?')}] "
            f"({item.get('subject', '')}/{item.get('knowledge_point', '')}; "
            f"source={item.get('source', 'unknown')}; score={float(item.get('score', 0)):.3f})\n"
            f"{item.get('content', '')}"
        )
        for item in retrieved
    )


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.update_time.desc()).all()
    return success({
        "items": [{
            "id": row.id, "title": row.title, "summary": row.summary,
            "update_time": row.update_time.isoformat(),
        } for row in rows],
    })
