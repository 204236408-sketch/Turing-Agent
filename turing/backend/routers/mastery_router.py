from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import KnowledgeMastery, KnowledgePoint, User
from services.mastery_service import recalculate_mastery, synchronize_user_mastery
from utils.response import success


router = APIRouter(prefix="/api/mastery", tags=["mastery"])


def payload(item: KnowledgeMastery) -> dict:
    return {
        "id": item.id,
        "subject": item.subject,
        "knowledge_point": item.knowledge_point,
        "final_status": item.final_status,
        "weak_score": item.weak_score,
        "total_answer_count": item.total_answer_count,
        "correct_count": item.correct_count,
        "wrong_count": item.wrong_count,
    }


@router.get("/list")
def list_mastery(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    points = db.query(KnowledgePoint).all()
    synchronize_user_mastery(db, user.id, [(point.subject, point.name) for point in points])
    db.commit()
    rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user.id).all()
    return success({"items": [payload(row) for row in rows]})


@router.get("/detail")
def detail(subject: str = Query("操作系统"), knowledge_point: str = Query("页面置换算法"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = (
        db.query(KnowledgeMastery)
        .filter(KnowledgeMastery.user_id == user.id, KnowledgeMastery.subject == subject, KnowledgeMastery.knowledge_point == knowledge_point)
        .first()
    )
    return success({"item": payload(row) if row else None})


@router.post("/recalculate")
def recalculate(subject: str = "操作系统", knowledge_point: str = "页面置换算法", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = recalculate_mastery(db, user.id, subject, knowledge_point)
    db.commit()
    return success({"item": payload(item)})


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    points = db.query(KnowledgePoint).all()
    synchronize_user_mastery(db, user.id, [(point.subject, point.name) for point in points])
    db.commit()
    rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user.id).all()
    return success({"summary": {status: sum(1 for row in rows if row.final_status == status) for status in ["未学", "掌握", "不熟", "不会", "薄弱点"]}})
