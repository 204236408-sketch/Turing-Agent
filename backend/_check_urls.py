import sys; sys.path.insert(0, '.')
from database import SessionLocal
from models import VideoResource
db = SessionLocal()
rows = db.query(VideoResource).filter(VideoResource.is_deleted==False).limit(15).all()
for r in rows:
    print(f"id={r.id} | {r.subject}/{r.knowledge_point}")
    print(f"  title: {r.title}")
    print(f"  url: {r.url}")
    print()
db.close()
