"""检查 内存管理概念 等案例的 sec_tokens"""
from database import SessionLocal
from models import KnowledgePoint
from services.video_service import _split_kp_tokens, _strip_generic_suffix, _wangdao_match_score, _wangdao_section_alignment, recommend_wangdao_for_knowledge_point
db = SessionLocal()

for section in ['内存管理概念', '数据结构的基本概念', '链式表示', '栈', '图的遍历']:
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.section == section, KnowledgePoint.is_deleted == False).first()
    if not kp:
        continue
    print(f'=== {kp.section!r} (name={kp.name!r}) ===')
    print(f"  sec_stem: {_strip_generic_suffix(kp.section)!r}")
    print(f"  sec_tokens: {_split_kp_tokens(kp.section, exclude={kp.subject})!r}")
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=3)
    for it in result['items']:
        top1_kp = it['knowledge_point']
        sec_tokens = _split_kp_tokens(kp.section, exclude={kp.subject})
        is_relevant = any(t in top1_kp for t in sec_tokens if len(t) >= 2)
        print(f"  {'[OK]' if is_relevant else '[BAD]'} kp=[{top1_kp}] is_relevant={is_relevant}")
        for t in sec_tokens:
            print(f"      token={t!r} in top1? {t in top1_kp}")
    print()
