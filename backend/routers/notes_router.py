from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from database import engine, get_db
from dependencies import get_current_user
from models import KnowledgePoint, Note, NoteShare, User
from utils.response import AppError, success


router = APIRouter(prefix="/api/notes", tags=["notes"])


def ensure_note_tables() -> None:
    Note.__table__.create(bind=engine, checkfirst=True)
    NoteShare.__table__.create(bind=engine, checkfirst=True)


def note_to_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "subject_id": note.subject_id,
        "knowledge_point_id": note.knowledge_point_id,
        "subject": note.subject,
        "chapter": note.chapter,
        "knowledge_point": note.knowledge_point,
        "title": note.title,
        "content": note.content,
        "summary": (note.content or "")[:120],
        "create_time": note.create_time.isoformat(sep=" ", timespec="minutes") if note.create_time else "",
        "update_time": note.update_time.isoformat(sep=" ", timespec="minutes") if note.update_time else "",
    }


def _point_scope(db: Session, knowledge_point_id: int) -> KnowledgePoint:
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id, KnowledgePoint.is_deleted == False).first()
    if not point:
        raise AppError("KNOWLEDGE_POINT_NOT_FOUND", "知识点不存在", status_code=404)
    return point


def _chapter_scope(db: Session, chapter_id: int) -> KnowledgePoint:
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == chapter_id, KnowledgePoint.is_deleted == False).first()
    if not point:
        raise AppError("CHAPTER_NOT_FOUND", "章节不存在", status_code=404)
    return point


@router.get("")
def list_notes(
    knowledge_point_id: int | None = Query(default=None),
    chapter_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_note_tables()
    query = db.query(Note).filter(Note.user_id == user.id, Note.is_deleted == False)
    if knowledge_point_id:
        point = _point_scope(db, knowledge_point_id)
        point_name = point.section or point.name
        query = query.filter(
            Note.subject == point.subject,
            Note.chapter == point.name,
            Note.knowledge_point == point_name,
        )
    elif chapter_id:
        chapter = _chapter_scope(db, chapter_id)
        query = query.filter(Note.subject == chapter.subject, Note.chapter == chapter.name)
    rows = query.order_by(Note.update_time.desc(), Note.id.desc()).all()
    return success({"items": [note_to_dict(row) for row in rows], "total": len(rows)})


@router.post("")
def create_note(payload: dict = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_note_tables()
    knowledge_point_id = payload.get("knowledge_point_id")
    point = _point_scope(db, int(knowledge_point_id)) if knowledge_point_id else None
    subject = payload.get("subject") or (point.subject if point else "")
    chapter = payload.get("chapter") or (point.name if point else "")
    knowledge_point = payload.get("knowledge_point") or ((point.section or point.name) if point else "")
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title or not content:
        raise AppError("NOTE_REQUIRED", "标题和内容不能为空")
    note = Note(
        user_id=user.id,
        subject_id=point.subject_id if point else payload.get("subject_id"),
        knowledge_point_id=point.id if point else knowledge_point_id,
        subject=subject[:64],
        chapter=chapter[:128],
        knowledge_point=knowledge_point[:128],
        title=title[:100],
        content=content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return success({"note": note_to_dict(note)})


@router.put("/{note_id}")
def update_note(note_id: int, payload: dict = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_note_tables()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id, Note.is_deleted == False).first()
    if not note:
        raise AppError("NOTE_NOT_FOUND", "笔记不存在", status_code=404)
    if "title" in payload:
        note.title = (payload.get("title") or note.title)[:100]
    if "content" in payload:
        note.content = payload.get("content") or note.content
    db.commit()
    db.refresh(note)
    return success({"note": note_to_dict(note)})


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_note_tables()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id, Note.is_deleted == False).first()
    if not note:
        raise AppError("NOTE_NOT_FOUND", "笔记不存在", status_code=404)
    note.is_deleted = True
    db.commit()
    return success({"deleted": True})


@router.post("/{note_id}/share")
def share_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_note_tables()
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user.id, Note.is_deleted == False).first()
    if not note:
        raise AppError("NOTE_NOT_FOUND", "笔记不存在", status_code=404)
    share = NoteShare(
        note_id=note.id,
        user_id=user.id,
        share_id=uuid.uuid4().hex[:16],
        share_title=note.title,
        share_summary=(note.content or "")[:180],
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return success({"share_id": share.share_id, "share_url": f"/note_share.html?share_id={share.share_id}"})


@router.get("/share/{share_id}")
def share_detail(share_id: str, db: Session = Depends(get_db)):
    ensure_note_tables()
    share = db.query(NoteShare).filter(NoteShare.share_id == share_id, NoteShare.is_public == True).first()
    if not share:
        raise AppError("SHARE_NOT_FOUND", "分享不存在", status_code=404)
    note = db.query(Note).filter(Note.id == share.note_id, Note.is_deleted == False).first()
    if not note:
        raise AppError("NOTE_NOT_FOUND", "笔记不存在", status_code=404)
    user = db.query(User).filter(User.id == share.user_id).first()
    return success(
        {
            "share": {
                "share_id": share.share_id,
                "title": share.share_title or note.title,
                "summary": share.share_summary,
                "create_time": share.create_time.isoformat(sep=" ", timespec="minutes") if share.create_time else "",
                "author": user.nickname if user else "408 同学",
                "note": note_to_dict(note),
            }
        }
    )
