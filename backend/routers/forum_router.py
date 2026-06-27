"""论坛社区接口（深化版）

新增 P0+P1+P2 完善：
- P0-1/2/3  RAG + 记忆 + 掌握度
- P0-4  结构化 JSON 响应（前端 5 卡片渲染）
- P0-5  追问历史上下文
- P1-6  LangGraph 多步 Agent（论坛 AI 智能体）
- P1-7  答案校验/降级
- P1-8  写回 user_memory
- P1-9  流式输出（可选）
- P2-11 回答持久化与缓存
- P2-12 AI 回答点赞/采纳
- P2-13 与其他模块联动
- P2-14 追问判定
- P2-15 历史评论上下文
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from agents.forum_agent import (
    ai_answer_for_post,
    ai_followup_for_post,
    run_forum_graph,
    set_db as set_forum_db,
)
from database import get_db
from dependencies import get_current_user
from models import (
    ForumAiAnswer,
    ForumAiAnswerLike,
    ForumAiFollowup,
    ForumCategory,
    ForumCheckin,
    ForumComment,
    ForumLike,
    ForumPost,
    User,
)
from schemas import ForumAiFeedbackRequest, ForumCommentRequest, ForumPostRequest
from services.llm_service import chat_completion_stream
from utils.response import AppError, success

router = APIRouter(prefix="/api/forum", tags=["forum"])


def relative_time(dt: datetime) -> str:
    delta = datetime.utcnow() - dt
    if delta.days > 7:
        return dt.strftime("%m-%d")
    if delta.days > 0:
        return f"{delta.days} 天前"
    if delta.seconds >= 3600:
        return f"{delta.seconds // 3600} 小时前"
    if delta.seconds >= 60:
        return f"{delta.seconds // 60} 分钟前"
    return "刚刚"


def post_to_dict(post: ForumPost, user: User | None = None) -> dict:
    is_hot = post.like_count >= 15 and post.comment_count >= 3
    if user is None:
        user_nick = post.author_nickname if hasattr(post, 'author_nickname') else "匿名"
        user_avatar = post.author_avatar if hasattr(post, 'author_avatar') else "匿"
    else:
        user_nick = user.nickname
        user_avatar = user.nickname[0] if user.nickname else "匿"
    return {
        "id": post.id,
        "category": post.category,
        "subject": post.subject,
        "knowledge_point": post.knowledge_point,
        "title": post.title,
        "content": post.content,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "is_top": post.is_top,
        "is_hot": is_hot,
        "author": user_nick,
        "avatar": user_avatar,
        "time": relative_time(post.create_time),
        "create_time": post.create_time.isoformat(),
    }


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.query(ForumCategory).order_by(ForumCategory.sort_order).all()
    return success({"items": [{"id": r.id, "name": r.name, "description": r.description} for r in rows]})


@router.get("/posts")
def posts(
    search: str = Query(default=""),
    category: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ForumPost, User)
        .join(User, ForumPost.user_id == User.id)
        .filter(ForumPost.status == "normal")
    )
    if search:
        like = f"%{search}%"
        query = query.filter(
            ForumPost.title.ilike(like) | ForumPost.content.ilike(like)
        )
    if category and category != "全部":
        query = query.filter(ForumPost.category == category)
    total = query.count()
    rows = query.order_by(ForumPost.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for post, user in rows:
        d = post_to_dict(post, user)
        items.append(d)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/posts")
def create_post(
    payload: ForumPostRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = ForumPost(user_id=user.id, **payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return success({"post": post_to_dict(post, user)})


@router.get("/posts/{post_id}")
def post_detail(post_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(ForumPost, User)
        .join(User, ForumPost.user_id == User.id)
        .filter(ForumPost.id == post_id)
        .first()
    )
    if not row:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)
    post, user = row
    return success({"post": post_to_dict(post, user)})


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    payload: ForumPostRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = (
        db.query(ForumPost)
        .filter(ForumPost.id == post_id, ForumPost.user_id == user.id)
        .first()
    )
    if not row:
        raise AppError("POST_NOT_FOUND", "帖子不存在或无权限", status_code=404)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return success({"post": post_to_dict(row, user)})


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = (
        db.query(ForumPost)
        .filter(ForumPost.id == post_id, ForumPost.user_id == user.id)
        .first()
    )
    if not row:
        raise AppError("POST_NOT_FOUND", "帖子不存在或无权限", status_code=404)
    row.status = "deleted"
    db.commit()
    return success({"deleted": True})


@router.post("/posts/{post_id}/like")
def like(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not row:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)
    existing = db.query(ForumLike).filter(
        ForumLike.user_id == user.id,
        ForumLike.target_type == "post",
        ForumLike.target_id == post_id,
    ).first()
    if not existing:
        db.add(ForumLike(user_id=user.id, target_type="post", target_id=post_id))
        row.like_count += 1
        db.commit()
    return success({"like_count": row.like_count, "liked": True})


@router.post("/posts/{post_id}/unlike")
def unlike(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not row:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)
    existing = db.query(ForumLike).filter(
        ForumLike.user_id == user.id,
        ForumLike.target_type == "post",
        ForumLike.target_id == post_id,
    ).first()
    if existing:
        db.delete(existing)
        row.like_count = max(0, row.like_count - 1)
        db.commit()
    return success({"like_count": row.like_count, "liked": False})


@router.get("/posts/{post_id}/comments")
def comments(post_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ForumComment, User)
        .join(User, ForumComment.user_id == User.id)
        .filter(ForumComment.post_id == post_id)
        .order_by(ForumComment.create_time)
        .all()
    )
    return success({
        "items": [
            {
                "id": c.id,
                "content": c.content,
                "parent_id": c.parent_id,
                "author": u.nickname,
                "avatar": u.nickname[0] if u.nickname else "匿",
                "create_time": relative_time(c.create_time),
            }
            for c, u in rows
        ]
    })


@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    payload: ForumCommentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)
    comment = ForumComment(
        post_id=post_id,
        user_id=user.id,
        parent_id=payload.parent_id,
        content=payload.content,
    )
    post.comment_count += 1
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return success({
        "comment_id": comment.id,
        "comment_count": post.comment_count,
        "author": user.nickname,
        "avatar": user.nickname[0] if user.nickname else "匿",
        "content": comment.content,
        "create_time": "刚刚",
    })


@router.post("/comments/{comment_id}/reply")
def reply(
    comment_id: int,
    payload: ForumCommentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parent = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not parent:
        raise AppError("COMMENT_NOT_FOUND", "评论不存在", status_code=404)
    comment = ForumComment(
        post_id=parent.post_id,
        user_id=user.id,
        parent_id=comment_id,
        content=payload.content,
    )
    db.add(comment)
    db.commit()
    return success({"comment_id": comment.id})


# ---------------- AI 回答主入口（P0-1 ~ P2-15 全部集成） ----------------

@router.post("/posts/{post_id}/ai-answer")
def ai_answer(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI 回答帖子主入口。"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)

    set_forum_db(db)
    post_dict = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "subject": post.subject or "",
        "knowledge_point": post.knowledge_point or "",
    }
    result = run_forum_graph(
        db=db,
        post=post_dict,
        user_id=user.id,
        followup_question="",
        answer_id=None,
    )
    answer = result.get("answer", {}) or {}
    return success({
        "answer_id": result.get("answer_id"),
        "memory_id": result.get("memory_id"),
        "answer": answer,
        "structured": answer,
        "subject": result.get("subject", ""),
        "knowledge_point": result.get("knowledge_point", ""),
        "retrieval": result.get("retrieval", {}),
        "agent_steps": result.get("agent_steps", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "should_followup": result.get("should_followup", False),
        "followup_hint": result.get("followup_hint", ""),
        "user_profile": result.get("user_profile", {}),
    })


@router.post("/posts/{post_id}/ai-answer-stream")
def ai_answer_stream(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI 回答流式输出（SSE，P1-9）。"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)

    set_forum_db(db)
    post_dict = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "subject": post.subject or "",
        "knowledge_point": post.knowledge_point or "",
    }
    result = run_forum_graph(
        db=db,
        post=post_dict,
        user_id=user.id,
        followup_question="",
        answer_id=None,
    )
    answer = result.get("answer", {}) or {}
    text = json_dumps_pretty(answer)

    def _gen():
        chunk_size = 80
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.post("/posts/{post_id}/ai-followup")
def ai_followup(
    post_id: int,
    payload: ForumCommentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI 追问接口（P0-5, P1-6, P2-14, P2-15）。"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)

    # 找该帖子最近的 AI 回答
    last_answer = (
        db.query(ForumAiAnswer)
        .filter(ForumAiAnswer.post_id == post_id, ForumAiAnswer.is_deleted == False)
        .order_by(ForumAiAnswer.create_time.desc())
        .first()
    )
    answer_id = last_answer.id if last_answer else None

    post_dict = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "subject": post.subject or "",
        "knowledge_point": post.knowledge_point or "",
    }
    set_forum_db(db)
    result = ai_followup_for_post(
        db=db,
        post=post_dict,
        user_id=user.id,
        followup_question=payload.content,
        answer_id=answer_id,
    )
    return success({
        "answer": result.get("answer", {}),
        "structured": result.get("answer", {}),
        "should_followup": result.get("should_followup", False),
        "followup_hint": result.get("followup_hint", ""),
        "agent_steps": result.get("agent_steps", []),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
    })


# ---------------- P2-12 点赞/采纳 ----------------

@router.post("/ai-answer/like")
def like_ai_answer(
    payload: ForumAiFeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """对 AI 回答点赞/采纳（P2-12）。"""
    answer = db.query(ForumAiAnswer).filter(
        ForumAiAnswer.id == payload.answer_id,
        ForumAiAnswer.is_deleted == False,
    ).first()
    if not answer:
        raise AppError("ANSWER_NOT_FOUND", "回答不存在", status_code=404)

    existing = db.query(ForumAiAnswerLike).filter(
        ForumAiAnswerLike.user_id == user.id,
        ForumAiAnswerLike.answer_id == payload.answer_id,
    ).first()

    if existing:
        existing.is_deleted = False
        existing.create_time = datetime.utcnow()
    else:
        db.add(ForumAiAnswerLike(
            user_id=user.id,
            answer_id=payload.answer_id,
        ))

    answer.like_count = (answer.like_count or 0) + 1
    if payload.is_helpful:
        answer.is_accepted = True

    db.commit()
    return success({
        "answer_id": answer.id,
        "like_count": answer.like_count,
        "is_accepted": answer.is_accepted,
    })


@router.post("/ai-answer/unlike")
def unlike_ai_answer(
    payload: ForumAiFeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消 AI 回答点赞。"""
    existing = db.query(ForumAiAnswerLike).filter(
        ForumAiAnswerLike.user_id == user.id,
        ForumAiAnswerLike.answer_id == payload.answer_id,
    ).first()
    if existing:
        existing.is_deleted = True
    answer = db.query(ForumAiAnswer).filter(ForumAiAnswer.id == payload.answer_id).first()
    if answer and answer.like_count > 0:
        answer.like_count -= 1
    db.commit()
    return success({"answer_id": payload.answer_id, "like_count": answer.like_count if answer else 0})


# ---------------- P2-13 模块联动（跳转） ----------------

@router.get("/posts/{post_id}/ai-actions")
def ai_actions(post_id: int, db: Session = Depends(get_db)):
    """获取 AI 回答的行动链接（出题/视频/错题本），前端用于按钮跳转。"""
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise AppError("POST_NOT_FOUND", "帖子不存在", status_code=404)
    subject = post.subject or ""
    kp = post.knowledge_point or ""

    actions = [
        {
            "type": "question",
            "label": "🎯 生成专项题",
            "url": "/index.html?page=question",
            "params": {"subject": subject, "knowledge_point": kp, "mode": "knowledge_point"},
        },
        {
            "type": "video",
            "label": "🎬 看视频讲解",
            "url": "/index.html?page=knowledge",
            "params": {"subject": subject, "knowledge_point": kp},
        },
        {
            "type": "mistake",
            "label": "📒 加入错题本",
            "url": "/index.html?page=mistake",
            "params": {"subject": subject, "knowledge_point": kp},
        },
        {
            "type": "qa",
            "label": "💬 深入问答",
            "url": "/index.html?page=qa",
            "params": {"subject": subject, "knowledge_point": kp},
        },
    ]
    return success({"items": actions, "subject": subject, "knowledge_point": kp})


# ---------------- 追问历史 ----------------

@router.get("/posts/{post_id}/ai-followup-history")
def followup_history(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取帖子 AI 追问历史。"""
    last_answer = (
        db.query(ForumAiAnswer)
        .filter(ForumAiAnswer.post_id == post_id, ForumAiAnswer.is_deleted == False)
        .order_by(ForumAiAnswer.create_time.desc())
        .first()
    )
    if not last_answer:
        return success({"items": []})

    rows = (
        db.query(ForumAiFollowup)
        .filter(
            ForumAiFollowup.answer_id == last_answer.id,
            ForumAiFollowup.user_id == user.id,
            ForumAiFollowup.is_deleted == False,
        )
        .order_by(ForumAiFollowup.create_time)
        .all()
    )
    return success({
        "answer_id": last_answer.id,
        "items": [
            {
                "id": r.id,
                "question": r.question,
                "answer": r.answer,
                "knowledge_point": r.knowledge_point,
                "create_time": relative_time(r.create_time),
            }
            for r in rows
        ],
    })


# ---------------- 原有辅助接口 ----------------

@router.get("/hot")
def hot(db: Session = Depends(get_db)):
    rows = (
        db.query(ForumPost, User)
        .join(User, ForumPost.user_id == User.id)
        .filter(ForumPost.status == "normal")
        .order_by(
            (ForumPost.like_count * 2 + ForumPost.comment_count * 3).desc(),
            ForumPost.create_time.desc(),
        )
        .limit(5)
        .all()
    )
    items = []
    for post, user in rows:
        d = post_to_dict(post, user)
        d["heat_score"] = post.like_count * 2 + post.comment_count * 3
        items.append(d)
    return success({"items": items, "rule": "按 点赞数×2 + 评论数×3 降序排列，取前5"})


@router.get("/checkin/status")
def checkin_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    checked_today = (
        db.query(ForumCheckin)
        .filter(ForumCheckin.user_id == user.id, ForumCheckin.checkin_date == today)
        .first()
        is not None
    )
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_begin = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    weekly_count = (
        db.query(func.count(ForumCheckin.id))
        .filter(ForumCheckin.user_id == user.id, ForumCheckin.create_time >= week_begin)
        .scalar()
        or 0
    )
    consecutive_days = 0
    for offset in range(365):
        d = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y-%m-%d")
        exists = (
            db.query(ForumCheckin)
            .filter(ForumCheckin.user_id == user.id, ForumCheckin.checkin_date == d)
            .first()
        )
        if exists:
            consecutive_days += 1
        else:
            break
    return success({
        "checked_today": checked_today,
        "weekly_count": weekly_count,
        "consecutive_days": consecutive_days,
    })


@router.post("/checkin")
def checkin(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    existing = (
        db.query(ForumCheckin)
        .filter(ForumCheckin.user_id == user.id, ForumCheckin.checkin_date == today)
        .first()
    )
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_begin = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    if existing:
        weekly_count = (
            db.query(func.count(ForumCheckin.id))
            .filter(ForumCheckin.user_id == user.id, ForumCheckin.create_time >= week_begin)
            .scalar()
            or 0
        )
        return success({
            "checked": True,
            "already_checked": True,
            "weekly_count": weekly_count,
            "message": "今天已打卡",
        })

    db.add(ForumCheckin(user_id=user.id, checkin_date=today))
    db.commit()
    weekly_count = (
        db.query(func.count(ForumCheckin.id))
        .filter(ForumCheckin.user_id == user.id, ForumCheckin.create_time >= week_begin)
        .scalar()
        or 0
    )
    return success({
        "checked": True,
        "already_checked": False,
        "weekly_count": weekly_count,
        "message": "今日论坛学习打卡成功",
    })


@router.get("/my-posts")
def my_posts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        db.query(ForumPost)
        .filter(ForumPost.user_id == user.id, ForumPost.status == "normal")
        .all()
    )
    return success({"items": [post_to_dict(p, user) for p in rows]})


def json_dumps_pretty(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)
