from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from config import PROJECT_DIR
from database import Base, engine


MIGRATIONS_DIR = PROJECT_DIR / "database" / "migrations"
MIGRATION_TABLE = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    checksum: str


def discover_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[Migration]:
    files = sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())
    migrations: list[Migration] = []
    for path in files:
        content = path.read_bytes()
        migrations.append(
            Migration(
                version=path.stem.split("_", 1)[0],
                name=path.name,
                path=path,
                checksum=hashlib.sha256(content).hexdigest(),
            )
        )
    return migrations


def applied_migrations(db_engine: Engine = engine) -> dict[str, dict]:
    inspector = inspect(db_engine)
    if MIGRATION_TABLE not in inspector.get_table_names():
        return {}
    with db_engine.connect() as connection:
        rows = connection.execute(
            text(f"SELECT version, name, checksum, applied_at FROM {MIGRATION_TABLE}")
        ).mappings()
        return {str(row["version"]): dict(row) for row in rows}


def check_migration_state(db_engine: Engine = engine) -> dict:
    migrations = discover_migrations()
    applied = applied_migrations(db_engine)
    pending = [
        {"version": migration.version, "name": migration.name, "checksum": migration.checksum}
        for migration in migrations
        if migration.version not in applied
    ]
    drift = [
        {
            "version": migration.version,
            "name": migration.name,
            "applied_checksum": applied[migration.version]["checksum"],
            "current_checksum": migration.checksum,
        }
        for migration in migrations
        if migration.version in applied and applied[migration.version]["checksum"] != migration.checksum
    ]
    return {
        "migration_table": MIGRATION_TABLE,
        "applied_count": len(applied),
        "pending": pending,
        "drift": drift,
    }


def run_migrations(db_engine: Engine = engine) -> dict:
    import models  # noqa: F401

    _ensure_migration_table(db_engine)
    applied = applied_migrations(db_engine)
    executed: list[dict] = []

    for migration in discover_migrations():
        if migration.version in applied:
            if applied[migration.version]["checksum"] != migration.checksum:
                raise RuntimeError(f"Migration checksum changed after apply: {migration.name}")
            continue

        _apply_migration(db_engine, migration)
        _record_migration(db_engine, migration)
        executed.append({"version": migration.version, "name": migration.name})

    return {"executed": executed, "state": check_migration_state(db_engine)}


def _ensure_migration_table(db_engine: Engine) -> None:
    with db_engine.begin() as connection:
        if db_engine.dialect.name == "sqlite":
            connection.exec_driver_sql(
                f"""
                CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
        else:
            connection.exec_driver_sql(
                f"""
                CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                    version VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at DATETIME NOT NULL
                )
                """
            )


def _apply_migration(db_engine: Engine, migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8-sig")
    if _is_schema_source_migration(sql):
        Base.metadata.create_all(bind=db_engine)
        return

    statements = list(_split_sql_statements(sql))
    if not statements:
        return
    with db_engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def _record_migration(db_engine: Engine, migration: Migration) -> None:
    with db_engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO {MIGRATION_TABLE} (version, name, checksum, applied_at)
                VALUES (:version, :name, :checksum, :applied_at)
                """
            ),
            {
                "version": migration.version,
                "name": migration.name,
                "checksum": migration.checksum,
                "applied_at": datetime.utcnow().isoformat(sep=" ", timespec="seconds"),
            },
        )


def _is_schema_source_migration(sql: str) -> bool:
    lines = [line.strip().lower() for line in sql.splitlines() if line.strip()]
    return any(line.startswith("source ") and "schema.sql" in line for line in lines)


def _split_sql_statements(sql: str) -> Iterable[str]:
    buffer: list[str] = []
    for raw_line in sql.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--") or line.lower().startswith("source "):
            continue
        buffer.append(raw_line)
        if line.endswith(";"):
            statement = "\n".join(buffer).strip().rstrip(";").strip()
            buffer.clear()
            if statement:
                yield statement
    tail = "\n".join(buffer).strip()
    if tail:
        yield tail
