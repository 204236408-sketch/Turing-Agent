"""知识图谱 / 掌握度聚合：唯一读取 mastery_service 写入的 mastery_score，不再自行重算。

设计原则（与 mastery_service 保持一致）：
- 三级 KP 的状态 = DB 中 KnowledgeMastery.final_status（已由 mastery_service 计算并持久化）
- 二级章节的 mastery_percent = 该章节下所有"有行为数据"的 KP 的 mastery_score 平均
  - 未学的 KP 不计入分母，避免"未学 KP 拉低分"
  - 若所有 KP 都未学，章节 mastery_percent = 0
- 二级章节的 status = 由 mastery_percent 经 mastery_service._score_to_status 派生
- 章节定义 = KnowledgePoint.name（缺失时回退 parent_name / section）
- 知识点名 = KnowledgePoint.section（缺失时回退 name）
- 一级科目的 mastery_percent = 各章节 mastery_percent × 章节 KP 数 加权平均
- 一级科目的 learned_count = 所有 KP 中"有行为数据"的数量（mastery_score > 0 或 final_status != 未学）

注意：
- 本模块不再调 compute_mastery_score，每条数据的状态分都来自 DB
- 上游 router（home_router / knowledge_router）必须先调用 synchronize_user_mastery 刷新分值
"""
from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Iterable

from sqlalchemy.orm import Session

from models import KnowledgeMastery, KnowledgePoint, Subject
from services.mastery_service import (
    STATUS_META,
    STATUS_ORDER,
    _score_to_status,
    normalize_status,
    status_label,
)


# 兼容旧导入：re-export 状态元数据
STATUS_ALIASES = {
    "掌握": "mastered", "已掌握": "mastered", "mastered": "mastered",
    "不熟": "unfamiliar", "正在学习": "unfamiliar", "unfamiliar": "unfamiliar",
    "不会": "unknown", "unknown": "unknown",
    "薄弱点": "weak", "薄弱": "weak", "weak": "weak",
    "未学": "unlearned", "unlearned": "unlearned",
    "": "unlearned", None: "unlearned",
}


def status_style(status: str | None) -> dict:
    """前端展示用的状态样式：key / label / score / color / class_name"""
    key = normalize_status(status)
    base = STATUS_META[key]
    class_name_map = {
        "mastered": "mastered", "unfamiliar": "unfamiliar",
        "unknown": "unknown", "weak": "weak", "unlearned": "unlearned",
    }
    return {
        "key": key,
        "label": base["label"],
        "score": base["score"],
        "color": base["color"],
        "class_name": class_name_map[key],
    }


# ── 章节/知识点名归一化 ────────────────────────────────────────────────
def chapter_name_of(point: KnowledgePoint) -> str:
    """统一章节名：name → parent_name → section，去空白"""
    return (point.name or point.parent_name or point.section or "").strip()


def point_name_of(point: KnowledgePoint) -> str:
    """统一知识点名：section → name（章节名是父级，section 才是具体知识点）"""
    return (point.section or point.name or "").strip()


# ── 加载 mastery 表，生成 (subject, point_name) → row 映射 ────────────────
def _mastery_map(rows: list[KnowledgeMastery]) -> dict[tuple[str, str], KnowledgeMastery]:
    """DB 行 → (subject, knowledge_point) 字典

    若同一 (subject, kp) 出现多行（理论上 unique 约束会阻止，但容错处理），
    选择 mastery_score 最高的那条（避免旧的"薄弱点"行压制新的"已掌握"行）。
    """
    result: dict[tuple[str, str], KnowledgeMastery] = {}
    for row in rows:
        key = ((row.subject or "").strip(), (row.knowledge_point or "").strip())
        if not key[0] or not key[1]:
            continue
        existing = result.get(key)
        if not existing:
            result[key] = row
            continue
        if (row.mastery_score or 0) > (existing.mastery_score or 0):
            result[key] = row
    return result


def _has_behavior(row: KnowledgeMastery | None) -> bool:
    """该 KP 是否有过学习行为（用于判定是否算入分母/已学习）"""
    if row is None:
        return False
    return any([
        row.total_answer_count,
        row.correct_count,
        row.wrong_count,
        row.qa_count,
        row.forum_count,
        row.user_mark_status,
        row.last_answer_time,
    ])


def _distribution(items: Iterable[str]) -> dict[str, int]:
    counter = Counter(normalize_status(item) for item in items)
    return {key: counter.get(key, 0) for key in STATUS_META}


def _distribution_percent(distribution: dict[str, int]) -> dict[str, int]:
    total = sum(distribution.values())
    if total <= 0:
        return {key: 0 for key in STATUS_META}
    return {key: round(value * 100 / total) for key, value in distribution.items()}


# ── 章节载荷：聚合三级 KP 得到章节的 mastery_percent / status ─────────────
def _chapter_payload(
    subject: Subject,
    chapter_name: str,
    points: list[KnowledgePoint],
    by_mastery: dict[tuple[str, str], KnowledgeMastery],
) -> dict:
    children = []
    seen_children: set[str] = set()
    child_scores: list[int] = []  # 仅收集"有行为数据"的子节点的 mastery_score
    child_statuses: list[str] = []  # 用于分布统计：包含"未学"，按全部子节点计

    for point in points:
        kp_name = point_name_of(point)
        if not kp_name or kp_name in seen_children:
            continue
        seen_children.add(kp_name)

        row = by_mastery.get((subject.name, kp_name))
        # 状态优先用 DB 里的 final_status；mastery_score 由 mastery_service 写入
        if row is not None:
            status_key = normalize_status(row.final_status)
            score = int(row.mastery_score or 0)
            has_data = _has_behavior(row) or score > 0
        else:
            # 无 mastery 行 → 视为未学，不进 child_scores 分母
            status_key = "unlearned"
            score = 0
            has_data = False

        child_statuses.append(status_key)
        if has_data:
            child_scores.append(score)

        # 最近学习时间
        raw_time = None
        if row:
            raw_time = row.last_answer_time or row.update_time
        updated_at = raw_time.isoformat() if raw_time else ""

        children.append({
            "id": point.id,
            "name": kp_name,
            "chapter_name": chapter_name,
            "status": status_key,
            "status_label": status_label(status_key),
            "mastery_score": score if has_data else 0,
            "style": status_style(status_key),
            "content": point.content or "",
            "keywords": point.keywords or "",
            "common_mistakes": point.common_mistakes or "",
            "has_behavior": has_data,
            "updated_at": updated_at,
        })

    # 章节百分比：有行为数据的子节点分数平均
    mastery_percent = round(sum(child_scores) / len(child_scores)) if child_scores else 0
    distribution = _distribution(child_statuses)
    status = _score_to_status(mastery_percent)
    learned_count = sum(1 for c in child_statuses if c != "unlearned")

    # 章节级 content / keywords
    chapter_point = points[0] if points else None
    chapter_content = chapter_point.content if chapter_point and chapter_point.content else ""
    chapter_keywords = chapter_point.keywords if chapter_point and chapter_point.keywords else ""
    if not chapter_content and children:
        chapter_content = children[0].get("content", "")
    if not chapter_keywords and children:
        chapter_keywords = "、".join(c.get("keywords", "").strip() for c in children if c.get("keywords", "").strip())

    # 最近学习
    learned_children = sorted(
        [c for c in children if c.get("updated_at")],
        key=lambda c: c["updated_at"],
        reverse=True,
    )
    last_study = learned_children[0] if learned_children else None

    return {
        "id": points[0].id if points else 0,
        "name": chapter_name,
        "subject_id": subject.id,
        "subject_name": subject.name,
        "mastery_percent": mastery_percent,
        "knowledge_count": len(children),
        "learned_count": learned_count,
        "status": status,
        "status_label": status_label(status),
        "style": status_style(status),
        "status_distribution": distribution,
        "status_distribution_percent": _distribution_percent(distribution),
        "children": children,
        "content": chapter_content,
        "keywords": chapter_keywords,
        "last_study": {
            "point_id": last_study["id"] if last_study else None,
            "point_name": last_study["name"] if last_study else "",
            "status_label": last_study["status_label"] if last_study else "",
            "study_time": last_study["updated_at"] if last_study else "",
        } if last_study else None,
    }


def _subject_query(db: Session, subject_id: int | None = None) -> list[Subject]:
    query = db.query(Subject).filter(Subject.is_deleted == False)
    if subject_id is not None:
        query = query.filter(Subject.id == subject_id)
    return query.order_by(Subject.sort_order, Subject.id).all()


def _subject_points(db: Session, subject: Subject) -> list[KnowledgePoint]:
    return (
        db.query(KnowledgePoint)
        .filter(
            KnowledgePoint.is_deleted == False,
            KnowledgePoint.subject_id == subject.id,
        )
        .order_by(KnowledgePoint.id)
        .all()
    )


def _load_mastery_for_points(
    db: Session, user_id: int, points: list[KnowledgePoint]
) -> dict[tuple[str, str], KnowledgeMastery]:
    """只取本批 KP 对应的 mastery 行，避免扫全表"""
    pairs: set[tuple[str, str]] = set()
    for p in points:
        kp_name = point_name_of(p)
        if kp_name:
            pairs.add((p.subject, kp_name))
    if not pairs:
        return {}
    cond = []
    for sub, kp in pairs:
        cond.append(
            (KnowledgeMastery.user_id == user_id)
            & (KnowledgeMastery.subject == sub)
            & (KnowledgeMastery.knowledge_point == kp)
        )
    from sqlalchemy import or_
    rows = db.query(KnowledgeMastery).filter(or_(*cond)).all()
    return _mastery_map(rows)


# ── 主接口 ──────────────────────────────────────────────────────────────
def build_subject_graph(db: Session, user_id: int, subject_id: int) -> dict:
    subject_list = _subject_query(db, subject_id)
    if not subject_list:
        return {}
    subject = subject_list[0]
    points = _subject_points(db, subject)
    by_mastery = _load_mastery_for_points(db, user_id, points)

    # 按 chapter_name(=point.name) 分组
    chapters_grouped: OrderedDict[str, list[KnowledgePoint]] = OrderedDict()
    for point in points:
        cn = chapter_name_of(point)
        if not cn:
            continue
        chapters_grouped.setdefault(cn, []).append(point)

    chapters = [
        _chapter_payload(subject, chapter_name, chapter_points, by_mastery)
        for chapter_name, chapter_points in chapters_grouped.items()
    ]

    total_knowledge = sum(c["knowledge_count"] for c in chapters)
    total_learned = sum(c["learned_count"] for c in chapters)
    # 科目级百分比：按 KP 数量加权
    weighted_score = sum(c["mastery_percent"] * c["knowledge_count"] for c in chapters)
    mastery_percent = round(weighted_score / total_knowledge) if total_knowledge else 0
    status_distribution = {key: 0 for key in STATUS_META}
    for chapter in chapters:
        for key, value in chapter["status_distribution"].items():
            status_distribution[key] += value

    weak_chapters = sorted(chapters, key=lambda item: (item["mastery_percent"], -item["knowledge_count"]))[:3]
    recommended_chapters = [item for item in chapters if item["status"] in {"weak", "unknown", "unfamiliar"}][:4]

    return {
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "mastery_percent": mastery_percent,
            "chapter_count": len(chapters),
            "knowledge_count": total_knowledge,
            "learned_count": total_learned,
            "status": _score_to_status(mastery_percent),
            "style": status_style(_score_to_status(mastery_percent)),
        },
        "status_distribution": status_distribution,
        "status_distribution_percent": _distribution_percent(status_distribution),
        "weak_chapters": [
            {"id": item["id"], "name": item["name"], "mastery_percent": item["mastery_percent"]}
            for item in weak_chapters
        ],
        "recommended_chapters": [
            {"id": item["id"], "name": item["name"], "mastery_percent": item["mastery_percent"], "status": item["status"]}
            for item in recommended_chapters
        ],
        "chapters": chapters,
        "status_style": {key: status_style(key) for key in STATUS_META},
        "score_weights": {"answer_performance": 0.50, "user_feedback": 0.20, "mistake_penalty": 0.20, "learning_behavior": 0.10},
    }


def build_knowledge_overview(db: Session, user_id: int) -> dict:
    subjects = []
    for subject in _subject_query(db):
        graph = build_subject_graph(db, user_id, subject.id)
        if not graph:
            continue
        sp = graph["subject"]
        subjects.append({
            "subject_id": sp["id"],
            "subject_name": sp["name"],
            "mastery_percent": sp["mastery_percent"],
            "chapter_count": sp["chapter_count"],
            "knowledge_count": sp["knowledge_count"],
            "learned_count": sp["learned_count"],
            "status": sp["status"],
            "style": sp["style"],
            "status_distribution": graph["status_distribution"],
            "status_distribution_percent": graph["status_distribution_percent"],
            "chapters": [
                {
                    "chapter_id": c["id"],
                    "chapter_name": c["name"],
                    "mastery_percent": c["mastery_percent"],
                    "knowledge_count": c["knowledge_count"],
                    "learned_count": c["learned_count"],
                    "status": c["status"],
                    "status_label": c["status_label"],
                    "style": c["style"],
                    "status_distribution": c["status_distribution"],
                }
                for c in graph["chapters"]
            ],
        })
    return {
        "subjects": subjects,
        "status_style": {key: status_style(key) for key in STATUS_META},
        "score_weights": {"answer_performance": 0.50, "user_feedback": 0.20, "mistake_penalty": 0.20, "learning_behavior": 0.10},
    }


def find_chapter_detail(db: Session, user_id: int, chapter_id: int) -> dict:
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == chapter_id, KnowledgePoint.is_deleted == False).first()
    if not point:
        return {}
    subject = db.query(Subject).filter(Subject.id == point.subject_id).first()
    if not subject:
        return {}
    graph = build_subject_graph(db, user_id, subject.id)
    chapter_name = chapter_name_of(point)
    for chapter in graph.get("chapters", []):
        if chapter["name"] == chapter_name:
            return {"subject": graph["subject"], "chapter": chapter}
    return {}


def find_point_detail(db: Session, user_id: int, knowledge_id: int) -> dict:
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_id, KnowledgePoint.is_deleted == False).first()
    if not point:
        return {}
    subject = db.query(Subject).filter(Subject.id == point.subject_id).first()
    if not subject:
        return {}
    by_mastery = _load_mastery_for_points(db, user_id, [point])
    kp_name = point_name_of(point)
    cn = chapter_name_of(point)
    row = by_mastery.get((subject.name, kp_name))
    if row is not None:
        status_key = normalize_status(row.final_status)
        score = int(row.mastery_score or 0)
        has_data = _has_behavior(row) or score > 0
    else:
        status_key = "unlearned"
        score = 0
        has_data = False
    return {
        "point": {
            "id": point.id,
            "name": kp_name,
            "subject_id": subject.id,
            "subject_name": subject.name,
            "chapter_name": cn,
            "status": status_key,
            "status_label": status_label(status_key),
            "mastery_score": score if has_data else 0,
            "style": status_style(status_key),
            "content": point.content or "",
            "keywords": point.keywords or "",
            "common_mistakes": point.common_mistakes or "",
            "total_answer_count": row.total_answer_count if row else 0,
            "wrong_count": row.wrong_count if row else 0,
            "weak_score": row.weak_score if row else 0,
        }
    }
