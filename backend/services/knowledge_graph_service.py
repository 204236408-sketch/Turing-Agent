from __future__ import annotations

from collections import Counter, OrderedDict
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from models import KnowledgeMastery, KnowledgePoint, Subject
from services.mastery_service import synchronize_user_mastery


STATUS_META = {
    "mastered": {"label": "掌握", "score": 100, "color": "#2fbf7a", "class_name": "mastered"},
    "unfamiliar": {"label": "不熟", "score": 60, "color": "#f5bd22", "class_name": "unfamiliar"},
    "unknown": {"label": "不会", "score": 30, "color": "#ff9f43", "class_name": "unknown"},
    "weak": {"label": "薄弱点", "score": 10, "color": "#ff6262", "class_name": "weak"},
    "unlearned": {"label": "未学", "score": 0, "color": "#a8b0bf", "class_name": "unlearned"},
}

STATUS_ORDER = ["weak", "unknown", "unfamiliar", "mastered", "unlearned"]

STATUS_ALIASES = {
    "掌握": "mastered",
    "已掌握": "mastered",
    "mastered": "mastered",
    "不熟": "unfamiliar",
    "正在学习": "unfamiliar",
    "unfamiliar": "unfamiliar",
    "不会": "unknown",
    "unknown": "unknown",
    "薄弱点": "weak",
    "薄弱": "weak",
    "weak": "weak",
    "未学": "unlearned",
    "unlearned": "unlearned",
    "": "unlearned",
    None: "unlearned",
}


@dataclass
class MasteryChoice:
    status: str
    row: KnowledgeMastery | None
    mastery_score: int
    source_scores: dict[str, int]


def normalize_status(status: str | None) -> str:
    return STATUS_ALIASES.get(status, "unlearned")


def status_score(status: str | None) -> int:
    return STATUS_META[normalize_status(status)]["score"]


def status_style(status: str | None) -> dict:
    key = normalize_status(status)
    return {"key": key, **STATUS_META[key]}


MASTERY_SCORE_WEIGHTS = {
    "answer_performance": 0.50,
    "user_feedback": 0.20,
    "mistake_penalty": 0.20,
    "learning_behavior": 0.10,
}


def _clamp_score(value: float) -> int:
    return round(max(0, min(100, value)))


def _row_has_behavior(row: KnowledgeMastery | None) -> bool:
    if row is None:
        return False
    return any(
        [
            row.total_answer_count,
            row.correct_count,
            row.wrong_count,
            row.unfamiliar_count,
            row.unknown_count,
            row.mastered_count,
            row.ocr_mistake_count,
            row.qa_count,
            row.forum_count,
            row.user_mark_status,
            row.weak_score,
            row.continuous_wrong_count,
            normalize_status(row.final_status) != "unlearned",
        ]
    )


def _answer_performance_score(row: KnowledgeMastery | None) -> int:
    if row is None or not row.total_answer_count:
        return 0
    score = (row.correct_count or 0) * 100 / max(row.total_answer_count or 0, 1)
    if (row.total_answer_count or 0) < 3:
        score = min(score, 70)
    if (row.continuous_wrong_count or 0) >= 2:
        score = min(score, 40)
    return _clamp_score(score)


def _user_feedback_score(row: KnowledgeMastery | None, answer_score: int) -> int:
    if row is None:
        return 0
    explicit_status = normalize_status(row.user_mark_status)
    if explicit_status != "unlearned":
        return STATUS_META[explicit_status]["score"]
    if row.total_answer_count:
        return answer_score
    inferred_status = normalize_status(row.final_status)
    return STATUS_META[inferred_status]["score"] if inferred_status != "unlearned" else 0


def _mistake_penalty_score(row: KnowledgeMastery | None) -> int:
    if not _row_has_behavior(row):
        return 0
    wrong_count = row.wrong_count or 0
    continuous_wrong = row.continuous_wrong_count or 0
    ocr_count = row.ocr_mistake_count or 0
    weak_penalty = min(40, (row.weak_score or 0) * 3)
    return _clamp_score(100 - wrong_count * 12 - continuous_wrong * 15 - ocr_count * 8 - weak_penalty)


def _learning_behavior_score(row: KnowledgeMastery | None) -> int:
    if row is None:
        return 0
    return _clamp_score(
        (row.total_answer_count or 0) * 20
        + (row.qa_count or 0) * 10
        + (row.forum_count or 0) * 5
    )


def _status_from_score(score: int) -> str:
    if score >= 80:
        return "mastered"
    if score >= 50:
        return "unfamiliar"
    if score >= 20:
        return "unknown"
    if score > 0:
        return "weak"
    return "unlearned"


def compute_mastery_score(row: KnowledgeMastery | None) -> tuple[int, str, dict[str, int]]:
    if not _row_has_behavior(row):
        empty_scores = {key: 0 for key in MASTERY_SCORE_WEIGHTS}
        return 0, "unlearned", empty_scores

    answer_score = _answer_performance_score(row)
    source_scores = {
        "answer_performance": answer_score,
        "user_feedback": _user_feedback_score(row, answer_score),
        "mistake_penalty": _mistake_penalty_score(row),
        "learning_behavior": _learning_behavior_score(row),
    }
    score = sum(source_scores[key] * MASTERY_SCORE_WEIGHTS[key] for key in MASTERY_SCORE_WEIGHTS)

    explicit_status = normalize_status(row.user_mark_status if row else None)
    final_status = normalize_status(row.final_status if row else None)
    if explicit_status == "weak" or final_status == "weak" or (row and (row.weak_score or 0) >= 10):
        score = min(score, 19)
    elif row and ((row.continuous_wrong_count or 0) >= 3 or (row.wrong_count or 0) >= 3):
        score = min(score, 49)

    mastery_score = _clamp_score(score)
    return mastery_score, _status_from_score(mastery_score), source_scores


def _best_row(existing: KnowledgeMastery | None, incoming: KnowledgeMastery) -> KnowledgeMastery:
    if existing is None:
        return incoming
    existing_status = normalize_status(existing.final_status)
    incoming_status = normalize_status(incoming.final_status)
    if STATUS_ORDER.index(incoming_status) < STATUS_ORDER.index(existing_status):
        return incoming
    if (incoming.weak_score or 0) > (existing.weak_score or 0):
        return incoming
    if (incoming.total_answer_count or 0) > (existing.total_answer_count or 0):
        return incoming
    return existing


def _mastery_map(rows: Iterable[KnowledgeMastery]) -> dict[tuple[str, str], KnowledgeMastery]:
    result: dict[tuple[str, str], KnowledgeMastery] = {}
    for row in rows:
        key = ((row.subject or "").strip(), (row.knowledge_point or "").strip())
        if not key[0] or not key[1]:
            continue
        result[key] = _best_row(result.get(key), row)
    return result


def _choose_mastery(
    by_mastery: dict[tuple[str, str], KnowledgeMastery],
    subject_name: str,
    point_name: str,
    chapter_name: str,
) -> MasteryChoice:
    point_row = by_mastery.get((subject_name, point_name))
    chapter_row = by_mastery.get((subject_name, chapter_name))
    row = _best_row(point_row, chapter_row) if point_row and chapter_row else (point_row or chapter_row)
    mastery_score, status, source_scores = compute_mastery_score(row)
    return MasteryChoice(status, row, mastery_score, source_scores)


def _distribution(items: Iterable[str]) -> dict[str, int]:
    counter = Counter(normalize_status(item) for item in items)
    return {key: counter.get(key, 0) for key in STATUS_META}


def _distribution_percent(distribution: dict[str, int]) -> dict[str, int]:
    total = sum(distribution.values())
    if total <= 0:
        return {key: 0 for key in STATUS_META}
    return {key: round(value * 100 / total) for key, value in distribution.items()}


def _chapter_status(mastery_percent: int) -> str:
    if mastery_percent >= 80:
        return "mastered"
    if mastery_percent >= 50:
        return "unfamiliar"
    if mastery_percent >= 20:
        return "unknown"
    if mastery_percent > 0:
        return "weak"
    return "unlearned"


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


def _sync_mastery_for_points(db: Session, user_id: int, points: list[KnowledgePoint]) -> dict[tuple[str, str], KnowledgeMastery]:
    pairs: set[tuple[str, str]] = set()
    for point in points:
        subject = point.subject
        if point.name:
            pairs.add((subject, point.name))
        if point.section:
            pairs.add((subject, point.section))
    if pairs:
        synchronize_user_mastery(db, user_id, sorted(pairs))
        db.flush()
    rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user_id).all()
    return _mastery_map(rows)


def _chapter_payload(subject: Subject, chapter_name: str, points: list[KnowledgePoint], by_mastery: dict[tuple[str, str], KnowledgeMastery]) -> dict:
    children = []
    seen_children: set[str] = set()
    child_statuses: list[str] = []
    child_scores: list[int] = []
    for point in points:
        point_name = (point.section or point.name or "").strip()
        if not point_name or point_name in seen_children:
            continue
        seen_children.add(point_name)
        mastery = _choose_mastery(by_mastery, subject.name, point_name, chapter_name)
        child_statuses.append(mastery.status)
        child_scores.append(mastery.mastery_score)
        # 取最近学习时间：优先 last_answer_time，其次 update_time
        raw_time = (mastery.row.last_answer_time if mastery.row else None) or (mastery.row.update_time if mastery.row else None)
        updated_at = raw_time.isoformat() if raw_time else ""
        children.append(
            {
                "id": point.id,
                "name": point_name,
                "mastery_score": mastery.mastery_score,
                "status": mastery.status,
                "status_label": STATUS_META[mastery.status]["label"],
                "style": status_style(mastery.status),
                "source_scores": mastery.source_scores,
                "content": point.content or "",
                "keywords": point.keywords or "",
                "common_mistakes": point.common_mistakes or "",
                "updated_at": updated_at,
            }
        )

    mastery_percent = round(sum(child_scores) / len(child_scores)) if child_scores else 0
    distribution = _distribution(child_statuses)
    status = _chapter_status(mastery_percent)

    # 聚合章节级 content / keywords：优先取 chapter 自身 KnowledgePoint 的值，否则从 children 拼接
    chapter_point = points[0] if points else None
    chapter_content = chapter_point.content if chapter_point and chapter_point.content else ""
    chapter_keywords = chapter_point.keywords if chapter_point and chapter_point.keywords else ""
    if not chapter_content and children:
        chapter_content = children[0].get("content", "")
    if not chapter_keywords and children:
        chapter_keywords = "、".join(c.get("keywords", "").strip() for c in children if c.get("keywords", "").strip())

    # 最近学习的知识点
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
        "status": status,
        "status_label": STATUS_META[status]["label"],
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


def build_subject_graph(db: Session, user_id: int, subject_id: int) -> dict:
    subjects = _subject_query(db, subject_id)
    if not subjects:
        return {}
    subject = subjects[0]
    points = _subject_points(db, subject)
    by_mastery = _sync_mastery_for_points(db, user_id, points)

    chapters_grouped: OrderedDict[str, list[KnowledgePoint]] = OrderedDict()
    for point in points:
        chapter_name = (point.name or point.parent_name or point.section or "").strip()
        if not chapter_name:
            continue
        chapters_grouped.setdefault(chapter_name, []).append(point)

    chapters = [
        _chapter_payload(subject, chapter_name, chapter_points, by_mastery)
        for chapter_name, chapter_points in chapters_grouped.items()
    ]

    total_knowledge = sum(chapter["knowledge_count"] for chapter in chapters)
    weighted_score = sum(chapter["mastery_percent"] * chapter["knowledge_count"] for chapter in chapters)
    mastery_percent = round(weighted_score / total_knowledge) if total_knowledge else 0
    status_distribution = {key: 0 for key in STATUS_META}
    for chapter in chapters:
        for key, value in chapter["status_distribution"].items():
            status_distribution[key] += value
    learned_count = total_knowledge - status_distribution["unlearned"]
    weak_chapters = sorted(chapters, key=lambda item: (item["mastery_percent"], -item["knowledge_count"]))[:3]
    recommended_chapters = [item for item in chapters if item["status"] in {"weak", "unknown", "unfamiliar"}][:4]

    return {
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "mastery_percent": mastery_percent,
            "chapter_count": len(chapters),
            "knowledge_count": total_knowledge,
            "learned_count": learned_count,
            "status": _chapter_status(mastery_percent),
            "style": status_style(_chapter_status(mastery_percent)),
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
        "score_weights": MASTERY_SCORE_WEIGHTS,
    }


def build_knowledge_overview(db: Session, user_id: int) -> dict:
    subjects = []
    for subject in _subject_query(db):
        graph = build_subject_graph(db, user_id, subject.id)
        if not graph:
            continue
        subject_payload = graph["subject"]
        subjects.append(
            {
                "subject_id": subject_payload["id"],
                "subject_name": subject_payload["name"],
                "mastery_percent": subject_payload["mastery_percent"],
                "chapter_count": subject_payload["chapter_count"],
                "knowledge_count": subject_payload["knowledge_count"],
                "learned_count": subject_payload["learned_count"],
                "status": subject_payload["status"],
                "style": subject_payload["style"],
                "status_distribution": graph["status_distribution"],
                "status_distribution_percent": graph["status_distribution_percent"],
                "chapters": [
                    {
                        "chapter_id": chapter["id"],
                        "chapter_name": chapter["name"],
                        "mastery_percent": chapter["mastery_percent"],
                        "knowledge_count": chapter["knowledge_count"],
                        "status": chapter["status"],
                        "status_label": chapter["status_label"],
                        "style": chapter["style"],
                        "status_distribution": chapter["status_distribution"],
                    }
                    for chapter in graph["chapters"]
                ],
            }
        )
    return {
        "subjects": subjects,
        "status_style": {key: status_style(key) for key in STATUS_META},
        "score_weights": MASTERY_SCORE_WEIGHTS,
    }


def find_chapter_detail(db: Session, user_id: int, chapter_id: int) -> dict:
    point = db.query(KnowledgePoint).filter(KnowledgePoint.id == chapter_id, KnowledgePoint.is_deleted == False).first()
    if not point:
        return {}
    subject = db.query(Subject).filter(Subject.id == point.subject_id).first()
    if not subject:
        return {}
    graph = build_subject_graph(db, user_id, subject.id)
    chapter_name = point.name or point.parent_name or point.section
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
    by_mastery = _sync_mastery_for_points(db, user_id, [point])
    point_name = point.section or point.name
    chapter_name = point.name or point.parent_name or subject.name
    mastery = _choose_mastery(by_mastery, subject.name, point_name, chapter_name)
    return {
        "point": {
            "id": point.id,
            "name": point_name,
            "subject_id": subject.id,
            "subject_name": subject.name,
            "chapter_name": chapter_name,
            "mastery_score": mastery.mastery_score,
            "status": mastery.status,
            "status_label": STATUS_META[mastery.status]["label"],
            "style": status_style(mastery.status),
            "source_scores": mastery.source_scores,
            "content": point.content or "",
            "keywords": point.keywords or "",
            "common_mistakes": point.common_mistakes or "",
            "total_answer_count": mastery.row.total_answer_count if mastery.row else 0,
            "wrong_count": mastery.row.wrong_count if mastery.row else 0,
            "weak_score": mastery.row.weak_score if mastery.row else 0,
        }
    }
