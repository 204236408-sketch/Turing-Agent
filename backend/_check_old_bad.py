"""验证之前 BAD case 修复情况"""
import sys
sys.path.insert(0, '.')
from database import SessionLocal
from models import KnowledgePoint
from services.video_service import recommend_wangdao_for_knowledge_point

db = SessionLocal()

# 之前 BAD case 列表
bad_kp_ids = {
    179: '操作系统发展历程 (id=179)',
    180: '操作系统发展历程 (id=180)',
    185: '操作系统发展历程 (id=185)',
}

# 数据结构 链式表示
chain_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '数据结构',
    KnowledgePoint.section == '链式表示',
    KnowledgePoint.name == '线性表',
).first()
if chain_kp:
    bad_kp_ids[chain_kp.id] = '链式表示 (数据结构)'

# 指令集体系结构
isa_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '计算机组成原理',
    KnowledgePoint.section == '指令集体系结构',
).first()
if isa_kp:
    bad_kp_ids[isa_kp.id] = '指令集体系结构 (计组)'

# 内部排序
sort_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '数据结构',
    KnowledgePoint.section == '内部排序',
).first()
if sort_kp:
    bad_kp_ids[sort_kp.id] = '内部排序 (数据结构)'

# 树型查找
tree_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '数据结构',
    KnowledgePoint.section == '树型查找',
).first()
if tree_kp:
    bad_kp_ids[tree_kp.id] = '树型查找 (数据结构)'

# 存储器概述
mem_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '计算机组成原理',
    KnowledgePoint.section == '存储器概述',
).first()
if mem_kp:
    bad_kp_ids[mem_kp.id] = '存储器概述 (计组)'

# 计算机网络概述
net_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '计算机网络',
    KnowledgePoint.section == '计算机网络概述',
).first()
if net_kp:
    bad_kp_ids[net_kp.id] = '计算机网络概述 (计网)'

# 寻址方式
addr_kp = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == '计算机组成原理',
    KnowledgePoint.section == '寻址方式',
).first()
if addr_kp:
    bad_kp_ids[addr_kp.id] = '寻址方式 (计组)'

for kp_id, label in bad_kp_ids.items():
    r = recommend_wangdao_for_knowledge_point(db, kp_id, limit=5)
    items = r['items']
    print(f'【{label}】')
    for it in items[:5]:
        fs = it.get('final_score', 0)
        kp_name = it.get('knowledge_point', '')
        print(f'  score={fs:.2f} kp=[{kp_name}]')
    print()

db.close()
