import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal
from models import KnowledgePoint

db = SessionLocal()
# 找"绪论"等高频 KP 看 content 长度变化
kps = db.query(KnowledgePoint).filter(
    KnowledgePoint.subject == "数据结构",
    KnowledgePoint.is_deleted == False,
).all()
print(f"共 {len(kps)} 个 KP")
print()
for kp in kps:
    content = kp.content or ""
    if "绪论" in kp.name or "基本概念" in kp.name or "三要素" in kp.name:
        print(f"=== {kp.name!r} ===")
        print(f"content 长度: {len(content)}")
        # 检查【核心概念】板块
        sections = content.split("【")
        for sec in sections:
            if "核心概念" in sec[:10]:
                body = sec.split("】", 1)[1] if "】" in sec else ""
                # 数核心概念板块的句子数
                import re
                sents = [s for s in re.split(r"(?<=[。！？!?])\s*", body) if s.strip()]
                print(f"  核心概念板块 句子数: {len(sents)}, 字符数: {len(body)}")
                # 检查重复句子
                seen = set()
                dup = 0
                for s in sents:
                    sk = s[:30]
                    if sk in seen:
                        dup += 1
                    seen.add(sk)
                print(f"  重复句子数: {dup}")
                # 取前 5 个句子
                for i, s in enumerate(sents[:6]):
                    print(f"    [{i}] {s[:80]}")
                break
        print()
db.close()
