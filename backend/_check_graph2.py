"""直接调用 _wangdao_match_score 看实际分数"""
from database import SessionLocal
from models import VideoResource
from services.video_service import _wangdao_match_score, _split_kp_tokens
db = SessionLocal()

kp_section = "图的遍历"
kp_name = "图"
subject = "数据结构"

sec_tokens = _split_kp_tokens(kp_section, exclude={subject})
print(f"sec_tokens: {sec_tokens!r}")

for v_kp in ["图的深度优先遍历", "图的广度优先遍历", "图的基本操作"]:
    v = db.query(VideoResource).filter(
        VideoResource.subject == subject,
        VideoResource.knowledge_point == v_kp,
    ).first()
    if not v:
        print(f"  没找到: {v_kp}")
        continue
    s = _wangdao_match_score(v, kp_name, kp_section, subject)
    print(f"  kp=[{v_kp}] score={s}")
