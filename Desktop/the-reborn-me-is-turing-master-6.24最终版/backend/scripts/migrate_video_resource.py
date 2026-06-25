"""One-time migration: add new columns to video_resource table."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "turing408.db"
if not db_path.exists():
    print("Database not found, skipping migration")
    exit(0)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute("PRAGMA table_info(video_resource)")
existing = {row[1] for row in cur.fetchall()}

migrations = [
    ("quality_score", "INTEGER DEFAULT 0"),
    ("author", "VARCHAR DEFAULT ''"),
    ("crawl_source", "VARCHAR DEFAULT 'seed'"),
]

for col_name, col_type in migrations:
    if col_name not in existing:
        cur.execute(f"ALTER TABLE video_resource ADD COLUMN {col_name} {col_type}")
        print(f"  Added: {col_name}")

conn.commit()
conn.close()
print("Migration complete")
