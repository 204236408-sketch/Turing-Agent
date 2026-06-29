"""调试：图的遍历 case"""
from database import SessionLocal
from models import VideoResource
from services.video_service import _wangdao_match_score, _wangdao_section_alignment
db = SessionLocal()
kp_section = "图的遍历"
kp_name = "图"
subject = "数据结构"
videos = db.query(VideoResource).filter(
    VideoResource.subject == subject,
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
).all()
scored = []
for v in videos:
    s = _wangdao_match_score(v, kp_name, kp_section, subject)
    a = _wangdao_section_alignment(v, kp_name, kp_section, subject)
    if s >= 45 or a > 0:
        scored.append((s, a, v.id, v.knowledge_point, v.quality_score, len(v.knowledge_point or '')))
scored.sort(key=lambda x: (-x[0], -x[1], -x[2], -x[4], x[5]))
print("所有相关视频：")
for s, a, vid, vkp, q, l in scored[:15]:
    print(f"  score={s:3d} align={a:3d} id={vid:3d} quality={q} len={l} kp=[{vkp}]")
