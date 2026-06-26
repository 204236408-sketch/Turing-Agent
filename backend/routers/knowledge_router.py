"""
知识点接口（已完成可复用）

功能：
- GET /api/knowledge/graph           — 获取全量知识图谱（树状结构，含掌握状态和着色）
- GET /api/knowledge/high-frequency  — 获取高频考点列表
- GET /api/knowledge/recommend       — 获取智能推荐知识点列表

状态：已完成可复用。graph 接口返回树状结构（科目 → 章节 → 知识点），
      每个知识点包含 status 和 style，前端可直接渲染。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import KnowledgeMastery, KnowledgePoint, User
from services.recommendation_service import build_smart_recommendations
from utils.response import success


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

STATUS_STYLE = {
    "未学": {"color": "#9aa5b1", "class_name": "unlearned", "label": "未学"},
    "掌握": {"color": "#27a978", "class_name": "mastered", "label": "掌握"},
    "不熟": {"color": "#d9a441", "class_name": "unfamiliar", "label": "不熟"},
    "不会": {"color": "#e17843", "class_name": "unknown", "label": "不会"},
    "薄弱点": {"color": "#e95f52", "class_name": "weak", "label": "薄弱点"},
}

STATUS_ORDER = ["薄弱点", "不会", "不熟", "掌握", "未学"]


def _normalize_status(row: KnowledgeMastery | None) -> str:
    if row is None:
        return "未学"
    total = row.total_answer_count or 0
    wrong = row.wrong_count or 0
    correct = row.correct_count or 0
    weak_score = row.weak_score or 0
    if total == 0 and weak_score <= 0:
        return "未学"
    if wrong >= 3 or weak_score >= 10:
        return "薄弱点"
    if row.unknown_count or (total >= 2 and correct == 0):
        return "不会"
    if row.unfamiliar_count or wrong in (1, 2):
        return "不熟"
    if total >= 3 and correct / max(total, 1) >= 0.8 and wrong <= 1 and weak_score <= 2:
        return "掌握"
    return "不熟"


@router.get("/graph")
def graph(
    scope: str = Query("user", description="all=全量扁平章节列表不含掌握状态, user=含用户掌握状态, tree=返回树状结构"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).order_by(KnowledgePoint.subject, KnowledgePoint.id).all()
    mastery_map_data: dict[tuple[str, str], KnowledgeMastery] = {}
    if scope in ("user", "tree"):
        mastery_rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user.id).all()
        for m in mastery_rows:
            mastery_map_data[(m.subject, m.knowledge_point)] = m

    if scope == "tree":
        subjects: dict[str, dict] = {}
        for row in rows:
            if row.subject not in subjects:
                subjects[row.subject] = {"name": row.subject, "children": []}
            parent_name = row.parent_name or row.subject
            parent_node = None
            for child in subjects[row.subject]["children"]:
                if child["name"] == parent_name:
                    parent_node = child
                    break
            if parent_node is None:
                parent_node = {"name": parent_name, "children": []}
                subjects[row.subject]["children"].append(parent_node)
            node = {"name": row.section or row.name, "knowledge_point": row.name, "content": row.content, "keywords": row.keywords}
            if scope == "tree":
                mastery_row = mastery_map_data.get((row.subject, row.name))
                status = _normalize_status(mastery_row)
                node["status"] = status
                node["style"] = STATUS_STYLE.get(status, STATUS_STYLE["未学"])
            parent_node["children"].append(node)
        return success({"subjects": list(subjects.values()), "status_style": STATUS_STYLE})

    SUBJECTS = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
    grouped: dict[str, list[dict]] = {s: [] for s in SUBJECTS}
    seen: dict[tuple[str, str], bool] = {}
    for p in rows:
        key = (p.subject, p.name)
        if key in seen:
            continue
        seen[key] = True
        if p.subject not in grouped:
            grouped[p.subject] = []
        mastery_row = mastery_map_data.get(key)
        status = _normalize_status(mastery_row) if scope == "user" else "未学"
        grouped[p.subject].append({
            "id": f"{p.subject}-{p.name}",
            "subject": p.subject,
            "name": p.name,
            "parent_name": p.parent_name or p.subject,
            "level": 2,
            "is_high_frequency": p.is_high_frequency,
            "status": status,
            "weak_score": mastery_row.weak_score if mastery_row else 0,
            "total_answer_count": mastery_row.total_answer_count if mastery_row else 0,
            "style": STATUS_STYLE.get(status, STATUS_STYLE["未学"]),
        })
    for s in SUBJECTS:
        if s not in grouped:
            grouped[s] = []
    summary = {status: 0 for status in STATUS_STYLE}
    for items in grouped.values():
        for item in items:
            summary[item["status"]] += 1
    return success({"subjects": grouped, "summary": summary, "status_style": STATUS_STYLE})


@router.get("/high-frequency")
def high_frequency(db: Session = Depends(get_db)):
    rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_high_frequency == True).all()
    return success({"items": [{"subject": r.subject, "knowledge_point": r.name, "content": r.content} for r in rows]})


@router.get("/recommend")
def recommend(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"items": build_smart_recommendations(db, user.id)})
