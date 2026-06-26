"""
会话管理接口（半成品需要深化）

功能：
- GET  /api/conversation/list              — 获取当前用户所有会话列表
- GET  /api/conversation/detail/{id}       — 获取会话详情及消息列表
- GET  /api/conversation/{id}/context      — 获取会话上下文（最近消息 + 知识点摘要）
- POST /api/conversation/{id}/summary      — 生成会话摘要

状态：半成品需要深化。列表/详情/上下文/摘要功能可用；摘要生成仅做文字拼接，未接入 AI。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from agents.summary_agent import generate_conversation_summary
from database import get_db
from dependencies import get_current_user
from models import Conversation, ConversationMessage, KnowledgeMastery, User
from utils.response import AppError, success


router = APIRouter(prefix="/api/conversation", tags=["conversation"])


@router.get("/list")
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.update_time.desc()).all()
    return success({"items": [{"id": row.id, "title": row.title, "summary": row.summary, "update_time": row.update_time.isoformat() if row.update_time else None} for row in rows]})


@router.get("/detail/{conversation_id}")
def detail(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not row:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", status_code=404)
    messages = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == row.id).all()
    return success({"conversation": {"id": row.id, "title": row.title, "summary": row.summary}, "messages": [{"id": m.id, "role": m.role, "content": m.content} for m in messages]})


@router.get("/{conversation_id}/context")
def context(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取会话上下文：最近消息 + 涉及的知识点摘要"""
    row = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not row:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", status_code=404)
    # 最近 10 条消息
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == row.id)
        .order_by(ConversationMessage.id.desc())
        .limit(10)
        .all()
    )
    messages = messages[::-1]
    # 从消息内容中提取涉及的知识点（简单启发式）
    knowledge_points = []
    mastery_rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user.id).all()
    for m in mastery_rows:
        if m.knowledge_point and m.knowledge_point in row.title:
            knowledge_points.append({
                "subject": m.subject,
                "knowledge_point": m.knowledge_point,
                "status": m.final_status,
            })
    if not knowledge_points and mastery_rows:
        # 取最近的 3 个有答题记录的知识点
        active = [m for m in mastery_rows if m.total_answer_count > 0]
        active.sort(key=lambda m: m.update_time, reverse=True)
        knowledge_points = [
            {"subject": m.subject, "knowledge_point": m.knowledge_point, "status": m.final_status}
            for m in active[:3]
        ]
    return success({
        "conversation_id": row.id,
        "title": row.title,
        "messages": [{"id": m.id, "role": m.role, "content": m.content} for m in messages],
        "knowledge_points": knowledge_points,
        "message_count": len(messages),
    })


@router.post("/{conversation_id}/summary")
def summarize(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not row:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", status_code=404)
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == row.id)
        .order_by(ConversationMessage.id.asc())
        .all()
    )
    result = generate_conversation_summary([{"role": m.role, "content": m.content} for m in messages])
    row.title = result["title"]
    row.summary = result["summary"]
    db.commit()
    return success({
        "title": result["title"],
        "summary": result["summary"],
        "followup_suggestions": result["followup_suggestions"],
        "llm_used": result["llm_used"],
        "agent_steps": result.get("agent_steps", []),
    })
