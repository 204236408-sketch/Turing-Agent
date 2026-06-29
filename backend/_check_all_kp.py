"""
全面检测：遍历所有 KP，调用 recommend_wangdao_for_knowledge_point，
人工核对"视频标题/KP"是否与"当前知识点主题"匹配。
"""
import sys
from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.video_service import recommend_wangdao_for_knowledge_point, _wangdao_match_score, _split_kp_tokens

LOG = open("c:/Users/Sophia/Desktop/turing/backend/_all_kp.txt", "w", encoding="utf-8", buffering=1)

def log(s=""):
    LOG.write(s + "\n")

db = SessionLocal()

kps = db.query(KnowledgePoint).filter(
    KnowledgePoint.is_deleted == False,
    KnowledgePoint.section.isnot(None),
    KnowledgePoint.section != "",
).order_by(KnowledgePoint.subject, KnowledgePoint.name, KnowledgePoint.section).all()

all_wd_by_subject = {}
for v in db.query(VideoResource).filter(
    VideoResource.crawl_source == "crawl_wangdao",
    VideoResource.is_deleted == False,
).all():
    all_wd_by_subject.setdefault(v.subject, []).append(v)

log(f"共 {len(kps)} 个 KP（按 section）\n")
log("=" * 80)

mismatches = []
empty_returns = []

for kp in kps:
    result = recommend_wangdao_for_knowledge_point(db, kp.id, limit=8)
    items = result['items']
    if not items:
        empty_returns.append(kp)
        continue

    wd_videos = all_wd_by_subject.get(kp.subject, [])
    expected = []
    for v in wd_videos:
        s = _wangdao_match_score(v, kp.name, kp.section, kp.subject)
        if s >= 60:
            expected.append((s, v.id, v.knowledge_point, v.title))
    expected.sort(key=lambda x: -x[0])

    returned_ids = {it['id'] for it in items}
    missing_strong = [e for e in expected if e[0] >= 65 and e[1] not in returned_ids]

    top1 = items[0]
    top1_kp = top1.get('knowledge_point', '')
    top1_score = top1.get('final_score', 0)

    sec_tokens = _split_kp_tokens(kp.section, exclude={kp.subject})
    # 判定相关性：sec_tokens / 同义词 / 去"的"后 / 前缀匹配
    from services.video_service import WANGDAO_SECTION_SYNONYMS, _strip_generic_suffix
    sec_norm = _strip_generic_suffix(kp.section).replace("的", "")
    top1_norm = _strip_generic_suffix(top1_kp).replace("的", "")
    is_top1_relevant = (
        any(t in top1_kp for t in sec_tokens if len(t) >= 1)  # 单字 token（如"栈"）也算
        or any(t in top1_kp for t in WANGDAO_SECTION_SYNONYMS.get(kp.section, []))  # 同义词
        or any(t in top1_kp for t in WANGDAO_SECTION_SYNONYMS.get(kp.name, []))
        or (sec_norm and sec_norm in top1_norm)  # 去"的"匹配
        or (top1_norm and top1_norm in sec_norm)
    )

    status = "[OK]" if is_top1_relevant else "[BAD]"
    log(f"[{kp.subject}] {kp.section!r} (kp_name={kp.name!r})")
    log(f"  {status} Top1: score={top1_score:.2f} kp=[{top1_kp}]")
    if len(items) > 1:
        for it in items[1:]:
            log(f"     #{it.get('keyword_match_score', 0):.2f} kp=[{it.get('knowledge_point', '')}]")

    if not is_top1_relevant or missing_strong:
        mismatches.append({
            'kp_id': kp.id,
            'subject': kp.subject,
            'section': kp.section,
            'name': kp.name,
            'top1_kp': top1_kp,
            'top1_score': top1_score,
            'missing_strong': missing_strong,
        })
        if missing_strong:
            log(f"  ⚠ 漏掉的高分匹配:")
            for s, vid, vkp, vtitle in missing_strong[:3]:
                log(f"     score={s} id={vid} kp=[{vkp}] title=[{vtitle[:50]}]")
    log("")

log("=" * 80)
log(f"\n总结：")
log(f"  总 KP 数: {len(kps)}")
log(f"  Top1 不相关: {sum(1 for m in mismatches if not any(t in m['top1_kp'] for t in _split_kp_tokens(m['section'], exclude={m['subject']}) if len(t) >= 2))}")
log(f"  漏掉高分匹配: {sum(1 for m in mismatches if m['missing_strong'])}")
log(f"  完全空结果: {len(empty_returns)}")
if empty_returns:
    log(f"\n  空结果的 KP:")
    for kp in empty_returns[:10]:
        log(f"    - [{kp.subject}] {kp.section!r} (name={kp.name!r})")

LOG.close()
print(f"DONE. See _all_kp.txt. Total {len(kps)} KPs, {len(mismatches)} issues.")
