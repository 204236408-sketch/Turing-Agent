"""
<<<<<<< HEAD
问答聊天接口（半成品需要深化）

功能：
- POST /api/qa/chat    — 发起问答对话（创建/追加会话 → 调用 qa_agent → 更新掌握度）
- GET  /api/qa/history — 获取问答历史会话列表

状态：半成品需要深化。基本问答流程可用，但功能较简单：无流式响应、无上下文管理优化、
       无会话删除功能、无消息删除/编辑支持。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from agents.qa_agent import answer_question
from database import get_db
from dependencies import get_current_user
from models import Conversation, ConversationMessage, KnowledgeMastery, User
from schemas import QaChatRequest
from services.mastery_service import get_or_create_mastery, recalculate_mastery
from utils.response import AppError, success

=======
问答聊天接口

功能：
- POST /api/qa/chat        — 同步问答（保留向后兼容）
- GET  /api/qa/chat/stream — SSE 流式问答（打字机 + 步骤提示）
- GET  /api/qa/history     — 获取问答历史会话列表
"""
import asyncio
import json
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agents.qa_agent import answer_question
from agents.qa_graph import (
    detect_intent,
    load_mastery,
    retrieve_knowledge_node,
    retrieve_memory,
    set_db,
)
from database import get_db
from dependencies import get_current_user
from models import Conversation, ConversationMessage, KnowledgeMastery, User
from prompts.qa_prompt import QA_SYSTEM_PROMPT, QA_USER_TEMPLATE
from schemas import QaChatRequest
from services.llm_service import chat_completion_stream
from services.mastery_service import get_or_create_mastery, recalculate_mastery
from utils.response import AppError, success

logger = logging.getLogger("qa_router")
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/chat")
def chat(payload: QaChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = None
    if payload.conversation_id:
<<<<<<< HEAD
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id, Conversation.user_id == user.id).first()
=======
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.user_id == user.id,
        ).first()
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    if not conversation:
        conversation = Conversation(user_id=user.id, title=payload.question[:30] or "408 问答")
        db.add(conversation)
        db.flush()
    db.add(ConversationMessage(conversation_id=conversation.id, role="user", content=payload.question))
    db.commit()
    conversation_id = conversation.id

    try:
        result = answer_question(db, user.id, payload.question, conversation_id=conversation_id)
    except Exception:
        result = {
            "answer": "系统暂时无法处理该问题，请稍后重试。",
            "subject": "408",
            "knowledge_point": "综合知识",
            "agent_steps": [
                {"name": "目标识别", "output": "识别异常，降级返回"},
                {"name": "生成回答", "output": "AI 服务异常，已降级本地回答"},
            ],
            "retrieved_knowledge": [],
            "memories": [],
            "related_actions": ["重试提问", "查看知识点"],
            "llm_used": False,
        }
    db.add(ConversationMessage(conversation_id=conversation_id, role="assistant", content=result["answer"]))
    try:
        mastery = get_or_create_mastery(db, user.id, result["subject"], result["knowledge_point"])
        mastery.qa_count += 1
        recalculate_mastery(db, user.id, result["subject"], result["knowledge_point"])
    except Exception:
        pass
    db.commit()
<<<<<<< HEAD
    # 重命名字段以匹配前端需求
=======
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    response_data = {
        "conversation_id": conversation_id,
        "subject": result["subject"],
        "knowledge_point": result["knowledge_point"],
        "answer": result["answer"],
        "agent_steps": result.get("agent_steps", []),
        "retrieved_knowledge": result.get("retrieved_knowledge", []),
<<<<<<< HEAD
        "memories_used": result.get("memories", []),
        "suggested_followups": result.get("related_actions", []),
=======
        "retrieval": result.get("retrieval", {}),
        "answer_sources": result.get("answer_sources", []),
        "retrieval_confidence": result.get("retrieval_confidence", "unknown"),
        "memories_used": result.get("memories", []),
        "suggested_followups": result.get("suggested_followups", result.get("related_actions", [])),
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        "llm_used": result.get("llm_used", False),
    }
    return success(response_data)


<<<<<<< HEAD
@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.update_time.desc()).all()
    return success({"items": [{"id": row.id, "title": row.title, "summary": row.summary, "update_time": row.update_time.isoformat()} for row in rows]})
=======
@router.get("/chat/stream")
async def chat_stream(
    question: str = Query(...),
    conversation_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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

    async def event_stream():
        q: queue.Queue = queue.Queue()
        thread_done = threading.Event()

        def _put(event_type: str, data: dict) -> None:
            q.put({"event": event_type, "data": data})

        def run_qa() -> None:
            try:
                set_db(db)
                state: dict = {
                    "user_id": user.id,
                    "conversation_id": cid,
                    "question": question,
                    "history": [],
                    "agent_steps": [],
                    "llm_used": False,
                    "llm_error": "",
                }

                # ---- Phase 1: Graph retrieval nodes ----
                t0 = time.time()
                state.update(detect_intent(state))
                _put("step", {
                    "name": "意图识别",
                    "status": "success",
                    "duration_ms": int((time.time() - t0) * 1000),
                    "output": f"学科={state.get('subject')}, 知识点={state.get('knowledge_point')}",
                })

                t0 = time.time()
                state.update(retrieve_knowledge_node(state))
                retrieval = state.get("retrieval", {})
                _put("step", {
                    "name": "检索知识库",
                    "status": "success",
                    "duration_ms": int((time.time() - t0) * 1000),
                    "chunks": len(state.get("retrieved_knowledge", [])),
                    "confidence": retrieval.get("confidence", "unknown"),
                })

                t0 = time.time()
                state.update(retrieve_memory(state))
                _put("step", {
                    "name": "读取长期记忆",
                    "status": "success",
                    "duration_ms": int((time.time() - t0) * 1000),
                    "memories": len(state.get("memories_used", [])),
                })

                t0 = time.time()
                state.update(load_mastery(state))
                _put("step", {
                    "name": "加载掌握度",
                    "status": "success",
                    "duration_ms": int((time.time() - t0) * 1000),
                    "mastery": state.get("mastery", {}),
                })

                # ---- Phase 2: Generate answer ----
                subject = state.get("subject", "408")
                knowledge_point = state.get("knowledge_point", "综合")
                retrieved = state.get("retrieved_knowledge", [])
                memories = state.get("memories_used", [])
                mastery = state.get("mastery", {})

                # Low-confidence path
                if not retrieval.get("grounded", False):
                    content = _cautious_answer(
                        question, subject, knowledge_point,
                        retrieval.get("warning", "证据不足，避免生成没有来源支撑的结论。"),
                    )
                    _put("step", {
                        "name": "生成回答",
                        "status": "degraded",
                        "reason": "检索置信度不足，使用谨慎回答",
                    })
                    for char in content:
                        _put("token", {"text": char})
                    _put("done", {
                        "answer": content,
                        "conversation_id": cid,
                        "subject": subject,
                        "knowledge_point": knowledge_point,
                        "llm_used": False,
                        "llm_error": retrieval.get("warning", "low-confidence retrieval"),
                        "suggested_followups": ["补充完整题干", "查看相关知识点", "生成基础诊断题"],
                    })
                    return

                # High-confidence: stream LLM
                knowledge_text = _format_knowledge_text(retrieved)
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
                    lines = []
                    for i, sq in enumerate(seed_qs[:2]):
                        lines.append(f"题目 {i + 1}: {sq.get('question_text', '')[:200]}")
                    similar_qs_text = "\n".join(lines)

                prompt = QA_USER_TEMPLATE.format(
                    question=question,
                    history_section=history_section,
                    knowledge_text=(
                        f"{knowledge_text}\n\n"
                        f"检索置信度：{retrieval.get('confidence', 'unknown')}。"
                        "回答必须以 [S1]、[S2] 这样的编号证据为依据；证据不足时要明确提示，不要补编。"
                    ),
                    memory_text=memory_text,
                    mastery_text=mastery_text,
                    similar_questions=similar_qs_text or "暂无强相关种子题。",
                )

                msgs = [
                    {"role": "system", "content": QA_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]

                _put("step", {
                    "name": "LLM 生成回答",
                    "status": "streaming",
                })

                full_content = ""
                for token in chat_completion_stream(msgs, ""):
                    _put("token", {"text": token})
                    full_content += token

                if not full_content:
                    fallback = _cautious_answer(question, subject, knowledge_point, "LLM 返回空内容，已使用保底回答。")
                    for char in fallback:
                        _put("token", {"text": char})
                    full_content = fallback

                # Save assistant message + update mastery
                db.add(ConversationMessage(conversation_id=cid, role="assistant", content=full_content))
                try:
                    m = get_or_create_mastery(db, user.id, subject, knowledge_point)
                    m.qa_count += 1
                    recalculate_mastery(db, user.id, subject, knowledge_point)
                except Exception:
                    pass
                db.commit()

                _put("done", {
                    "answer": full_content,
                    "conversation_id": cid,
                    "subject": subject,
                    "knowledge_point": knowledge_point,
                    "llm_used": True,
                    "suggested_followups": ["生成专项题", "加入复习计划", f"更多 {knowledge_point} 练习"],
                })

            except Exception as e:
                logger.exception("chat_stream run_qa error")
                _put("error", {"message": str(e)})
            finally:
                _put(None)  # sentinel
                thread_done.set()

        ThreadPoolExecutor(max_workers=1).submit(run_qa)

        while True:
            try:
                item = q.get(timeout=0.08)
            except queue.Empty:
                await asyncio.sleep(0.01)
                continue
            if item is None:
                break
            yield f"event: {item['event']}\ndata: {json.dumps(item['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _cautious_answer(question: str, subject: str, knowledge_point: str, warning: str) -> str:
    kp = knowledge_point or "综合知识"
    return (
        f"<b>检索结论：</b>当前知识库没有找到足够可信的证据来直接回答“{question}”。<br>"
        f"<b>已定位：</b>{subject} / {kp}。<br>"
        f"<b>风险提示：</b>{warning or '证据不足，避免生成没有来源支撑的结论。'}<br>"
        "<b>建议：</b>请补充完整题干、选项或关键术语；也可以先查看该知识点的基础定义、典型题型和易错点。"
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
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
