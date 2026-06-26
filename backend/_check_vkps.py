import sys; sys.path.insert(0, '.')
from database import SessionLocal
from models import VideoResource
db = SessionLocal()
for subj in ["计算机组成原理", "操作系统", "数据结构", "计算机网络"]:
    rows = db.query(VideoResource).filter(VideoResource.subject==subj, VideoResource.is_deleted==False).all()
    kps = set((r.knowledge_point or '') for r in rows)
    print(f"\n{subj} ({len(rows)} videos):")
    for kp in sorted(kps):
        cnt = sum(1 for r in rows if r.knowledge_point==kp)
        print(f"  [{cnt}] {kp}")
db.close()
