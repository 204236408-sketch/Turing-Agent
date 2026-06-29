"""
LLM 离线关键词批处理（直接跑版，避免 logging 缓冲问题）
"""
import sys
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("gen_keywords")

sys.path.insert(0, ".")

from database import SessionLocal
from models import KnowledgePoint, VideoResource
from services.keyword_extractor import (
    extract_kp_matching_keywords,
    extract_video_matching_keywords,
    _deserialize_kws,
)


def _already_has(s: str) -> bool:
    if not s:
        return False
    kws = _deserialize_kws(s)
    return len(kws) > 0


def process_one_kp(args):
    kp_id, subject, section, name, content, overwrite = args
    db = SessionLocal()
    try:
        kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
        if not kp:
            return (kp_id, None, "NOT_FOUND")
        if not overwrite and _already_has(kp.keywords):
            return (kp_id, _deserialize_kws(kp.keywords), "SKIP")
        kws = extract_kp_matching_keywords(
            subject=subject, section=section, name=name, content=content,
        )
        if kws:
            kp.keywords = json.dumps(kws, ensure_ascii=False)
            db.commit()
            return (kp_id, kws, "OK")
        return (kp_id, None, "EMPTY")
    except Exception as e:
        db.rollback()
        return (kp_id, None, f"ERR:{e!r}"[:50])
    finally:
        db.close()


def process_one_video(args):
    vid, subject, section, video_kp, title, description, overwrite = args
    db = SessionLocal()
    try:
        v = db.query(VideoResource).filter(VideoResource.id == vid).first()
        if not v:
            return (vid, None, "NOT_FOUND")
        if not overwrite and _already_has(v.keywords):
            return (vid, _deserialize_kws(v.keywords), "SKIP")
        kws = extract_video_matching_keywords(
            subject=subject, section=section, video_kp=video_kp,
            title=title, description=description,
        )
        if kws:
            v.keywords = json.dumps(kws, ensure_ascii=False)
            db.commit()
            return (vid, kws, "OK")
        return (vid, None, "EMPTY")
    except Exception as e:
        db.rollback()
        return (vid, None, f"ERR:{e!r}"[:50])
    finally:
        db.close()


def run_kp(workers: int, overwrite: bool):
    db = SessionLocal()
    kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
    db.close()
    log.info(f"待处理 KP: {len(kps)} 个")

    todo = [(kp.id, kp.subject, kp.section or "", kp.name or "", kp.content or "", overwrite) for kp in kps]
    if not todo:
        return

    stats = {"OK": 0, "EMPTY": 0, "ERR": 0, "SKIP": 0}
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(process_one_kp, t) for t in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            key = r[2].split(":")[0]
            stats[key] = stats.get(key, 0) + 1
            if i % 30 == 0 or i == len(todo):
                el = time.time() - start
                eta = el / i * (len(todo) - i)
                log.info(f"KP {i}/{len(todo)} stats={stats} eta={eta:.0f}s")
    log.info(f"KP 完成: {stats} 耗时 {time.time()-start:.0f}s")


def run_video(workers: int, overwrite: bool):
    db = SessionLocal()
    vs = db.query(VideoResource).filter(
        VideoResource.is_deleted == False,
        VideoResource.crawl_source == "crawl_wangdao",
    ).all()
    db.close()
    log.info(f"待处理视频: {len(vs)} 个")

    todo = [(v.id, v.subject, v.section or "", v.knowledge_point or "", v.title or "", v.description or "", overwrite) for v in vs]
    if not todo:
        return

    stats = {"OK": 0, "EMPTY": 0, "ERR": 0, "SKIP": 0}
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(process_one_video, t) for t in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            key = r[2].split(":")[0]
            stats[key] = stats.get(key, 0) + 1
            if i % 20 == 0 or i == len(todo):
                el = time.time() - start
                eta = el / i * (len(todo) - i)
                log.info(f"视频 {i}/{len(todo)} stats={stats} eta={eta:.0f}s")
    log.info(f"视频完成: {stats} 耗时 {time.time()-start:.0f}s")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--only-kp", action="store_true")
    p.add_argument("--only-video", action="store_true")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    if not args.only_video:
        log.info("=" * 60)
        log.info("开始处理 KP 关键词")
        log.info("=" * 60)
        run_kp(args.workers, args.overwrite)

    if not args.only_kp:
        log.info("=" * 60)
        log.info("开始处理视频关键词")
        log.info("=" * 60)
        run_video(args.workers, args.overwrite)
