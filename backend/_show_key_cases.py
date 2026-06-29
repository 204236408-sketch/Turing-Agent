from database import SessionLocal
from models import KnowledgePoint
from services.video_service import recommend_wangdao_for_knowledge_point

db = SessionLocal()
sections = ['虚拟内存管理', '高速缓冲存储器', '计算机系统层次结构', '数据结构三要素', '存储器概述', '操作系统的运行环境', '栈', '虚拟存储器', '数组和特殊矩阵']
for sec in sections:
    kp = db.query(KnowledgePoint).filter(
        KnowledgePoint.section == sec, KnowledgePoint.is_deleted == False
    ).first()
    if not kp:
        print(f'KP not found: {sec}')
        continue
    r = recommend_wangdao_for_knowledge_point(db, kp.id, limit=3)
    items = r['items']
    print(f'[{kp.subject}] {sec}  kp_name={kp.name}:')
    for i, it in enumerate(items, 1):
        score = it.get('final_score', 0)
        vkp = it.get('knowledge_point', '')
        print(f'  #{i} score={score:.2f}  v_kp=[{vkp}]')
    print()
