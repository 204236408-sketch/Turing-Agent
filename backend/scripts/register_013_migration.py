"""一次性脚本：把 013_mastery_score 标记为已应用（字段已手动添加）。"""
import os
import sqlite3
from config import settings


def main() -> None:
    url = settings.active_database_url
    if not url.startswith("sqlite"):
        raise SystemExit("仅支持 sqlite")
    db_path = url.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, name TEXT NOT NULL, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)")
    # 计算 013 的 checksum 与 migration_service 一致
    import hashlib
    from pathlib import Path
    sql_path = Path(__file__).resolve().parents[2] / "database" / "migrations" / "013_mastery_score.sql"
    content = sql_path.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    cur.execute(
        "INSERT OR REPLACE INTO schema_migrations(version, name, checksum, applied_at) VALUES (?,?,?,datetime('now'))",
        ("013", "013_mastery_score.sql", checksum),
    )
    conn.commit()
    cur.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version")
    for row in cur.fetchall():
        print("migration:", row)
    conn.close()


if __name__ == "__main__":
    main()
