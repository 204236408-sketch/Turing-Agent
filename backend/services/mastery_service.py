from collections import Counter

from sqlalchemy.orm import Session

from models import AnswerRecord, ForumPost, KnowledgeMastery, Mistake, Question, UserMemory


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


def recalculate_mastery(
    db: Session, user_id: int, subject: str, knowledge_point: str
) -> KnowledgeMastery:
    """基于答题记录、错因、记忆标记等重新计算某个知识点掌握状态。

    final_status 优先级（从高到低）:
        薄弱点 > 不会 > 不熟 > 掌握 > 未学
    """
    mastery = get_or_create_mastery(db, user_id, subject, knowledge_point)

    # ── 统计数据源 ──
    records = (
        db.query(AnswerRecord)
        .filter(
            AnswerRecord.user_id == user_id,
            AnswerRecord.subject == subject,
            AnswerRecord.knowledge_point == knowledge_point,
        )
        .order_by(AnswerRecord.create_time.asc(), AnswerRecord.id.asc())
        .all()
    )
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

    # ── 基础统计量 ──
    total_answer_count = len(records)
    correct_count = sum(1 for item in records if item.is_correct)
    wrong_count = total_answer_count - correct_count
    unfamiliar_count = sum(1 for item in records if item.mastery_feedback == "不熟")
    unknown_count = sum(1 for item in records if item.mastery_feedback == "不会")
    mastered_count = sum(1 for item in records if item.mastery_feedback == "掌握")

    mastery.total_answer_count = total_answer_count
    mastery.correct_count = correct_count
    mastery.wrong_count = wrong_count
    mastery.unfamiliar_count = unfamiliar_count
    mastery.unknown_count = unknown_count
    mastery.mastered_count = mastered_count
    mastery.ocr_mistake_count = sum(1 for item in mistakes if "ocr" in (item.input_type or "").lower())
    mastery.forum_count = forum_count
    mastery.last_answer_time = records[-1].create_time if records else None

    marked_records = [item for item in records if item.mastery_feedback in {"掌握", "不熟", "不会"}]
    if marked_records:
        mastery.user_mark_status = marked_records[-1].mastery_feedback

    # ── 连续错误分析 ──
    continuous_wrong = 0
    for item in reversed(records):
        if item.is_correct:
            break
        continuous_wrong += 1
    mastery.continuous_wrong_count = continuous_wrong

    # ── 错因分析 ──
    rule_confusion_count = sum(1 for item in mistakes if "规则混淆" in (item.error_type or ""))
    concept_error_count = sum(1 for item in mistakes if "概念理解错误" in (item.error_type or ""))
    repeated_error_type = any(
        count >= 2
        for error, count in Counter(item.error_type for item in mistakes if item.error_type).items()
    )

    # ── weak_score: 综合弱分（越高代表越薄弱）──
    mastery.weak_score = max(0,
        wrong_count * 3
        + unfamiliar_count * 2
        + unknown_count * 4
        + mastery.ocr_mistake_count * 3
        + rule_confusion_count * 2
        + concept_error_count * 2
        + mastery.qa_count
        + forum_count
        - correct_count
        - mastered_count * 2
    )

    # ── 是否有行为数据 ──
    has_behavior = bool(
        records or mistakes or weak_memories
        or mastery.qa_count or forum_count
        or mastery.user_mark_status
    )

    correct_rate = correct_count / total_answer_count if total_answer_count else 0

    # ── 状态判定（优先级：薄弱点 > 不会 > 不熟 > 掌握 > 未学）──
    if not has_behavior:
        mastery.final_status = "未学"

    # 等级 1: 薄弱点 — 连续错 ≥3 | weak_score≥10 | 重复同类错因 | 有弱记忆 | 3+ 题源类型
    elif (
        wrong_count >= 3
        or mastery.weak_score >= 10
        or repeated_error_type
        or weak_memories > 0
        or len({item.input_type for item in mistakes if item.input_type}) >= 3
    ):
        mastery.final_status = "薄弱点"

    # 等级 2: 不会 — 正确率<50% | 连续错 ≥2 | 从未答对 | 概念理解错误
    elif (
        (total_answer_count > 0 and correct_rate < 0.5)
        or continuous_wrong >= 2
        or (total_answer_count >= 2 and correct_count == 0)
        or concept_error_count > 0
    ):
        mastery.final_status = "不会"

<<<<<<< HEAD
    # 等级 3: 不熟 — 答题不足 | 正确率50-80% | 用户标记不熟 | 错1-2次 | 频繁提问
    elif (
        (0 < total_answer_count < 3)
        or (0.5 <= correct_rate < 0.8)
        or mastery.user_mark_status == "不熟"
=======
    # 等级 3: 不熟 — 答题不足 | 正确率50-80% | 错1-2次 | 频繁提问
    elif (
        (0 < total_answer_count < 3)
        or (0.5 <= correct_rate < 0.8)
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        or wrong_count in (1, 2)
        or mastery.qa_count >= 2
    ):
        mastery.final_status = "不熟"

    # 等级 4: 掌握 — ≥3次答题 | 正确率≥80% | 错≤1 | 无弱记忆 | 低 weak_score
    elif (
        total_answer_count >= 3
        and correct_rate >= 0.8
        and wrong_count <= 1
<<<<<<< HEAD
        and mastery.user_mark_status not in {"不熟", "不会"}
=======
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
        and weak_memories == 0
        and mastery.weak_score <= 2
    ):
        mastery.final_status = "掌握"

    # 兜底: 有行为但数据矛盾，保守归为"不熟"
    else:
        mastery.final_status = "不熟"

    db.flush()
    return mastery


def apply_manual_feedback(
    db: Session, user_id: int, subject: str, knowledge_point: str, status: str,
    mistake_id: int | None = None, question_id: int | None = None,
) -> KnowledgeMastery:
    """用户手动标记某个知识点的掌握状态。

    同时更新对应错题的 mastery_status 和最近一条答题记录的 mastery_feedback，
    随后调用 recalculate_mastery 统一重算所有统计量。
    """
    mastery = get_or_create_mastery(db, user_id, subject, knowledge_point)
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
                mistake = Mistake(
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
                question = db.query(Question).filter(Question.id == question_id).first()
                if question:
                    mistake = Mistake(
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
<<<<<<< HEAD
    mastery.user_mark_status = status
=======
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    return recalculate_mastery(db, user_id, subject, knowledge_point)


def synchronize_user_mastery(
    db: Session, user_id: int, points: list[tuple[str, str]]
) -> list[KnowledgeMastery]:
    """批量同步多个知识点的掌握状态。"""
    return [recalculate_mastery(db, user_id, subject, point) for subject, point in points]
