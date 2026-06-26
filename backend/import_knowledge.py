import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal, init_database
from models import KnowledgePoint, Subject
from services.seed_service import SUBJECTS

def main():
    init_database()
    db = SessionLocal()
    try:
        data_path = Path(__file__).parent / "data" / "seed_knowledge_points.json"
        if not data_path.exists():
            data_path = Path(__file__).parent / "seed_knowledge_points.json"
        print(f"Loading from: {data_path}")
        
        with open(data_path, "r", encoding="utf-8") as f:
            kp_list = json.load(f)
        
        for sub_name in SUBJECTS:
            sub = db.query(Subject).filter(Subject.name == sub_name).first()
            if not sub:
                sub = Subject(name=sub_name, description=f"408 {sub_name} 考纲知识体系")
                db.add(sub)
                db.flush()
        
        existing_count = db.query(KnowledgePoint).count()
        print(f"Existing knowledge points: {existing_count}")
        
        deleted = db.query(KnowledgePoint).delete()
        print(f"Deleted {deleted} old knowledge points")
        db.flush()
        
        added = 0
        for item in kp_list:
            sub_name = item["subject"]
            sub = db.query(Subject).filter(Subject.name == sub_name).first()
            if not sub:
                print(f"WARNING: subject {sub_name} not found, skipping")
                continue
            kp = KnowledgePoint(
                subject_id=sub.id,
                subject=sub_name,
                parent_name=item.get("parent_name", sub_name),
                name=item["name"],
                section=item.get("section", ""),
                level=item.get("level", 3),
                content=item.get("content", ""),
                common_mistakes=item.get("common_mistakes", ""),
                keywords=item.get("keywords", ""),
                is_high_frequency=item.get("is_high_frequency", False),
                is_deleted=False,
            )
            db.add(kp)
            added += 1
        
        db.commit()
        
        from collections import OrderedDict
        chapters = OrderedDict()
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).order_by(KnowledgePoint.subject, KnowledgePoint.id).all()
        for r in rows:
            key = (r.subject, r.name)
            if key not in chapters:
                chapters[key] = True
        
        print(f"\nImport complete! Added {added} knowledge points")
        print(f"Total in DB: {db.query(KnowledgePoint).count()}")
        print(f"\nChapters by subject:")
        for (sub, name), _ in chapters.items():
            print(f"  {sub} | {name}")
        print(f"\nTotal unique chapters: {len(chapters)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
