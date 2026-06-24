from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import User, UserMemory
from schemas import MemoryUpdateRequest, SemanticSearchRequest
from services.rag_service import retrieve_user_memory
from utils.response import AppError, success


router = APIRouter(prefix="/api/memory", tags=["memory"])


def memory_payload(row: UserMemory) -> dict:
    return {
        "id": row.id,
        "memory_type": row.memory_type,
        "subject": row.subject,
        "knowledge_point": row.knowledge_point,
        "content": row.content,
        "evidence": row.evidence,
        "status": row.status,
    }


@router.get("/profile")
def profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(UserMemory).filter(UserMemory.user_id == user.id, UserMemory.status == "active").all()
    return success({"profile": "；".join([r.content for r in rows]) or "暂无长期画像", "memories": [memory_payload(r) for r in rows]})


@router.get("/list")
def list_memory(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(UserMemory).filter(UserMemory.user_id == user.id).order_by(UserMemory.update_time.desc()).all()
    return success({"items": [memory_payload(r) for r in rows]})


@router.get("/weak-points")
def weak_points(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(UserMemory).filter(UserMemory.user_id == user.id, UserMemory.memory_type == "weak_point", UserMemory.status == "active").all()
    return success({"items": [memory_payload(r) for r in rows]})


@router.get("/by-knowledge")
def by_knowledge(knowledge_point: str = Query("页面置换算法"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(UserMemory).filter(UserMemory.user_id == user.id, UserMemory.knowledge_point == knowledge_point).all()
    return success({"items": [memory_payload(r) for r in rows]})


@router.post("/update")
def update(payload: MemoryUpdateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = UserMemory(user_id=user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return success({"item": memory_payload(row)})


@router.post("/resolve/{memory_id}")
def resolve(memory_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(UserMemory).filter(UserMemory.id == memory_id, UserMemory.user_id == user.id).first()
    if not row:
        raise AppError("MEMORY_NOT_FOUND", "记忆不存在", status_code=404)
    row.status = "resolved"
    db.commit()
    return success({"resolved": True})


@router.post("/semantic-search")
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"items": retrieve_user_memory(db, user.id, payload.query, payload.limit)})
