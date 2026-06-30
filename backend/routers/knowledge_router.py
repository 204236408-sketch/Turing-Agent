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
from services.knowledge_graph_service import (
    build_knowledge_overview,
    build_subject_graph,
    find_chapter_detail,
    find_point_detail,
    status_style,
    point_name_of,
)
from services.mastery_service import synchronize_user_mastery
from services.recommendation_service import build_smart_recommendations
from utils.response import AppError
from utils.response import success


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# 与后端 _score_to_status 阈值一致，供前端兜底展示
STATUS_STYLE_FALLBACK = status_style("unlearned")


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(build_knowledge_overview(db, user.id))


@router.get("/subject/{subject_id}/graph")
def subject_graph(subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = build_subject_graph(db, user.id, subject_id)
    if not payload:
        raise AppError("SUBJECT_NOT_FOUND", "科目不存在", status_code=404)
    return success(payload)


@router.get("/chapter/{chapter_id}")
def chapter_detail(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = find_chapter_detail(db, user.id, chapter_id)
    if not payload:
        raise AppError("CHAPTER_NOT_FOUND", "章节不存在", status_code=404)
    return success(payload)


@router.get("/point/{knowledge_id}")
def point_detail(knowledge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = find_point_detail(db, user.id, knowledge_id)
    if not payload:
        raise AppError("KNOWLEDGE_POINT_NOT_FOUND", "知识点不存在", status_code=404)
    return success(payload)


@router.get("/point/{knowledge_id}/related")
def point_related(knowledge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    detail_payload = find_point_detail(db, user.id, knowledge_id)
    if not detail_payload:
        raise AppError("KNOWLEDGE_POINT_NOT_FOUND", "知识点不存在", status_code=404)
    point = detail_payload["point"]
    graph = build_subject_graph(db, user.id, point["subject_id"])
    items = []
    for chapter in graph.get("chapters", []):
        if chapter["name"] != point["chapter_name"]:
            continue
        for child in chapter.get("children", []):
            if child["id"] != knowledge_id:
                items.append({
                    "id": child["id"],
                    "name": child["name"],
                    "status": child["status"],
                    "status_label": child["status_label"],
                    "style": child["style"],
                })
    return success({"items": items[:8]})


@router.get("/chapter/{chapter_id}/points")
def chapter_points(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = find_chapter_detail(db, user.id, chapter_id)
    if not payload:
        raise AppError("CHAPTER_NOT_FOUND", "章节不存在", status_code=404)
    return success({"items": payload["chapter"].get("children", [])})


@router.get("/chapter/{chapter_id}/stats")
def chapter_stats(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = find_chapter_detail(db, user.id, chapter_id)
    if not payload:
        raise AppError("CHAPTER_NOT_FOUND", "章节不存在", status_code=404)
    chapter = payload["chapter"]
    children = chapter.get("children", [])
    learned = [item for item in children if item.get("status") != "unlearned"]
    last = learned[0] if learned else (children[0] if children else None)
    return success(
        {
            "mastery_percent": chapter["mastery_percent"],
            "status": chapter["status"],
            "status_distribution": chapter["status_distribution"],
            "status_distribution_percent": chapter["status_distribution_percent"],
            "last_study": {
                "knowledge_point_id": last["id"] if last else None,
                "knowledge_point_name": last["name"] if last else "",
                "study_time": "",
            },
        }
    )


@router.get("/chapter/{chapter_id}/related")
def chapter_related(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload = find_chapter_detail(db, user.id, chapter_id)
    if not payload:
        raise AppError("CHAPTER_NOT_FOUND", "章节不存在", status_code=404)
    graph = build_subject_graph(db, user.id, payload["subject"]["id"])
    items = [
        {
            "id": chapter["id"],
            "name": chapter["name"],
            "mastery_percent": chapter["mastery_percent"],
            "status": chapter["status"],
            "style": chapter["style"],
        }
        for chapter in graph.get("chapters", [])
        if chapter["id"] != chapter_id
    ]
    return success({"items": items[:5]})


@router.get("/graph")
def graph(
    scope: str = Query("user", description="all=全量扁平章节列表不含掌握状态, user=含用户掌握状态, tree=返回树状结构"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """知识图谱：与 build_knowledge_overview 同源，避免再写一遍判定逻辑。"""
    rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).order_by(KnowledgePoint.subject, KnowledgePoint.id).all()
    if scope in ("user", "tree"):
        # KP key 统一用 (subject, section)（与 knowledge_graph_service 一致）
        synchronize_user_mastery(db, user.id, [(r.subject, point_name_of(r)) for r in rows])
        db.flush()

    if scope == "tree":
        # 树状结构：复用 overview，转换为嵌套树
        overview = build_knowledge_overview(db, user.id)
        return success(_convert_to_tree(overview))

    # 扁平章节列表 / 总览
    overview = build_knowledge_overview(db, user.id)
    return success({
        "subjects": _convert_to_grouped(overview),
        "summary": _compute_summary(overview),
        "status_style": overview["status_style"],
    })


def _convert_to_grouped(overview: dict) -> dict[str, list[dict]]:
    """将 build_knowledge_overview 的 list 形态转成首页期望的 dict[科目] → list[chapter]"""
    grouped: dict[str, list[dict]] = {}
    for subject in overview.get("subjects", []):
        sname = subject["subject_name"]
        grouped.setdefault(sname, [])
        for chapter in subject.get("chapters", []):
            grouped[sname].append({
                "id": f"{sname}-{chapter['chapter_name']}",
                "subject": sname,
                "name": chapter["chapter_name"],
                "content": "",
                "parent_name": sname,
                "level": 2,
                "is_high_frequency": False,
                "status": chapter["status"],
                "mastery_percent": chapter["mastery_percent"],
                "knowledge_count": chapter["knowledge_count"],
                "learned_count": chapter.get("learned_count", 0),
                "style": chapter["style"],
            })
    return grouped


def _convert_to_tree(overview: dict) -> dict:
    """转成 { subjects: [{ name, children: [{ name, children: [{ name, status, style }] }] }] }"""
    subjects: list[dict] = []
    for subject in overview.get("subjects", []):
        chapter_nodes = []
        for chapter in subject.get("chapters", []):
            chapter_node = {
                "name": chapter["chapter_name"],
                "status": chapter["status"],
                "mastery_percent": chapter["mastery_percent"],
                "style": chapter["style"],
                "children": [
                    {
                        "name": child["name"],
                        "knowledge_point": child["name"],
                        "status": child["status"],
                        "style": child["style"],
                        "mastery_score": child.get("mastery_score", 0),
                    }
                    for child in chapter.get("children", [])
                ],
            }
            chapter_nodes.append(chapter_node)
        subjects.append({
            "name": subject["subject_name"],
            "mastery_percent": subject["mastery_percent"],
            "style": subject["style"],
            "children": chapter_nodes,
        })
    return {"subjects": subjects, "status_style": overview["status_style"]}


def _compute_summary(overview: dict) -> dict[str, int]:
    summary = {"mastered": 0, "unfamiliar": 0, "unknown": 0, "weak": 0, "unlearned": 0}
    for subject in overview.get("subjects", []):
        for chapter in subject.get("chapters", []):
            summary[chapter["status"]] = summary.get(chapter["status"], 0) + 1
    return summary


@router.get("/high-frequency")
def high_frequency(db: Session = Depends(get_db)):
    rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_high_frequency == True).all()
    return success({"items": [{"subject": r.subject, "knowledge_point": r.name, "content": r.content} for r in rows]})


@router.get("/recommend")
def recommend(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"items": build_smart_recommendations(db, user.id)})
