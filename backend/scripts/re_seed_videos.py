"""Re-import seed videos from JSON into the database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from database import SessionLocal, init_database
from services.seed_service import seed_videos


def main():
    init_database()
    db = SessionLocal()

    # 清除旧种子（保留爬虫数据）
    db.execute(text("DELETE FROM video_resource WHERE crawl_source = 'seed'"))
    db.commit()

    seed_videos(db)
    db.commit()

    cnt = db.execute(text("SELECT COUNT(*) FROM video_resource")).scalar()
    print(f"Total videos in DB: {cnt}")

    rows = db.execute(
        text("SELECT subject, COUNT(*) FROM video_resource GROUP BY subject ORDER BY subject")
    ).fetchall()
    for s, c in rows:
        print(f"  {s}: {c}")

    real = db.execute(
        text("SELECT COUNT(*) FROM video_resource WHERE url LIKE '%/video/%'")
    ).scalar()
    print(f"Real Bilibili video URLs: {real}")


if __name__ == "__main__":
    main()
