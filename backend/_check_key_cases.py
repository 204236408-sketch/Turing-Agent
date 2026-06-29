"""检查几个关键 case 的排序效果"""
from database import SessionLocal
from models import KnowledgePoint
from services.video_service import recommend_wangdao_for_knowledge_point
db = SessionLocal()
for section in ['二叉树的概念', '浮点数的表示与运算', 'TCP', '流量控制与可靠传输机制']:
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.section == section, KnowledgePoint.is_deleted == False).first()
    print(f'=== [{kp.subject}] {kp.section!r} (name={kp.name!r}) ===')
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=5)
    for it in result['items']:
        print(f'  score={it["final_score"]:.2f} kp=[{it["knowledge_point"]}]')
    print()
