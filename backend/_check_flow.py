"""调试：流量控制与可靠传输机制 case"""
from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.video_service import _wangdao_match_score, _wangdao_section_alignment
db = SessionLocal()

kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.section == "流量控制与可靠传输机制",
    KnowledgePoint.is_deleted == False
).first()
print(f"KP: id={kp.id} name={kp.name!r} section={kp.section!r}")

# 关键视频
for v_kp_str in ["TCP可靠传输、流量控制（咸鱼版）", "流量控制、可靠传输与滑动窗口机制（咸鱼版）"]:
    v = db.query(VideoResource).filter(
        VideoResource.subject == "计算机网络",
        VideoResource.knowledge_point == v_kp_str,
    ).first()
    if not v:
        print(f"  没找到: {v_kp_str}")
        continue
    s = _wangdao_match_score(v, kp.name, kp.section, kp.subject)
    a = _wangdao_section_alignment(v, kp.name, kp.section, kp.subject)
    print(f"  kp=[{v_kp_str}]")
    print(f"    match_score={s}, alignment={a}, id={v.id}")
    print(f"    v_stem (after strip): {_wangdao_match_score.__globals__['_strip_generic_suffix'](v.knowledge_point)!r}")
    print()
