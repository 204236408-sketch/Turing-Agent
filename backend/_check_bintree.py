"""调试：二叉树的概念 case"""
from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.video_service import _wangdao_match_score, _split_kp_tokens, _strip_generic_suffix
db = SessionLocal()

kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.section == "二叉树的概念",
    KnowledgePoint.is_deleted == False
).first()
print(f"KP: id={kp.id} name={kp.name!r} section={kp.section!r}")

# 看看 section token 是什么
print(f"sec_stem: {_strip_generic_suffix(kp.section)!r}")
print(f"sec_tokens: {_split_kp_tokens(kp.section, exclude={kp.subject})!r}")

videos = db.query(VideoResource).filter(
    VideoResource.subject == "数据结构",
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
    VideoResource.is_active == True,
).all()

scored = []
for v in videos:
    s = _wangdao_match_score(v, kp.name, kp.section, kp.subject)
    if "二叉树" in (v.knowledge_point or "") and s >= 30:
        scored.append((s, -v.id, v.id, v.knowledge_point))
scored.sort(key=lambda x: (-x[0], x[1]))
print()
print("'二叉树' 相关视频的评分（≥30）：")
for s, _, vid, vkp in scored:
    print(f"  score={s:3d} id={vid} kp=[{vkp}]")
