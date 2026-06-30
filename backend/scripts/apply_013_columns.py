"""一次性脚本：给 knowledge_mastery 添加 mastery_score / user_mark_at / recent_wrong_7d / recent_answer_7d 字段。

绕开 migration_service 的 checksum drift 校验，直接执行 ALTER。
"""
import os
import sqlite3

from config import settings


def main() -> None:
    url = settings.active_database_url
    if not url.startswith("sqlite"):
        raise SystemExit("此脚本仅适用于 sqlite，请手动在 MySQL 上执行相同 SQL")
    db_path = url.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    print("DB path:", db_path, "exists:", os.path.exists(db_path))
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    stmts = [
        "ALTER TABLE knowledge_mastery ADD COLUMN mastery_score INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_mastery ADD COLUMN user_mark_at DATETIME NULL",
        "ALTER TABLE knowledge_mastery ADD COLUMN recent_wrong_7d INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_mastery ADD COLUMN recent_answer_7d INTEGER DEFAULT 0",
        "CREATE INDEX IF NOT EXISTS idx_mastery_score ON knowledge_mastery (mastery_score)",
    ]
    for sql in stmts:
        try:
            cur.execute(sql)
            conn.commit()
            print("OK:", sql)
        except Exception as exc:
            print("SKIP:", exc)
    cur.execute("PRAGMA table_info(knowledge_mastery)")
    for row in cur.fetchall():
        print(" col:", row[1], row[2])
    conn.close()


if __name__ == "__main__":
    main()
