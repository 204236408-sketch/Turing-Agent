"""知识点掌握度计算：综合分（0~100）为唯一事实，状态由分数派生。

设计原则（修复合并自上方沟通后确立）：
- mastery_score（综合分）由本模块的 compute_mastery_score 唯一计算并写入
- final_status 由 mastery_score 经 _score_to_status 派生，保证两字段严格一致
- 状态五档：未学(0) / 薄弱点(1-19) / 不会(20-49) / 不熟(50-79) / 掌握(80+)
- 连续错 / weak_score / user_mark_status 都参与综合分计算
- 近 7 天窗口：连续错只统计 7 天内的错误，弱分按 14 天半衰期衰减
- 用户手动标记需 3 次答题冷却，未冷却则降权
- 章节 / 科目聚合统一在 knowledge_graph_service 用 mastery_score 平均，不再各自重新判定
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from models import AnswerRecord, ForumPost, KnowledgeMastery, KnowledgePoint, Mistake, Question, UserMemory


# ── 状态档位定义（与 knowledge_graph_service 保持一致） ──────────────────
STATUS_ORDER = ["weak", "unknown", "unfamiliar", "mastered", "unlearned"]
STATUS_META = {
    "mastered":   {"label": "掌握",   "score": 100, "color": "#2fbf7a"},
    "unfamiliar": {"label": "不熟",   "score": 60,  "color": "#f5bd22"},
    "unknown":    {"label": "不会",   "score": 30,  "color": "#ff9f43"},
    "weak":       {"label": "薄弱点", "score": 10,  "color": "#ff6262"},
    "unlearned":  {"label": "未学",   "score": 0,   "color": "#a8b0bf"},
}
STATUS_ALIASES = {
    "掌握": "mastered", "已掌握": "mastered", "mastered": "mastered",
    "不熟": "unfamiliar", "正在学习": "unfamiliar", "unfamiliar": "unfamiliar",
    "不会": "unknown", "unknown": "unknown",
    "薄弱点": "weak", "薄弱": "weak", "weak": "weak",
    "未学": "unlearned", "unlearned": "unlearned",
    "": "unlearned", None: "unlearned",
}

# 权重分配：四档加权求和
SCORE_WEIGHTS = {
    "answer_performance": 0.50,  # 答题表现
    "user_feedback": 0.20,       # 用户反馈（手动标记优先，附冷却）
    "mistake_penalty": 0.20,    # 错题惩罚
    "learning_behavior": 0.10,  # 学习行为
}

# 时间窗口
RECENT_WINDOW_DAYS = 7
WEAK_SCORE_HALFLIFE_DAYS = 14
USER_MARK_COOLDOWN_ANSWERS = 3  # 标记后至少 3 次答题才完全生效


def normalize_status(status: str | None) -> str:
    return STATUS_ALIASES.get(status, "unlearned")


def status_score(status: str | None) -> int:
    return STATUS_META[normalize_status(status)]["score"]


def status_label(status: str | None) -> str:
    return STATUS_META[normalize_status(status)]["label"]


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> int:
    return round(max(lo, min(hi, value)))


def _score_to_status(score: int) -> str:
    """综合分 → 状态档位（唯一映射，所有页面统一）。"""
    if score >= 80:
        return "mastered"
    if score >= 50:
        return "unfamiliar"
    if score >= 20:
        return "unknown"
    if score > 0:
        return "weak"
    return "unlearned"


# ── 数据源加载 ──────────────────────────────────────────────────────────
def get_or_create_mastery(db: Session, user_id: int, subject: str, knowledge_point: str) -> KnowledgeMastery:
    mastery = (
        db.query(KnowledgeMastery)
        .filter(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.subject == subject,
            KnowledgeMastery.knowledge_point == knowledge_point,
        )
        .first()
    )
    if not mastery:
        mastery = KnowledgeMastery(user_id=user_id, subject=subject, knowledge_point=knowledge_point)
        db.add(mastery)
        db.flush()
    return mastery


def _split_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    import re
    return [part.strip() for part in re.split(r"[,，;；、\s]+", value) if len(part.strip()) >= 2]


def _point_name(point: KnowledgePoint) -> str:
    return (point.section or point.name or "").strip()


def _best_child_point(children: list[KnowledgePoint], evidence_text: str) -> tuple[str, int]:
    if not children:
        return "", 0
    text = evidence_text or ""
    best_name = _point_name(children[0])
    best_score = -1
    aliases = {
        "数组和特殊矩阵": ["稀疏矩阵", "特殊矩阵", "矩阵", "压缩存储", "三元组"],
        "队列": ["队列", "循环队列", "顺序队列"],
        "栈": ["栈", "入栈", "出栈", "栈顶"],
        "串的模式匹配": ["模式匹配", "KMP", "next数组", "子串匹配"],
    }
    for child in children:
        name = _point_name(child)
        if not name:
            continue
        score = 0
        if name and name in text:
            score += 100
        if child.section and child.section in text:
            score += 80
        for alias in aliases.get(name, []):
            if alias in text:
                score += 70
        for keyword in _split_keywords(child.keywords):
            if keyword in text:
                score += 20
        for keyword in _split_keywords(child.content)[:20]:
            if keyword in text:
                score += 4
        if score > best_score:
            best_score = score
            best_name = name
    return best_name, max(best_score, 0)


def _llm_child_point(children: list[KnowledgePoint], evidence_text: str, fallback: str) -> str:
    try:
        from services.llm_service import chat_json
        candidates = [
            {
                "name": _point_name(child),
                "keywords": child.keywords or "",
                "content": (child.content or "")[:160],
                "common_mistakes": (child.common_mistakes or "")[:120],
            }
            for child in children
            if _point_name(child)
        ]
        allowed = {item["name"] for item in candidates}
        if len(allowed) <= 1:
            return fallback
        prompt = f"""请把题目归类到最匹配的一个三级知识点。
要求：
1. 只能从候选三级知识点中选择一个 name；
2. 如果题干包含稀疏矩阵、特殊矩阵、数组压缩存储，优先选择数组相关知识点；
3. 如果证据不足，选择最接近题干核心对象的候选。

候选三级知识点：
{json.dumps(candidates, ensure_ascii=False)}

题目证据：
{(evidence_text or '')[:1200]}

只输出 JSON：{{"knowledge_point":"候选 name","confidence":0.0到1.0,"reason":"一句话理由"}}"""
        result = chat_json(
            [
                {"role": "system", "content": "你是 408 知识点归类器。只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            {"knowledge_point": fallback, "confidence": 0, "reason": "fallback"},
            temperature=0.0,
            max_tokens=300,
        )
        picked = str((result.data or {}).get("knowledge_point") or "").strip()
        return picked if picked in allowed else fallback
    except Exception:
        return fallback


def resolve_mastery_point(
    db: Session,
    subject: str,
    knowledge_point: str,
    question_id: int | None = None,
) -> str:
    """Return the canonical third-level knowledge point used by graph/mastery.

    Older question-generation paths sometimes stored a chapter name in
    Question.knowledge_point. The graph indexes mastery by KnowledgePoint.section,
    so write paths must normalize chapter labels to a concrete child point.
    """
    kp = (knowledge_point or "").strip()
    if not db or not subject or not kp:
        return kp

    exists = (
        db.query(KnowledgePoint.id)
        .filter(
            KnowledgePoint.subject == subject,
            KnowledgePoint.section == kp,
            KnowledgePoint.is_deleted == False,
        )
        .first()
    )
    if exists:
        return kp

    children = (
        db.query(KnowledgePoint)
        .filter(
            KnowledgePoint.subject == subject,
            KnowledgePoint.name == kp,
            KnowledgePoint.is_deleted == False,
        )
        .order_by(KnowledgePoint.id.asc())
        .all()
    )
    if not children:
        return kp

    evidence = ""
    if question_id:
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            evidence = "\n".join([
                question.question_text or "",
                question.explanation or "",
                question.easy_mistakes or "",
            ])
    best_name, score = _best_child_point(children, evidence)
    if score >= 20:
        return best_name or kp
    return _llm_child_point(children, evidence, best_name or kp)


def _recent_window(now: datetime | None = None) -> datetime:
    now = now or datetime.utcnow()
    return now - timedelta(days=RECENT_WINDOW_DAYS)


def _decayed_wrong_count(records: list[AnswerRecord], now: datetime | None = None) -> tuple[int, int]:
    """返回 (近7天错题数, 近7天答题数)。错题数已含 14 天半衰期权重。"""
    if not records:
        return 0, 0
    now = now or datetime.utcnow()
    cutoff = _recent_window(now)
    half_life = WEAK_SCORE_HALFLIFE_DAYS
    wrong = 0
    total = 0
    for r in records:
        ctime = r.create_time
        if not ctime or ctime < cutoff:
            continue
        # 半衰期衰减：14 天前权重 0.5，28 天前 0.25
        age_days = max(0.0, (now - ctime).total_seconds() / 86400.0)
        weight = 0.5 ** (age_days / half_life)
        total += 1
        if not r.is_correct:
            wrong += 1 * weight
    return round(wrong), total


def _load_records(db: Session, user_id: int, subject: str, knowledge_point: str) -> list[AnswerRecord]:
    return (
        db.query(AnswerRecord)
        .filter(
            AnswerRecord.user_id == user_id,
            AnswerRecord.subject == subject,
            AnswerRecord.knowledge_point == knowledge_point,
        )
        .order_by(AnswerRecord.create_time.asc(), AnswerRecord.id.asc())
        .all()
    )


# ── 综合分四档子分（与原 knowledge_graph_service.compute_mastery_score 逻辑保持一致，
#    但修复了「user_mark 100% 覆盖」的硬伤，引入冷却衰减） ─────────────
def _answer_performance_score(row: KnowledgeMastery | None, recent_total: int) -> int:
    if row is None or not row.total_answer_count:
        return 0
    score = (row.correct_count or 0) * 100 / max(row.total_answer_count or 0, 1)
    # 样本不足与近期连错时封顶
    if (row.total_answer_count or 0) < 3:
        score = min(score, 70)
    if (row.recent_wrong_7d or 0) >= 2:
        score = min(score, 40)
    # 7 天内无活跃：衰减答题表现的 30%（防远古一次性刷分后状态长期不回落）
    if recent_total == 0 and (row.total_answer_count or 0) > 0:
        score = score * 0.7
    return _clamp(score)


def _user_feedback_score(row: KnowledgeMastery | None, answer_score: int, answers_after_mark: int) -> int:
    """用户标记在冷却期内按 0.5 降权（不强制 100% 覆盖）。"""
    if row is None:
        return 0
    explicit = normalize_status(row.user_mark_status)
    if explicit == "unlearned":
        # 无标记：退回 final_status 或答题分
        if row.total_answer_count:
            return answer_score
        inferred = normalize_status(row.final_status)
        return STATUS_META[inferred]["score"] if inferred != "unlearned" else 0
    # 有标记：按状态对应分 + 冷却降权
    base = STATUS_META[explicit]["score"]
    cooldown_factor = 1.0 if answers_after_mark >= USER_MARK_COOLDOWN_ANSWERS else 0.5
    # 用最终综合分（已知）混合：标记占 60%、answer_score 占 40%
    return _clamp(base * cooldown_factor * 0.6 + answer_score * 0.4)


def _mistake_penalty_score(row: KnowledgeMastery | None) -> int:
    if row is None or row.total_answer_count == 0 and not row.weak_score:
        return 0
    wrong = row.wrong_count or 0
    cw = row.continuous_wrong_count or 0
    ocr = row.ocr_mistake_count or 0
    weak_penalty = min(40, (row.weak_score or 0) * 3)
    # 7 天连错加权
    recent_wrong = row.recent_wrong_7d or 0
    return _clamp(100 - wrong * 12 - cw * 15 - ocr * 8 - weak_penalty - recent_wrong * 4)


def _learning_behavior_score(row: KnowledgeMastery | None) -> int:
    if row is None:
        return 0
    return _clamp(
        (row.total_answer_count or 0) * 20
        + (row.qa_count or 0) * 10
        + (row.forum_count or 0) * 5
    )


def compute_mastery_score(
    row: KnowledgeMastery | None,
    *,
    answers_after_mark: int = 0,
    recent_total: int = 0,
) -> tuple[int, str, dict[str, int]]:
    """计算综合分；返回 (score, status_key, source_scores)。

    无行为数据 → 0, unlearned。
    """
    empty = {key: 0 for key in SCORE_WEIGHTS}
    if row is None or (row.total_answer_count or 0) == 0 and not (row.qa_count or 0) and not (row.forum_count or 0) and not (row.user_mark_status):
        return 0, "unlearned", empty

    answer_score = _answer_performance_score(row, recent_total)
    source_scores = {
        "answer_performance": answer_score,
        "user_feedback": _user_feedback_score(row, answer_score, answers_after_mark),
        "mistake_penalty": _mistake_penalty_score(row),
        "learning_behavior": _learning_behavior_score(row),
    }
    score = sum(source_scores[key] * SCORE_WEIGHTS[key] for key in SCORE_WEIGHTS)

    # 硬约束：用户标记为薄弱点 / final_status 持久薄弱点 / weak_score 高 → 压到薄弱点档
    explicit = normalize_status(row.user_mark_status if row else None)
    final = normalize_status(row.final_status if row else None)
    if explicit == "weak" or final == "weak" or (row and (row.weak_score or 0) >= 10):
        score = min(score, 19)
    elif row and ((row.recent_wrong_7d or 0) >= 3 or (row.wrong_count or 0) >= 3):
        score = min(score, 49)

    mastery_score = _clamp(score)
    return mastery_score, _score_to_status(mastery_score), source_scores


# ── 主入口：重算并持久化 ──────────────────────────────────────────────
def recalculate_mastery(db: Session, user_id: int, subject: str, knowledge_point: str) -> KnowledgeMastery:
    """基于答题记录、错因、记忆标记等重新计算某个知识点的掌握状态。

    写入：
      - mastery_score（0~100）
      - final_status（由 mastery_score 派生，五档状态）
      - recent_wrong_7d / recent_answer_7d（近 7 天窗口统计，供前端展示）
      - 其它基础统计量（total/correct/wrong/...）保持原有口径
    """
    mastery = get_or_create_mastery(db, user_id, subject, knowledge_point)

    records = _load_records(db, user_id, subject, knowledge_point)
    mistakes = (
        db.query(Mistake)
        .filter(
            Mistake.user_id == user_id,
            Mistake.subject == subject,
            Mistake.knowledge_point == knowledge_point,
            Mistake.status == "active",
        )
        .all()
    )
    weak_memories = (
        db.query(UserMemory)
        .filter(
            UserMemory.user_id == user_id,
            UserMemory.subject == subject,
            UserMemory.knowledge_point == knowledge_point,
            UserMemory.memory_type == "weak_point",
            UserMemory.status == "active",
        )
        .count()
    )
    forum_count = (
        db.query(ForumPost)
        .filter(
            ForumPost.user_id == user_id,
            ForumPost.subject == subject,
            ForumPost.knowledge_point == knowledge_point,
            ForumPost.status == "normal",
        )
        .count()
    )

    total_answer_count = len(records)
    correct_count = sum(1 for r in records if r.is_correct)
    wrong_count = total_answer_count - correct_count
    unfamiliar_count = sum(1 for r in records if r.mastery_feedback == "不熟")
    unknown_count = sum(1 for r in records if r.mastery_feedback == "不会")
    mastered_count = sum(1 for r in records if r.mastery_feedback == "掌握")

    mastery.total_answer_count = total_answer_count
    mastery.correct_count = correct_count
    mastery.wrong_count = wrong_count
    mastery.unfamiliar_count = unfamiliar_count
    mastery.unknown_count = unknown_count
    mastery.mastered_count = mastered_count
    mastery.ocr_mistake_count = sum(1 for m in mistakes if "ocr" in (m.input_type or "").lower())
    mastery.forum_count = forum_count
    mastery.last_answer_time = records[-1].create_time if records else None

    marked = [r for r in records if r.mastery_feedback in {"掌握", "不熟", "不会"}]
    if marked:
        mastery.user_mark_status = marked[-1].mastery_feedback
        mastery.user_mark_at = marked[-1].create_time

    # 7 天窗口 + 半衰期
    recent_wrong, recent_total = _decayed_wrong_count(records)
    mastery.recent_wrong_7d = recent_wrong
    mastery.recent_answer_7d = recent_total

    # 连续错：仅在 7 天窗口内回溯
    cw = 0
    for r in reversed(records):
        if r.create_time and r.create_time < _recent_window():
            break
        if r.is_correct:
            break
        cw += 1
    mastery.continuous_wrong_count = cw

    # 错因分析
    rule_confusion = sum(1 for m in mistakes if "规则混淆" in (m.error_type or ""))
    concept_error = sum(1 for m in mistakes if "概念理解错误" in (m.error_type or ""))

    # weak_score：14 天半衰期，错误行为随时间衰减
    now = datetime.utcnow()
    # 找到最近一次答题行为的时间，作为衰减起点
    last_activity = mastery.last_answer_time or now
    age_days = max(0.0, (now - last_activity).total_seconds() / 86400.0)
    decay = 0.5 ** (age_days / WEAK_SCORE_HALFLIFE_DAYS)  # 默认按 last_answer_time 衰减
    if not records:
        decay = 1.0
    mastery.weak_score = max(
        0.0,
        wrong_count * 3 * decay
        + unfamiliar_count * 2
        + unknown_count * 4
        + mastery.ocr_mistake_count * 3
        + rule_confusion * 2
        + concept_error * 2
        + (mastery.qa_count or 0)
        + forum_count
        - correct_count
        - mastered_count * 2,
    )

    # 计算冷却（标记后答题数）
    answers_after_mark = 0
    if mastery.user_mark_at:
        answers_after_mark = sum(1 for r in records if r.create_time and r.create_time > mastery.user_mark_at)

    has_behavior = bool(
        records or mistakes or weak_memories
        or mastery.qa_count or forum_count
        or mastery.user_mark_status
    )

    if not has_behavior:
        mastery.mastery_score = 0
        mastery.final_status = "未学"
    else:
        score, status_key, _ = compute_mastery_score(
            mastery, answers_after_mark=answers_after_mark, recent_total=recent_total
        )
        mastery.mastery_score = score
        mastery.final_status = status_label(status_key)

    db.flush()
    return mastery


def apply_manual_feedback(
    db: Session, user_id: int, subject: str, knowledge_point: str, status: str,
    mistake_id: int | None = None, question_id: int | None = None,
) -> KnowledgeMastery:
    """用户手动标记某个知识点的掌握状态。标记后冷却 3 次答题。"""
    knowledge_point = resolve_mastery_point(db, subject, knowledge_point, question_id)
    mastery = get_or_create_mastery(db, user_id, subject, knowledge_point)
    now = datetime.utcnow()
    mastery.user_mark_status = status
    mastery.user_mark_at = now

    if mistake_id:
        mistake = db.query(Mistake).filter(Mistake.id == mistake_id, Mistake.user_id == user_id).first()
        if mistake:
            mistake.mastery_status = status
    else:
        mistake = (
            db.query(Mistake)
            .filter(
                Mistake.user_id == user_id,
                Mistake.subject == subject,
                Mistake.knowledge_point == knowledge_point,
                Mistake.status == "active",
            )
            .order_by(Mistake.create_time.desc(), Mistake.id.desc())
            .first()
        )
        if mistake:
            mistake.mastery_status = status
        elif status in ("不熟", "不会"):
            latest_wrong = (
                db.query(AnswerRecord)
                .filter(
                    AnswerRecord.user_id == user_id,
                    AnswerRecord.subject == subject,
                    AnswerRecord.knowledge_point == knowledge_point,
                    AnswerRecord.is_correct == False,
                )
                .order_by(AnswerRecord.create_time.desc(), AnswerRecord.id.desc())
                .first()
            )
            if latest_wrong:
                from models import Mistake as _M
                mistake = _M(
                    user_id=user_id,
                    answer_record_id=latest_wrong.id,
                    question_id=latest_wrong.question_id,
                    subject=subject,
                    knowledge_point=knowledge_point,
                    error_type="手动标记",
                    error_reason=f"用户手动标记为「{status}」",
                    suggestion="建议重新学习该知识点并做同类练习",
                    input_type="系统出题",
                )
                db.add(mistake)
                db.flush()
                mistake.mastery_status = status
            elif question_id:
                from models import Question as _Q
                question = db.query(_Q).filter(_Q.id == question_id).first()
                if question:
                    from models import Mistake as _M
                    mistake = _M(
                        user_id=user_id,
                        answer_record_id=None,
                        question_id=question.id,
                        subject=question.subject,
                        knowledge_point=question.knowledge_point,
                        error_type="手动标记",
                        error_reason=f"用户在题目页手动标记为「{status}」",
                        suggestion="建议重新学习该知识点并做同类练习",
                        input_type="系统出题",
                    )
                    db.add(mistake)
                    db.flush()
                    mistake.mastery_status = status

    latest = (
        db.query(AnswerRecord)
        .filter(
            AnswerRecord.user_id == user_id,
            AnswerRecord.subject == subject,
            AnswerRecord.knowledge_point == knowledge_point,
        )
        .order_by(AnswerRecord.create_time.desc(), AnswerRecord.id.desc())
        .first()
    )
    if latest:
        latest.mastery_feedback = status
    return recalculate_mastery(db, user_id, subject, knowledge_point)


def synchronize_user_mastery(
    db: Session, user_id: int, points: list[tuple[str, str]]
) -> list[KnowledgeMastery]:
    """批量同步多个知识点的掌握状态。"""
    return [recalculate_mastery(db, user_id, subject, point) for subject, point in points]
