"""检查 parent chapter matching 案例"""
from database import SessionLocal
from models import KnowledgePoint
from services.video_service import recommend_wangdao_for_knowledge_point, _split_kp_tokens
db = SessionLocal()
for section in ['虚拟内存管理', '高速缓冲存储器', '虚拟存储器', '计算机系统层次结构']:
    kp = db.query(KnowledgePoint).filter(
        KnowledgePoint.section == section, KnowledgePoint.is_deleted == False
    ).first()
    if not kp:
        continue
    print(f'=== [{kp.subject}] {kp.section!r} (name={kp.name!r}) ===')
    print(f'  sec_tokens: {_split_kp_tokens(kp.section, exclude={kp.subject})!r}')
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=3)
    for it in result['items']:
        print(f"  score={it['final_score']:.2f} kp=[{it['knowledge_point']}] title=[{it['title'][:50]}]")
    print()
