"""查看 王道 数据结构 中"数组"和"矩阵"相关的视频。"""
import sys
sys.path.insert(0, "backend")
from database import SessionLocal
from models import VideoResource, KnowledgePoint

db = SessionLocal()
print("=== 王道 数据结构 中含'数组'或'矩阵'的 ===")
for v in db.query(VideoResource).filter(
    VideoResource.subject == "数据结构",
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
).order_by(VideoResource.section).all():
    kp = v.knowledge_point or ""
    if "数组" in kp or "矩阵" in kp or "稀疏" in kp:
        print(f"  sec={v.section!r:12s} kp={kp!r}")

print("\n=== KP '数组和特殊矩阵' 的实际 DB 字段 ===")
for r in db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == "数据结构",
    KnowledgePoint.name == "数组和特殊矩阵",
    KnowledgePoint.is_deleted == False,
).all():
    print(f"  id={r.id}  name={r.name!r}  section={r.section!r}  parent={r.parent_name!r}  level={r.level}")

db.close()
