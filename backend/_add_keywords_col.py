from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text("PRAGMA table_info(video_resource)")).fetchall()
    cols = [row[1] for row in r]
    print("video_resource cols:", cols)
    if "keywords" not in cols:
        conn.execute(text('ALTER TABLE video_resource ADD COLUMN keywords TEXT DEFAULT ""'))
        conn.commit()
        print("Added keywords column")
    else:
        print("keywords column already exists")
