"""检查几个 BAD 案例的真实推荐结果"""
from database import SessionLocal
from models import KnowledgePoint
from services.video_service import recommend_wangdao_for_knowledge_point
db = SessionLocal()
for section_name in ['虚拟内存管理', '文件的表示与基本操作', 'CPU调度', '高速缓冲存储器', '差错控制', '顺序表与链表的比较', '二叉树的遍历']:
    kp = db.query(KnowledgePoint).filter(
        KnowledgePoint.section == section_name,
        KnowledgePoint.is_deleted == False
    ).first()
    if not kp:
        print(f'  没找到: {section_name}')
        continue
    print(f'=== [{kp.subject}] {kp.section!r} (name={kp.name!r}) ===')
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=3)
    print(f'  matched={result["wangdao_matched"]} passed={result["wangdao_passed"]} returned={result["total_returned"]}')
    for it in result['items']:
        print(f'  score={it["final_score"]:.2f} kp=[{it["knowledge_point"]}] title=[{it["title"][:60]}]')
    print()
