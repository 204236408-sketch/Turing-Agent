"""
视频爬虫脚本

用法：
  python scripts/crawl_videos.py                        # 爬所有知识点
  python scripts/crawl_videos.py --subject 操作系统       # 爬指定科目
  python scripts/crawl_videos.py --subject 操作系统 --kp 页面置换算法  # 爬指定知识点
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("crawl_videos")

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"


def main():
    parser = argparse.ArgumentParser(description="408 视频爬虫")
    parser.add_argument("--subject", type=str, default="", help="科目（可选）")
    parser.add_argument("--kp", type=str, default="", help="知识点（可选）")
    args = parser.parse_args()

    sys.path.insert(0, ".")

    from database import SessionLocal, init_database
    from services.video_crawler_service import crawl_for_point, crawl_all_points

    init_database()

    with SessionLocal() as db:
        if args.subject and args.kp:
            logger.info("爬取 %s/%s 的视频...", args.subject, args.kp)
            saved = crawl_for_point(db, args.subject, args.kp)
            logger.info("新增 %d 个视频", len(saved))
            for v in saved:
                logger.info("  [%.2f] %s - %s", v.get("score", 0), v["title"], v["url"])
            if saved:
                count = append_seed_videos(saved)
                logger.info("已写入 %d 条新爬取视频到 %s", count, SEED_PATH)
        elif args.subject:
            from models import KnowledgePoint
            points = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.subject == args.subject, KnowledgePoint.is_deleted == False)
                .distinct(KnowledgePoint.subject, KnowledgePoint.name)
                .all()
            )
            seen = set()
            total = 0
            all_saved = []
            for kp in points:
                key = (kp.subject, kp.name)
                if key in seen:
                    continue
                seen.add(key)
                saved = crawl_for_point(db, kp.subject, kp.name)
                total += len(saved)
                if saved:
                    all_saved.extend(saved)
                logger.info("%s/%s: 新增 %d 个视频", kp.subject, kp.name, len(saved))
                time.sleep(1)
            logger.info("总计新增 %d 个视频", total)
            if all_saved:
                count = append_seed_videos(all_saved)
                logger.info("已写入 %d 条新爬取视频到 %s", count, SEED_PATH)
        else:
            logger.info("爬取所有知识点的视频...")
            result = crawl_all_points(db)
            logger.info("总计: %d 个知识点, 新增 %d 个视频, 跳过 %d 个, 强制抓取 %d 个",
                        result["total_points"], result["total_new_videos"], result["total_skipped"], result["total_forced_crawl"])
            if result.get("results"):
                all_saved = []
                for saved_list in result["results"].values():
                    all_saved.extend(saved_list)
                if all_saved:
                    count = append_seed_videos(all_saved)
                    logger.info("已写入 %d 条新爬取视频到 %s", count, SEED_PATH)

        db.commit()

    logger.info("完成。")


def append_seed_videos(new_videos: list[dict]) -> int:
    try:
        if SEED_PATH.exists():
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
        else:
            entries = []
    except (json.JSONDecodeError, FileNotFoundError):
        entries = []

    existing_urls = {entry.get("url") for entry in entries if entry.get("url")}
    added = 0
    for video in new_videos:
        url = (video.get("url") or "").strip()
        if not url or url in existing_urls:
            continue
        entries.append({
            "subject": video.get("subject", ""),
            "knowledge_point": video.get("knowledge_point", ""),
            "title": video.get("title", ""),
            "platform": video.get("platform", "Bilibili"),
            "url": url,
            "cover_url": video.get("cover_url", ""),
            "duration": video.get("duration", ""),
            "author": video.get("author", ""),
            "quality_score": int(video.get("quality_score") or 0),
            "reason": video.get("reason", ""),
        })
        existing_urls.add(url)
        added += 1

    if added > 0:
        SEED_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return added


if __name__ == "__main__":
    main()
