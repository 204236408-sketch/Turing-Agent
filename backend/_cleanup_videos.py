import sys; sys.path.insert(0, '.')
from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
total = db.execute(text("SELECT COUNT(*) FROM video_resource")).scalar()
seed_cnt = db.execute(text("SELECT COUNT(*) FROM video_resource WHERE crawl_source='seed'")).scalar()
old_cnt = db.execute(text("SELECT COUNT(*) FROM video_resource WHERE crawl_source!='seed' OR crawl_source IS NULL")).scalar()
print(f"Total: {total}, seed: {seed_cnt}, old/non-seed: {old_cnt}")
if old_cnt:
    db.execute(text("DELETE FROM video_resource WHERE crawl_source!='seed' OR crawl_source IS NULL"))
    db.commit()
    print("Deleted old non-seed video records")
total2 = db.execute(text("SELECT COUNT(*) FROM video_resource")).scalar()
print(f"After cleanup: {total2}")
rows = db.execute(text("SELECT id, subject, knowledge_point, substr(url,1,60) FROM video_resource LIMIT 5")).fetchall()
for r in rows:
    print(f"  id={r[0]} {r[1]}/{r[2]} | {r[3]}")
db.close()
