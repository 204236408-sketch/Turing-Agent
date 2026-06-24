from database import SessionLocal, init_database
from models import KnowledgeMastery
from services.mastery_service import recalculate_mastery


if __name__ == "__main__":
    init_database()
    with SessionLocal() as db:
        rows = db.query(KnowledgeMastery).all()
        for row in rows:
            recalculate_mastery(db, row.user_id, row.subject, row.knowledge_point)
        db.commit()
    print("知识点掌握状态重算完成")
