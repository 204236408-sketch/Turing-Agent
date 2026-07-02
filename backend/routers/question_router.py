"""
题目管理接口（半成品需要深化）

功能：
- POST /api/questions/generate              — 手动指定参数生成题目
- GET  /api/questions/recommendations        — 获取智能推荐题目列表
- POST /api/questions/generate-smart         — 按推荐模式智能生成题目
- GET  /api/questions/session/{id}           — 获取出题批次的详情
- GET  /api/questions/detail/{id}            — 题目详情
- GET  /api/questions/{id}/hints             — 获取题目提示
- GET  /api/questions/{id}/videos            — 获取推荐视频
- POST /api/questions/{id}/mastery           — 针对某题设置掌握状态
- POST /api/questions/mastery                — 通用设置掌握状态
- POST /api/questions/{id}/interaction       — 记录题目交互（空实现）

状态：半成品需要深化。出题、推荐、掌握度功能完整；交互接口为空实现，
      缺少题目编辑、删除、批量操作等功能。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from agents.question_agent import generate_questions
from database import get_db
from dependencies import get_current_user, get_current_user_optional
from models import AnswerRecord, KnowledgePoint, Question, QuestionFeedback, QuestionGenerationSession, User
from schemas import MasteryFeedbackRequest, QuestionFeedbackRequest, QuestionGenerateRequest, SmartQuestionGenerateRequest
from services.mastery_service import apply_manual_feedback
from services.recommendation_service import build_smart_recommendations, resolve_smart_recommendation
from services.serialization import question_to_dict
from services.video_service import recommend_videos
from utils.response import AppError, success


router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/generate")
def generate(payload: QuestionGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = generate_questions(
        db,
        user.id,
        payload.mode,
        payload.subject,
        payload.knowledge_point,
        payload.difficulty,
        payload.question_type,
        payload.count,
        scope=payload.scope or "",
        chapter=payload.chapter or "",
        chapter_id=payload.chapter_id,
        reference_text=payload.reference_text or "",
        reference_answer=payload.reference_answer or "",
        source=payload.source or "manual",
    )
    db.commit()
    return success(data)


@router.get("/recommendations")
def recommendations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"items": build_smart_recommendations(db, user.id)})


@router.get("/history")
def history(
    knowledge_point_id: int | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AnswerRecord).filter(AnswerRecord.user_id == user.id)
    if knowledge_point_id:
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if point:
            point_name = point.section or point.name
            query = query.filter(AnswerRecord.subject == point.subject, AnswerRecord.knowledge_point.in_([point_name, point.name]))
    rows = query.order_by(AnswerRecord.create_time.desc()).limit(max(1, min(limit, 50))).all()
    q_ids = [row.question_id for row in rows if row.question_id]
    questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()} if q_ids else {}
    return success({
        "items": [
            {
                "id": row.id,
                "question_id": row.question_id,
                "question_text": (questions.get(row.question_id).question_text if questions.get(row.question_id) else "")[:220],
                "question_type": questions.get(row.question_id).question_type if questions.get(row.question_id) else "",
                "difficulty": questions.get(row.question_id).difficulty if questions.get(row.question_id) else "",
                "knowledge_point": row.knowledge_point,
                "user_answer": row.user_answer,
                "standard_answer": row.standard_answer,
                "is_correct": row.is_correct,
                "feedback": row.feedback,
                "create_time": row.create_time.isoformat(sep=" ", timespec="minutes") if row.create_time else "",
            }
            for row in rows
        ]
    })


@router.post("/generate-smart")
def generate_smart(payload: SmartQuestionGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    recommendation = resolve_smart_recommendation(db, user.id, payload.recommend_mode)
    data = generate_questions(
        db,
        user.id,
        recommendation["mode"],
        recommendation["subject"],
        recommendation["knowledge_point"],
        recommendation["difficulty"],
        recommendation["question_type"],
        payload.count,
        recommendation_reason=recommendation["reason"],
    )
    db.commit()
    return success({**data, "recommendation": recommendation})


@router.get("/session/{session_id}")
def session_detail(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(QuestionGenerationSession).filter(QuestionGenerationSession.id == session_id, QuestionGenerationSession.user_id == user.id).first()
    if not session:
        raise AppError("SESSION_NOT_FOUND", "出题批次不存在", status_code=404)
    return success({"session_id": session.id, "questions": [question_to_dict(q) for q in session.questions]})


@router.get("/detail/{question_id}")
def detail(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)
    return success({"question": question_to_dict(question)})


@router.get("/{question_id}/hints")
def hints(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)
    return success({"hints": question_to_dict(question)["hints"]})


@router.get("/{question_id}/videos")
def videos(
    question_id: int,
    limit: int = 3,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_optional),
):
    """
    获取题目推荐视频（增强版）

    - limit: 返回视频数量，默认3条
    - 返回结构化结果，包含关键词提取信息和推荐理由
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)

    # 使用增强版推荐
    from services.video_service import recommend_videos_v2
    # 组装完整题目文本（含选项）
    full_question_text = question.question_text
    options = question.options_json or []
    if options:
        # 兼容两种格式：dict 列表 或 字符串列表
        opt_strs = []
        for o in options:
            if isinstance(o, dict):
                k = o.get("key", "")
                t = o.get("text", "")
                if t:
                    opt_strs.append(f"{k}. {t}" if k else t)
            elif isinstance(o, str) and o.strip():
                opt_strs.append(o.strip())
        if opt_strs:
            full_question_text = f"{question.question_text}\n" + "  ".join(opt_strs)
    result = recommend_videos_v2(
        db,
        question_id=question_id,
        subject=question.subject,
        knowledge_point=question.knowledge_point or "",
        question_text=full_question_text,
        options=options,
        limit=limit,
        use_llm=True,
        user_id=user.id if user else None,
    )

    return success({
        "items": result.get("items", []),
        "subject": question.subject,
        "knowledge_point": question.knowledge_point or "",
        "llm_keywords": result.get("llm_keywords", []),
        "keyword_extract_method": result.get("keyword_extract_method", "unknown"),
        "total_candidates": result.get("total_candidates", 0),
        "cache_hit": result.get("cache_hit", False),
        "question_type": result.get("question_type", "未知"),
        "difficulty_hint": result.get("difficulty_hint", "中等"),
    })


@router.post("/{question_id}/mastery")
def mastery_by_question(question_id: int, payload: MasteryFeedbackRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)
    item = apply_manual_feedback(db, user.id, question.subject, question.knowledge_point, payload.status, payload.mistake_id, question.id)
    db.commit()
    return success({"status": item.final_status, "weak_score": item.weak_score})


@router.post("/mastery")
def mastery(payload: MasteryFeedbackRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = apply_manual_feedback(db, user.id, payload.subject, payload.knowledge_point, payload.status, payload.mistake_id, payload.question_id)
    db.commit()
    return success({"status": item.final_status, "weak_score": item.weak_score})


@router.post("/{question_id}/interaction")
def interaction(question_id: int):
    return success({"question_id": question_id, "logged": True})


@router.post("/feedback")
def submit_feedback(
    payload: QuestionFeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """用户对题目质量反馈；累 3 次 wrong_answer 自动降级（is_verified=False、quality_flag=deprecated）。

    同时维护 Question.reported_count / reported_reason / last_reported_at，
    供后续出题/题库参考环节做"被多个用户标错的题降权"使用。
    """
    q = db.query(Question).filter(Question.id == payload.question_id, Question.is_deleted == False).first()
    if not q:
        raise AppError(404, "题目不存在")

    from datetime import datetime as _dt
    db.add(QuestionFeedback(
        question_id=q.id,
        user_id=user.id,
        feedback_type=payload.feedback_type,
        content=(payload.content or "")[:500],
    ))

    # 累计 3 次"答案有误"反馈：自动降级
    wrong_count = 0
    if payload.feedback_type == "wrong_answer":
        wrong_count = (
            db.query(QuestionFeedback)
            .filter(QuestionFeedback.question_id == q.id, QuestionFeedback.feedback_type == "wrong_answer", QuestionFeedback.is_deleted == False)
            .count()
        )
        if wrong_count >= 3:
            q.is_verified = False
            q.quality_flag = "deprecated"
            q.quality_score = 0
        elif wrong_count >= 1:
            q.quality_flag = "disputed"

    # 维护 Question 表上的累计反馈数（供出题参考池过滤用）
    q.reported_count = (q.reported_count or 0) + 1
    q.reported_reason = (payload.content or q.reported_reason or "")[:255]
    q.last_reported_at = _dt.utcnow()

    db.commit()
    return success({
        "question_id": q.id,
        "received": True,
        "reported_count": q.reported_count,
        "quality_flag": q.quality_flag,
    })
