from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import KnowledgeMastery, KnowledgePoint, Mistake, QuestionGenerationSession, UserMemory


STATUS_PRIORITY = {"薄弱点": 0, "不会": 1, "不熟": 2, "掌握": 3, "未学": 4}
SMART_MODES = {"薄弱点强化", "最近错题复练", "高频提问专项", "已改善知识点复测", "四科随机综合"}

_ALL_SUBJECTS = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
_ALL_QUESTION_TYPES = ["选择题", "填空题", "简答题", "综合题"]


def _to_difficulty(mastery: KnowledgeMastery | None, base: str = "中等") -> str:
    if mastery is None:
        return base
    ws = mastery.weak_score or 0
    if ws > 6:
        return "简单"
    if ws >= 3:
        return "中等"
    if mastery.total_answer_count and mastery.total_answer_count >= 5:
        return "较难"
    return base


def _to_question_type(mastery: KnowledgeMastery | None, mode: str) -> str:
    if mode == "已改善知识点复测":
        return "选择题"
    if mastery is None:
        return "选择题"
    cw = mastery.continuous_wrong_count or 0
    qa = mastery.qa_count or 0
    ws = mastery.weak_score or 0
    if cw >= 2:
        return "填空题"
    if qa >= 3:
        return "简答题"
    if ws >= 8:
        return "综合题"
    return "选择题"


def _to_count(mastery: KnowledgeMastery | None, mode: str) -> int:
    if mode == "已改善知识点复测":
        return 2
    if mode == "四科随机综合":
        return 3
    if mastery is None:
        return 3
    ws = mastery.weak_score or 0
    if ws > 6:
        return 5
    if ws >= 3:
        return 3
    return 2


def _point_payload(
    mode: str,
    subject: str,
    knowledge_point: str,
    reason: str,
    difficulty: str,
    question_type: str,
    count: int,
    *,
    available: bool = True,
    initial: bool = False,
) -> dict:
    return {
        "mode": mode,
        "subject": subject,
        "knowledge_point": knowledge_point,
        "reason": reason,
        "difficulty": difficulty,
        "question_type": question_type,
        "count": count,
        "available": available,
        "initial": initial,
    }


def _baseline_points(db: Session) -> list[KnowledgePoint]:
    points = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.is_high_frequency == True)
        .order_by(KnowledgePoint.subject.asc(), KnowledgePoint.id.asc())
        .all()
    )
    if points:
        return points
    return db.query(KnowledgePoint).order_by(KnowledgePoint.subject.asc(), KnowledgePoint.id.asc()).all()


def _urgency_score(mastery: KnowledgeMastery) -> float:
    ws = mastery.weak_score or 0
    cw = mastery.continuous_wrong_count or 0
    qa = mastery.qa_count or 0
    recency = 0
    if mastery.last_answer_time:
        days = (datetime.utcnow() - mastery.last_answer_time).days
        recency = max(0, 5 - days)
    return ws * 0.4 + cw * 2.5 + qa * 0.5 + recency * 0.5


def _recently_recommended(db: Session, user_id: int, hours: int = 2) -> set[tuple[str, str]]:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(QuestionGenerationSession)
        .filter(
            QuestionGenerationSession.user_id == user_id,
            QuestionGenerationSession.create_time >= cutoff,
        )
        .all()
    )
    return {(r.subject, r.knowledge_point) for r in rows}


def _masteries_with_scores(db: Session, user_id: int) -> list[tuple[KnowledgeMastery, float]]:
    rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user_id).all()
    scored = [(r, _urgency_score(r)) for r in rows]
    scored.sort(key=lambda x: -x[1])
    return scored


def build_smart_recommendations(db: Session, user_id: int) -> list[dict]:
    mastery_rows = (
        db.query(KnowledgeMastery)
        .filter(KnowledgeMastery.user_id == user_id)
        .all()
    )
    mistakes = (
        db.query(Mistake)
        .filter(Mistake.user_id == user_id, Mistake.status == "active")
        .order_by(desc(Mistake.create_time), desc(Mistake.id))
        .all()
    )
    memories = (
        db.query(UserMemory)
        .filter(
            UserMemory.user_id == user_id,
            UserMemory.memory_type == "weak_point",
            UserMemory.status == "active",
        )
        .order_by(desc(UserMemory.update_time), desc(UserMemory.id))
        .all()
    )
    baseline = _baseline_points(db)
    fallback = baseline[0] if baseline else None
    fallback_subject = fallback.subject if fallback else "数据结构"
    fallback_point = fallback.name if fallback else "线性表"

    recent = _recently_recommended(db, user_id)
    scored = _masteries_with_scores(db, user_id)

    weak_map: dict[str, KnowledgeMastery] = {}
    for m in mastery_rows:
        weak_map[(m.subject, m.knowledge_point)] = m

    # ── 薄弱点强化 ──
    scored_weak = [
        (m, s) for m, s in scored
        if m.final_status in {"薄弱点", "不会", "不熟"}
    ]
    if scored_weak:
        m, _ = scored_weak[0]
        ws = m.weak_score or 0
        weak_item = _point_payload(
            "薄弱点强化", m.subject, m.knowledge_point,
            f"{m.final_status} · 错 {m.wrong_count} 次 · 连续错 {m.continuous_wrong_count} 次，"
            f"优先生成 {_to_question_type(m, '薄弱点强化')} 专项题。",
            _to_difficulty(m),
            _to_question_type(m, "薄弱点强化"),
            _to_count(m, "薄弱点强化"),
        )
    elif memories:
        mem = memories[0]
        m = weak_map.get((mem.subject, mem.knowledge_point))
        weak_item = _point_payload(
            "薄弱点强化", mem.subject, mem.knowledge_point,
            "长期记忆仍标记为薄弱点，优先通过专项题验证。",
            _to_difficulty(m),
            _to_question_type(m, "薄弱点强化"),
            _to_count(m, "薄弱点强化"),
        )
    else:
        weak_item = _point_payload(
            "薄弱点强化", fallback_subject, fallback_point,
            "尚未形成薄弱点。先完成基线诊断，答题后系统会自动定位需要强化的知识点。",
            "简单", "选择题", 3,
            available=False, initial=True,
        )

    # ── 最近错题复练 ──
    if mistakes:
        lm = mistakes[0]
        m = weak_map.get((lm.subject, lm.knowledge_point))
        mistake_item = _point_payload(
            "最近错题复练", lm.subject, lm.knowledge_point,
            f"最近错题来自「{lm.knowledge_point}」（{lm.error_type or '未分类'}），"
            f"生成 {_to_count(m, '最近错题复练')} 道同类变式题检查是否真正理解错因。",
            _to_difficulty(m, "中等"),
            _to_question_type(m, "最近错题复练"),
            _to_count(m, "最近错题复练"),
        )
    else:
        mistake_item = _point_payload(
            "最近错题复练", fallback_subject, fallback_point,
            "暂无错题记录。完成一次答题并确认错因后，这里会自动生成错题复练。",
            "简单", "选择题", 2,
            available=False, initial=True,
        )

    # ── 高频提问专项 ──
    qa_sorted = sorted(
        [m for m in mastery_rows if (m.qa_count or 0) > 0],
        key=lambda r: -(r.qa_count or 0),
    )
    if qa_sorted:
        qa_m = qa_sorted[0]
        not_recent = [m for m in qa_sorted if (m.subject, m.knowledge_point) not in recent]
        if not_recent:
            qa_m = not_recent[0]
        qa_item = _point_payload(
            "高频提问专项", qa_m.subject, qa_m.knowledge_point,
            f"你已围绕该知识点提问 {qa_m.qa_count} 次，"
            f"适合把「问懂了」转化为「会做题」。",
            _to_difficulty(qa_m, "中等"),
            _to_question_type(qa_m, "高频提问专项"),
            _to_count(qa_m, "高频提问专项"),
        )
    else:
        qa_item = _point_payload(
            "高频提问专项", fallback_subject, fallback_point,
            "暂无可归类的高频提问。完成知识问答后，系统会按提问知识点生成专项题。",
            "中等", "填空题", 2,
            available=False, initial=True,
        )

    # ── 已改善知识点复测 ──
    improved_list = [
        m for m in mastery_rows
        if m.final_status == "掌握"
        and (m.subject, m.knowledge_point) not in recent
    ]
    if improved_list:
        imp = improved_list[0]
        improved_item = _point_payload(
            "已改善知识点复测", imp.subject, imp.knowledge_point,
            f"当前状态已掌握（答对 {imp.correct_count}/{imp.total_answer_count}），"
            f"提高难度复测掌握是否稳定。",
            "较难", "选择题", 2,
        )
    else:
        improved_item = _point_payload(
            "已改善知识点复测", fallback_subject, fallback_point,
            "暂无达到「掌握」的知识点。累计至少 3 次答题且正确率达到 80% 后开放复测。",
            "较难", "选择题", 2,
            available=False, initial=True,
        )

    # ── 四科随机综合 ──
    today = datetime.utcnow()
    seed = today.timetuple().tm_yday
    subject_index = (seed // 7) % 4  # rotate primary subject weekly
    qtype_index = (seed // 3) % 4     # rotate question type daily-ish

    primary_subject = _ALL_SUBJECTS[subject_index]
    primary_qtype = _ALL_QUESTION_TYPES[qtype_index]

    by_subject: dict[str, list[KnowledgePoint]] = {}
    for p in baseline:
        by_subject.setdefault(p.subject, []).append(p)
    primary_point = (by_subject.get(primary_subject) or [fallback])[seed % max(len(by_subject.get(primary_subject, [])), 1)]

    comprehensive_item = _point_payload(
        "四科随机综合",
        primary_subject,
        primary_point.name if primary_point else fallback_point,
        f"本周主推 {primary_subject}，题型轮换至 {primary_qtype}。"
        f"按 408 高频考点轮换抽取，用于建立或校准当前学习画像。",
        "中等",
        primary_qtype,
        3,
        initial=not any(r.total_answer_count for r in mastery_rows),
    )

    return [weak_item, mistake_item, qa_item, improved_item, comprehensive_item]


def resolve_smart_recommendation(db: Session, user_id: int, mode: str) -> dict:
    normalized_mode = mode if mode in SMART_MODES else "薄弱点强化"
    items = build_smart_recommendations(db, user_id)
    chosen = next(item for item in items if item["mode"] == normalized_mode)
    if chosen["available"]:
        return chosen
    return next(item for item in items if item["mode"] == "四科随机综合")


def choose_today_plan(db: Session, user_id: int) -> dict:
    items = build_smart_recommendations(db, user_id)
    chosen = next((item for item in items if item["available"] and item["mode"] != "四科随机综合"), None)
    if not chosen:
        chosen = next(item for item in items if item["mode"] == "四科随机综合")
        return {
            **chosen,
            "title": "先完成一次\n408 基线诊断",
            "reason": "你当前还没有稳定的答题或错题记录。系统会先从高频考点生成诊断题，完成后自动形成薄弱点和长期学习记忆。",
            "empty_state": True,
        }
    return {
        **chosen,
        "title": f"今天优先攻克\n{chosen['knowledge_point']}",
        "empty_state": False,
    }
