"""
逐个 KP 调用推荐 API，把完整 Top 5 列出来让人眼看是否对应。
"""
from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.video_service import recommend_wangdao_for_knowledge_point

LOG = open("c:/Users/Sophia/Desktop/turing/backend/_all_kp_full.txt", "w", encoding="utf-8", buffering=1)
def log(s=""):
    LOG.write(s + "\n")

db = SessionLocal()

# 加载所有 wangdao 视频，按 subject 索引，方便看 candidate 池
all_wd = {}
for v in db.query(VideoResource).filter(
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
).all():
    all_wd.setdefault(v.subject, []).append((v.knowledge_point, v.title, v.id))

kps = db.query(KnowledgePoint).filter(
    KnowledgePoint.is_deleted == False,
    KnowledgePoint.section.isnot(None),
    KnowledgePoint.section != "",
).order_by(KnowledgePoint.subject, KnowledgePoint.section, KnowledgePoint.name).all()

log(f"=== 全部 {len(kps)} 个 KP 完整推荐结果 ===\n")

for kp in kps:
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=5)
    items = result['items']
    log(f"----------")
    log(f"[{kp.subject}] section={kp.section!r}  kp_name={kp.name!r}  (id={kp.id})")
    if not items:
        log(f"  (空)")
    else:
        for i, it in enumerate(items, 1):
            log(f"  #{i} score={it.get('final_score', 0):.2f}  v_kp=[{it.get('knowledge_point','')}]  v_title=[{it.get('title','')[:60]}]")
    # 列出 subject 下所有 wangdao 视频，方便对照
    pool = all_wd.get(kp.subject, [])
    log(f"  (subject池: {len(pool)} 部)  关键词命中候选 >50 分:")
    for vkp, vtitle, vid in pool:
        log(f"      id={vid} v_kp=[{vkp}]")
    log("")

LOG.close()
print(f"DONE. See _all_kp_full.txt. Total {len(kps)} KPs.")
