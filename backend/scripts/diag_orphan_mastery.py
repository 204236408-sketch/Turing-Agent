"""一次性诊断脚本：检查 KnowledgeMastery 是否存在 KP 名称与 KnowledgePoint.section 不匹配的孤儿行。

如果发现，说明智能出题时把章节名当 KP 名传给 mastery，导致图谱聚合时找不到。
"""
from collections import defaultdict

from database import SessionLocal, init_database
from models import KnowledgeMastery, KnowledgePoint


def main() -> None:
    init_database()
    with SessionLocal() as db:
        # 收集所有 (subject, section) 合法 KP 名
        valid_pairs: set[tuple[str, str]] = set()
        chapter_pairs: set[tuple[str, str]] = set()
        for p in db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all():
            kp_name = (p.section or p.name or "").strip()
            ch_name = (p.name or "").strip()
            if p.subject and kp_name:
                valid_pairs.add((p.subject, kp_name))
            if p.subject and ch_name:
                chapter_pairs.add((p.subject, ch_name))

        print(f"合法 (subject, KP=section) 组合 = {len(valid_pairs)}")
        print(f"合法 (subject, chapter=name) 组合 = {len(chapter_pairs)}")

        rows = db.query(KnowledgeMastery).all()
        print(f"KnowledgeMastery 总行数 = {len(rows)}")

        orphan_section = []
        chapter_in_mastery = []
        for r in rows:
            if not r.subject or not r.knowledge_point:
                continue
            key = (r.subject, r.knowledge_point)
            if key not in valid_pairs:
                # 这条 mastery 找不到对应的 KP
                if key in chapter_pairs:
                    chapter_in_mastery.append(r)
                else:
                    orphan_section.append(r)

        print(f"孤儿 mastery 行（既非 KP 也非章节）= {len(orphan_section)}")
        for r in orphan_section[:5]:
            print(f"  - user={r.user_id} ({r.subject} / {r.knowledge_point})  status={r.final_status} score={r.mastery_score}")

        print(f"存了章节名当 KP 的 mastery 行 = {len(chapter_in_mastery)}")
        for r in chapter_in_mastery[:10]:
            print(f"  - user={r.user_id} ({r.subject} / {r.knowledge_point})  status={r.final_status} score={r.mastery_score}  wrong={r.wrong_count} correct={r.correct_count}")


if __name__ == "__main__":
    main()
