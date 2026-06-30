"""回填脚本：用新规则刷新所有 mastery_score 与 final_status。

适用：迁移 013_mastery_score.sql 之后，对存量数据进行一次性重算。
不依赖前端：纯数据库操作，跑完即生效。
"""
from database import SessionLocal, init_database
from models import KnowledgeMastery, KnowledgePoint, User
from services.mastery_service import recalculate_mastery


def point_kp_keys(point: KnowledgePoint) -> str:
    """与 knowledge_graph_service.point_name_of 保持一致：section → name"""
    return (point.section or point.name or "").strip()


def main() -> None:
    init_database()
    total_users = 0
    total_updated = 0
    with SessionLocal() as db:
        users = db.query(User).all()
        points = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        # 用 (subject, kp_name) 作为 mastery 写入 key
        kp_pairs = [(p.subject, point_kp_keys(p)) for p in points if point_kp_keys(p)]
        for user in users:
            total_users += 1
            for subject, kp in kp_pairs:
                try:
                    row = recalculate_mastery(db, user.id, subject, kp)
                    if row is not None:
                        total_updated += 1
                except Exception as exc:  # noqa: BLE001
                    print(f"[user={user.id} {subject}/{kp}] 重算失败：{exc}")
        db.commit()
    print(f"回填完成：用户 {total_users} 个、知识点行 {total_updated} 条刷新")


if __name__ == "__main__":
    main()
