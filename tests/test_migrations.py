from pathlib import Path
import sys

from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from services.migration_service import MIGRATION_TABLE, run_migrations  # noqa: E402


def test_migrations_are_idempotent_on_empty_sqlite():
    db_engine = create_engine("sqlite:///:memory:")

    first = run_migrations(db_engine)
    second = run_migrations(db_engine)

    assert first["executed"]
    assert second["executed"] == []
    tables = set(inspect(db_engine).get_table_names())
    assert MIGRATION_TABLE in tables
    assert "user" in tables
    assert "knowledge_point" in tables
