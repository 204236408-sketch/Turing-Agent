"""
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


router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/chat")
def chat(payload: QaChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = None
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id, Conversation.user_id == user.id).first()
    if not conversation:
        conversation = Conversation(user_id=user.id, title=payload.question[:30] or "408 问答")
        db.add(conversation)
        db.flush()
    db.add(ConversationMessage(conversation_id=conversation.id, role="user", content=payload.question))
    db.commit()
    conversation_id = conversation.id

    try:
        result = answer_question(db, user.id, payload.question)
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
    # 重命名字段以匹配前端需求
    response_data = {
        "conversation_id": conversation_id,
        "subject": result["subject"],
        "knowledge_point": result["knowledge_point"],
        "answer": result["answer"],
        "agent_steps": result.get("agent_steps", []),
        "retrieved_knowledge": result.get("retrieved_knowledge", []),
        "memories_used": result.get("memories", []),
        "suggested_followups": result.get("related_actions", []),
        "llm_used": result.get("llm_used", False),
    }
    return success(response_data)


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.update_time.desc()).all()
    return success({"items": [{"id": row.id, "title": row.title, "summary": row.summary, "update_time": row.update_time.isoformat()} for row in rows]})
