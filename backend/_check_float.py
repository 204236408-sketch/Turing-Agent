"""检查浮点数推荐 + alignment"""
from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.video_service import _wangdao_match_score, _wangdao_section_alignment
db = SessionLocal()
kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.section == "浮点数的表示与运算", KnowledgePoint.is_deleted == False
).first()
print(f'KP: {kp.name!r} / {kp.section!r}')
videos = db.query(VideoResource).filter(
    VideoResource.subject == "计算机组成原理",
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
    VideoResource.is_active == True,
).all()
scored = []
for v in videos:
    if "浮点" not in (v.knowledge_point or ""):
        continue
    s = _wangdao_match_score(v, kp.name, kp.section, kp.subject)
    a = _wangdao_section_alignment(v, kp.name, kp.section, kp.subject)
    if s >= 45:
        scored.append((s, a, v.id, v.knowledge_point, v.quality_score or 80, len(v.knowledge_point or '')))
scored.sort(key=lambda x: (-x[0], -x[1], -x[2], -x[4], x[5]))
print()
for s, a, vid, vkp, q, l in scored:
    print(f"  score={s:3d} align={a:3d} id={vid} q={q} len={l} kp=[{vkp}]")
