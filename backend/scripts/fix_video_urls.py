import json
from pathlib import Path
from urllib.parse import quote

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"

with open(SEED_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Processing {len(data)} videos...")

fixed = 0
for item in data:
    url = item.get("url", "")
    kp = item.get("knowledge_point", "")
    subj = item.get("subject", "")
    title = item.get("title", "")
    if "search.bilibili.com" in url or "bilibili.com/video/av" in url or "bilibili.com/video/BV" in url:
        keyword = f"408考研 {subj} {kp} {title}"
        search_url = f"https://search.bilibili.com/all?keyword={quote(keyword)}"
        item["url"] = search_url
        fixed += 1

with open(SEED_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed {fixed} video URLs.")

import sys; sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
db.execute(text("DELETE FROM video_resource WHERE crawl_source = 'seed'"))
db.commit()
from services.seed_service import seed_videos
seed_videos(db)
db.commit()
cnt = db.execute(text("SELECT COUNT(*) FROM video_resource")).scalar()
by_subj = db.execute(text("SELECT subject, COUNT(*) FROM video_resource WHERE is_deleted=0 GROUP BY subject ORDER BY subject")).fetchall()
print(f"Re-imported. Total videos: {cnt}")
for row in by_subj:
    print(f"  {row[0]}: {row[1]}")
db.close()
