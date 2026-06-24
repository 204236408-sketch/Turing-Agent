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


def recalculate_mastery(db: Session, user_id: int, subject: str, knowledge_point: str) -> KnowledgeMastery:
    mastery = get_or_create_mastery(db, user_id, subject, knowledge_point)
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
    mastery.total_answer_count = len(records)
    mastery.correct_count = sum(1 for item in records if item.is_correct)
    mastery.wrong_count = mastery.total_answer_count - mastery.correct_count
    mastery.unfamiliar_count = sum(1 for item in records if item.mastery_feedback == "不熟")
    mastery.unknown_count = sum(1 for item in records if item.mastery_feedback == "不会")
    mastery.mastered_count = sum(1 for item in records if item.mastery_feedback == "掌握")
    mastery.ocr_mistake_count = sum(1 for item in mistakes if "ocr" in (item.input_type or "").lower())
    mastery.forum_count = forum_count
    mastery.last_answer_time = records[-1].create_time if records else None
    marked_records = [item for item in records if item.mastery_feedback in {"掌握", "不熟", "不会"}]
    if marked_records:
        mastery.user_mark_status = marked_records[-1].mastery_feedback

    continuous_wrong = 0
    for item in reversed(records):
        if item.is_correct:
            break
        continuous_wrong += 1
    mastery.continuous_wrong_count = continuous_wrong

    rule_confusion_count = sum(1 for item in mistakes if "规则混淆" in (item.error_type or ""))
    concept_error_count = sum(1 for item in mistakes if "概念理解错误" in (item.error_type or ""))
    repeated_error_type = any(count >= 2 for error, count in Counter(item.error_type for item in mistakes if item.error_type).items())
    mastery.weak_score = (
        mastery.wrong_count * 3
        + mastery.unfamiliar_count * 2
        + mastery.unknown_count * 4
        + mastery.ocr_mistake_count * 3
        + rule_confusion_count * 2
        + concept_error_count * 2
        + mastery.qa_count
        + mastery.forum_count
        - mastery.correct_count
        - mastery.mastered_count * 2
    )
    has_behavior = bool(
        records
        or mistakes
        or weak_memories
        or mastery.qa_count
        or mastery.forum_count
        or mastery.user_mark_status
    )
    correct_rate = mastery.correct_count / mastery.total_answer_count if mastery.total_answer_count else 0
    if not has_behavior:
        mastery.final_status = "未学"
    elif mastery.user_mark_status == "不会":
        mastery.final_status = "不会"
    elif (
        mastery.wrong_count >= 3
        or mastery.weak_score >= 10
        or repeated_error_type
        or weak_memories > 0
        or len({item.input_type for item in mistakes if item.input_type}) >= 3
    ):
        mastery.final_status = "薄弱点"
    elif (
        (mastery.total_answer_count > 0 and correct_rate < 0.5)
        or mastery.user_mark_status == "不会"
        or mastery.continuous_wrong_count >= 2
        or (mastery.total_answer_count >= 2 and mastery.correct_count == 0)
        or concept_error_count > 0
    ):
        mastery.final_status = "不会"
    elif (
        (0 < mastery.total_answer_count < 3)
        or (0.5 <= correct_rate < 0.8)
        or mastery.user_mark_status == "不熟"
        or mastery.wrong_count in (1, 2)
        or mastery.qa_count >= 2
    ):
        mastery.final_status = "不熟"
    elif (
        mastery.total_answer_count >= 3
        and correct_rate >= 0.8
        and mastery.wrong_count <= 1
        and mastery.user_mark_status not in {"不熟", "不会"}
        and weak_memories == 0
        and mastery.weak_score <= 2
    ):
        mastery.final_status = "掌握"
    else:
        mastery.final_status = "不熟"
    db.flush()
    return mastery


def apply_manual_feedback(db: Session, user_id: int, subject: str, knowledge_point: str, status: str,
                          mistake_id: int | None = None, question_id: int | None = None) -> KnowledgeMastery:
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
    mastery.user_mark_status = status
    if status == "掌握":
        mastery.mastered_count += 1
    elif status == "不熟":
        mastery.unfamiliar_count += 1
    elif status == "不会":
        mastery.unknown_count += 1
    return recalculate_mastery(db, user_id, subject, knowledge_point)


def synchronize_user_mastery(db: Session, user_id: int, points: list[tuple[str, str]]) -> list[KnowledgeMastery]:
    return [recalculate_mastery(db, user_id, subject, point) for subject, point in points]
