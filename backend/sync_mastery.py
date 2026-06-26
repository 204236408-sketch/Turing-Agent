import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import KnowledgePoint, KnowledgeMastery, User
from services.mastery_service import synchronize_user_mastery

def main():
    db = SessionLocal()
    try:
        points = [(p.subject, p.name) for p in db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()]
        unique_points = list(dict.fromkeys(points))
        print(f"Total unique (subject, chapter) pairs: {len(unique_points)}")
        
        old_mastery = db.query(KnowledgeMastery).all()
        print(f"Existing mastery records: {len(old_mastery)}")
        for m in old_mastery:
            print(f"  {m.user_id}: {m.subject}/{m.knowledge_point} - total={m.total_answer_count}, wrong={m.wrong_count}")
        
        users = db.query(User).all()
        for user in users:
            synchronize_user_mastery(db, user.id, unique_points)
        
        db.commit()
        
        new_mastery = db.query(KnowledgeMastery).all()
        print(f"\nAfter sync, mastery records: {len(new_mastery)}")
        
        for user in users:
            user_mastery = [m for m in new_mastery if m.user_id == user.id]
            print(f"  User {user.username} ({user.id}): {len(user_mastery)} mastery records")
    finally:
        db.close()

if __name__ == "__main__":
    main()
