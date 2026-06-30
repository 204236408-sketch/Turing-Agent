"""一次性数据修复：把"章节名当 KP 名"的孤儿 mastery 行迁移/清理。

根因：智能出题 fallback 用 baseline.name（章节名）作为 KP 名，答题后写入
KnowledgeMastery 但与 KnowledgePoint.section 对不上，章节聚合时找不到。

修复策略：
1. 完全孤儿行（既不是 KP 名也不是章节名）：直接删除
2. 章节名误当 KP 名：把该行的 wrong/correct/ocr_mistake/qa/forum 计数，按比例分摊到
   该章节下"无 mastery 行"的具体 KP 上。统计量不可逆，所以按"该章节子 KP 数等分"。

迁移前后会回填 mastery_score 保持一致。
"""
import json
from collections import defaultdict

from database import SessionLocal, init_database
from models import KnowledgeMastery, KnowledgePoint
from services.mastery_service import recalculate_mastery


def main() -> None:
    init_database()
    with SessionLocal() as db:
        # 1. 收集 (subject, kp_name=section) 合法 KP 和 (subject, chapter_name=name) 合法章节
        valid_kp: set[tuple[str, str]] = set()
        chapter_to_kps: dict[tuple[str, str], list[KnowledgePoint]] = defaultdict(list)
        points = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        for p in points:
            kp_name = (p.section or p.name or "").strip()
            ch_name = (p.name or "").strip()
            if p.subject and kp_name:
                valid_kp.add((p.subject, kp_name))
            if p.subject and ch_name:
                chapter_to_kps[(p.subject, ch_name)].append(p)

        rows = db.query(KnowledgeMastery).all()
        print(f"扫描到 {len(rows)} 条 mastery")

        deleted_orphan = 0
        migrated_chapter = 0
        touched = 0

        for r in rows:
            key = (r.subject, r.knowledge_point)
            if not r.subject or not r.knowledge_point:
                continue
            if key in valid_kp:
                continue
            # 是章节名误存？
            ch_kps = chapter_to_kps.get(key)
            if ch_kps and (r.total_answer_count or 0) > 0:
                # 把统计量按子 KP 数量等分
                child_kp_names = [(p.subject, _kp_name(p)) for p in ch_kps if _kp_name(p)]
                if not child_kp_names:
                    db.delete(r)
                    deleted_orphan += 1
                    continue
                n = len(child_kp_names)
                split_wrong = (r.wrong_count or 0) // n
                split_correct = (r.correct_count or 0) // n
                split_total = (r.total_answer_count or 0) // n
                split_unfamiliar = (r.unfamiliar_count or 0) // n
                split_unknown = (r.unknown_count or 0) // n
                split_mastered = (r.mastered_count or 0) // n
                split_ocr = (r.ocr_mistake_count or 0) // n
                split_weak = (r.weak_score or 0.0) / n
                split_qa = (r.qa_count or 0) // n
                split_forum = (r.forum_count or 0) // n
                # 标记转移
                migrated_chapter += 1
                # 在子 KP 上创建/更新 mastery 行
                for sub, kn in child_kp_names:
                    target = (
                        db.query(KnowledgeMastery)
                        .filter(
                            KnowledgeMastery.user_id == r.user_id,
                            KnowledgeMastery.subject == sub,
                            KnowledgeMastery.knowledge_point == kn,
                        )
                        .first()
                    )
                    if target is None:
                        target = KnowledgeMastery(
                            user_id=r.user_id, subject=sub, knowledge_point=kn
                        )
                        db.add(target)
                    target.total_answer_count = (target.total_answer_count or 0) + split_total
                    target.correct_count = (target.correct_count or 0) + split_correct
                    target.wrong_count = (target.wrong_count or 0) + split_wrong
                    target.unfamiliar_count = (target.unfamiliar_count or 0) + split_unfamiliar
                    target.unknown_count = (target.unknown_count or 0) + split_unknown
                    target.mastered_count = (target.mastered_count or 0) + split_mastered
                    target.ocr_mistake_count = (target.ocr_mistake_count or 0) + split_ocr
                    target.weak_score = (target.weak_score or 0.0) + split_weak
                    target.qa_count = (target.qa_count or 0) + split_qa
                    target.forum_count = (target.forum_count or 0) + split_forum
                    if r.last_answer_time and (
                        not target.last_answer_time or r.last_answer_time > target.last_answer_time
                    ):
                        target.last_answer_time = r.last_answer_time
                    touched += 1
                # 删除原孤儿行
                db.delete(r)
            else:
                # 真正的孤儿：直接删除
                db.delete(r)
                deleted_orphan += 1

        # 重新回填所有行的 mastery_score 与 final_status
        all_subjects = db.query(KnowledgeMastery.subject).distinct().all()
        for (sub,) in all_subjects:
            rows_sub = db.query(KnowledgeMastery).filter(KnowledgeMastery.subject == sub).all()
            for row in rows_sub:
                recalculate_mastery(db, row.user_id, sub, row.knowledge_point)

        db.commit()
        print(f"已删除孤儿行 = {deleted_orphan}")
        print(f"已迁移章节名行 = {migrated_chapter}，影响子 KP mastery 行 = {touched}")
        print("已用新规则回填 mastery_score / final_status")


def _kp_name(point: KnowledgePoint) -> str:
    return (point.section or point.name or "").strip()


if __name__ == "__main__":
    main()
