"""
视频爬虫脚本

用法：
  python scripts/crawl_videos.py                        # 爬所有知识点
  python scripts/crawl_videos.py --subject 操作系统       # 爬指定科目
  python scripts/crawl_videos.py --subject 操作系统 --kp 页面置换算法  # 爬指定知识点
"""
import argparse
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("crawl_videos")


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
            for kp in points:
                key = (kp.subject, kp.name)
                if key in seen:
                    continue
                seen.add(key)
                saved = crawl_for_point(db, kp.subject, kp.name)
                total += len(saved)
                logger.info("%s/%s: 新增 %d 个视频", kp.subject, kp.name, len(saved))
                time.sleep(1)
            logger.info("总计新增 %d 个视频", total)
        else:
            logger.info("爬取所有知识点的视频...")
            result = crawl_all_points(db)
            logger.info("总计: %d 个知识点, 新增 %d 个视频, 跳过 %d 个",
                        result["total_points"], result["total_new_videos"], result["total_skipped"])

        db.commit()

    logger.info("完成。")


if __name__ == "__main__":
    main()
