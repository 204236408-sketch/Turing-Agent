"""
错题本接口（半成品需要深化）

功能：
- GET  /api/mistakes                  — 错题列表（含关联题目与 OCR 还原）
- GET  /api/mistakes/notebook         — 错题本（按掌握状态筛选，含详细字段）
- GET  /api/mistakes/{id}             — 错题详情
- POST /api/mistakes/cause-confirm    — 确认错题原因（调用 mistake_agent）
- POST /api/mistakes/retrain          — 生成同类训练建议（当前为桩，返回固定值）
- POST /api/mistakes/{id}/mastery     — 设置错题掌握状态

状态：半成品需要深化。错题列表/本/详情结构良好，cause-confirm 有 Agent 支撑；
      retrain 接口仅返回固定 mock 值，detail 返回字段偏少，缺少错题统计分析接口。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from agents.mistake_agent import confirm_cause
from agents.question_agent import generate_questions
from database import get_db
from dependencies import get_current_user
from models import AnswerRecord, KnowledgePoint, Mistake, Question, User
from schemas import CauseConfirmRequest, MasteryFeedbackRequest, RetrainRequest
from services.mastery_service import apply_manual_feedback
from utils.response import AppError, success


router = APIRouter(prefix="/api/mistakes", tags=["mistakes"])


def _ocr_question_text(error_reason: str) -> str:
    if not error_reason:
        return ""
    marker = "从图片识别到题目："
    if marker not in error_reason:
        return ""
    text = error_reason.split(marker, 1)[1]
    for stop in ("\n用户答案：", "\nAgent 推断标准答案：", "\n答案解析：", "\n错因分析："):
        if stop in text:
            text = text.split(stop, 1)[0]
    return text.strip()


def _dedup_mistakes(mistakes: list, db: Session = None) -> list:
    """错题按 (subject, knowledge_point, 题干特征) 去重,只保留最新一条。

    用于题本展示场景:同一道题多次被 OCR 导入 / 答错时,不会在题本里重复刷屏。
    """
    if not mistakes:
        return []
    import re
    # 一次性把关联 Question 的题干预热,避免 N+1
    qid_text: dict = {}
    if db is not None:
        qids = {m.question_id for m in mistakes if m.question_id}
        if qids:
            for r in db.query(Question).filter(Question.id.in_(qids)).all():
                qid_text[r.id] = r.question_text or ""
    seen: dict[str, object] = {}
    for m in mistakes:
        if m.question_id and m.question_id in qid_text:
            q_text = qid_text[m.question_id]
        else:
            q_text = _ocr_question_text(m.error_reason or "")
        # 归一化:去除空格/标点,只保留前 80 字符作 key
        norm = re.sub(r"\s+", "", q_text)[:80]
        if not norm:
            # 退化到 subject+kp 作 key,避免空 key 把所有题都并掉
            norm = f"{(m.subject or '').strip()}|{(m.knowledge_point or '').strip()}"
        key = f"{(m.subject or '').strip()}|{(m.knowledge_point or '').strip()}|{norm}"
        existing = seen.get(key)
        if existing is None or (m.create_time and existing.create_time and m.create_time > existing.create_time):
            seen[key] = m
    return list(seen.values())


@router.get("")
def list_mistakes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    knowledge_point_id: int | None = Query(default=None),
    chapter_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Mistake).filter(Mistake.user_id == user.id)
    if knowledge_point_id:
        point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if point:
            query = query.filter(Mistake.subject == point.subject, Mistake.knowledge_point.in_([point.section or point.name, point.name]))
    elif chapter_id:
        chapter = db.query(KnowledgePoint).filter(KnowledgePoint.id == chapter_id).first()
        if chapter:
            child_names = [
                row.section or row.name
                for row in db.query(KnowledgePoint).filter(
                    KnowledgePoint.subject_id == chapter.subject_id,
                    KnowledgePoint.name == chapter.name,
                    KnowledgePoint.is_deleted == False,
                ).all()
            ]
            query = query.filter(Mistake.subject == chapter.subject, Mistake.knowledge_point.in_(child_names + [chapter.name]))
    total = query.count()
    rows = query.order_by(Mistake.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    q_ids = [r.question_id for r in rows if r.question_id]
    questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()} if q_ids else {}
    items = []
    for r in rows:
        q = questions.get(r.question_id)
        items.append({
            "id": r.id,
            "subject": r.subject,
            "knowledge_point": r.knowledge_point,
            "error_type": r.error_type,
            "suggestion": r.suggestion,
            "question_text": q.question_text if q else "",
            "question_id": r.question_id,
        })
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/notebook")
def notebook(
    status: str = Query("不熟,不会"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    status_list = [s.strip() for s in status.split(",")]
    all_user_mistakes = db.query(Mistake).filter(
        Mistake.user_id == user.id,
        Mistake.status == "active",
    ).order_by(Mistake.create_time.desc()).all()

    # 先按“同一道题”合并，再按最新 mastery_status 分发到题本。
    # 同题如果最新状态是“不会”，就不会继续出现在“不熟题本”。
    unique_all_mistakes = _dedup_mistakes(all_user_mistakes, db=db)
    unique_mistakes = [m for m in unique_all_mistakes if m.mastery_status in status_list]
    total = len(unique_mistakes)
    start = (page - 1) * page_size
    mistakes = unique_mistakes[start:start + page_size]

    total_unfamiliar = sum(1 for m in unique_all_mistakes if m.mastery_status == "不熟")
    total_unknown = sum(1 for m in unique_all_mistakes if m.mastery_status == "不会")
    total_all = len(unique_all_mistakes)

    q_ids = [m.question_id for m in mistakes if m.question_id]
    questions = {q.id: q for q in db.query(Question).filter(Question.id.in_(q_ids)).all()} if q_ids else {}

    ar_ids = [m.answer_record_id for m in mistakes if m.answer_record_id]
    answer_records = {r.id: r for r in db.query(AnswerRecord).filter(AnswerRecord.id.in_(ar_ids)).all()} if ar_ids else {}

    result = []
    for m in mistakes:
        q = questions.get(m.question_id)
        rec = answer_records.get(m.answer_record_id) if m.answer_record_id else None
        question_text = q.question_text if q else _ocr_question_text(m.error_reason)
        standard_answer = q.standard_answer if q else ""
        explanation = q.explanation if q else ""
        if not standard_answer and "Agent 推断标准答案：" in (m.error_reason or ""):
            standard_answer = m.error_reason.split("Agent 推断标准答案：", 1)[1].split("\n", 1)[0].strip()
        if not explanation and "答案解析：" in (m.error_reason or ""):
            explanation = m.error_reason.split("答案解析：", 1)[1].split("\n", 1)[0].strip()
        result.append({
            "id": m.id,
            "subject": m.subject,
            "knowledge_point": m.knowledge_point,
            "mastery_status": m.mastery_status,
            "error_type": m.error_type,
            "error_reason": m.error_reason,
            "suggestion": m.suggestion,
            "input_type": m.input_type,
            "create_time": m.create_time.isoformat() if m.create_time else None,
            "question_id": m.question_id,
            "question_text": question_text,
            "options_json": q.options_json if q else "[]",
            "standard_answer": standard_answer,
            "explanation": explanation,
            "user_answer": rec.user_answer if rec else "",
            "is_correct": rec.is_correct if rec else False,
            "mastery_feedback": rec.mastery_feedback if rec else "",
        })
    return success({
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": {
            "unfamiliar": total_unfamiliar,
            "unknown": total_unknown,
            "total": total_all,
        },
    })


@router.get("/{mistake_id}")
def detail(mistake_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Mistake).filter(Mistake.id == mistake_id, Mistake.user_id == user.id).first()
    if not row:
        raise AppError("MISTAKE_NOT_FOUND", "错题不存在", status_code=404)
    q = db.query(Question).filter(Question.id == row.question_id).first()
    rec = None
    if row.answer_record_id:
        rec = db.query(AnswerRecord).filter(AnswerRecord.id == row.answer_record_id).first()
    return success({
        "item": {
            "id": row.id,
            "subject": row.subject,
            "knowledge_point": row.knowledge_point,
            "error_type": row.error_type,
            "error_reason": row.error_reason,
            "suggestion": row.suggestion,
            "mastery_status": row.mastery_status,
            "input_type": row.input_type,
            "create_time": row.create_time.isoformat() if row.create_time else None,
            "question_id": row.question_id,
            "question_text": q.question_text if q else "",
            "standard_answer": q.standard_answer if q else "",
            "explanation": q.explanation if q else "",
            "user_answer": rec.user_answer if rec else "",
            "is_correct": rec.is_correct if rec else False,
        }
    })


@router.post("/cause-confirm")
def cause_confirm(payload: CauseConfirmRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = confirm_cause(db, user.id, payload.answer_record_id, payload.error_types, payload.user_note, payload.evidence_source, payload.agent_suggested_types)
    db.commit()
    return success(data)


@router.post("/retrain")
def retrain(payload: RetrainRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mistake = db.query(Mistake).filter(Mistake.id == payload.mistake_id, Mistake.user_id == user.id).first()
    if not mistake:
        raise AppError("MISTAKE_NOT_FOUND", "错题不存在", status_code=404)
    data = generate_questions(
        db=db,
        user_id=user.id,
        mode="错题重练",
        subject=mistake.subject or "",
        knowledge_point=mistake.knowledge_point or "",
        difficulty="中等",
        question_type="选择题",
        count=3,
        recommendation_reason=f"基于错题（{mistake.error_type}）的同类训练",
    )
    db.commit()
    return success({
        "mistake_id": mistake.id,
        "subject": mistake.subject,
        "knowledge_point": mistake.knowledge_point,
        "error_type": mistake.error_type,
        "session_id": data.get("session_id"),
        "questions": data.get("questions", []),
        "count": len(data.get("questions", [])),
    })


@router.post("/{mistake_id}/mastery")
def set_mistake_mastery(mistake_id: int, payload: MasteryFeedbackRequest, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    m = db.query(Mistake).filter(Mistake.id == mistake_id, Mistake.user_id == user.id).first()
    if not m:
        raise AppError("MISTAKE_NOT_FOUND", "错题不存在", status_code=404)
    item = apply_manual_feedback(db, user.id, m.subject, m.knowledge_point, payload.status, mistake_id)
    db.commit()
    return success({"status": item.final_status, "weak_score": item.weak_score})
