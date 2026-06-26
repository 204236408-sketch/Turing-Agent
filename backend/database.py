from contextlib import contextmanager
<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import DateTime, create_engine, inspect, text
from sqlalchemy.schema import CreateTable
=======
from sqlalchemy import create_engine
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings


engine_kwargs = {"pool_pre_ping": True}
if settings.active_database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.active_database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database() -> None:
    import models  # noqa: F401

<<<<<<< HEAD
    Base.metadata.create_all(bind=engine)
    _ensure_compatibility_columns()


def _ensure_compatibility_columns() -> None:
    """Keep existing SQLite DB files aligned with the SQLAlchemy models."""
    if not settings.active_database_url.startswith("sqlite"):
        return
    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                connection.execute(CreateTable(table))

        inspector = inspect(connection)
        for table in Base.metadata.sorted_tables:
            table_name = table.name
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column in table.columns:
                if column.primary_key or column.name in existing:
                    continue
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {_sqlite_column_definition(column)}"))
        _normalize_sqlite_datetime_values(connection)


def _sqlite_column_definition(column) -> str:
    definition = column.type.compile(dialect=engine.dialect)
    if column.default is None or not column.default.is_scalar:
        return definition

    value = column.default.arg
    if isinstance(value, bool):
        rendered = "1" if value else "0"
    elif isinstance(value, (int, float)):
        rendered = str(value)
    elif isinstance(value, (list, dict)):
        rendered = repr("[]")
    else:
        rendered = repr(str(value))
    return f"{definition} DEFAULT {rendered}"


def _normalize_sqlite_datetime_values(connection) -> None:
    replacement = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            if not isinstance(column.type, DateTime):
                continue
            connection.execute(
                text(f"UPDATE {table.name} SET {column.name} = :replacement WHERE {column.name} = 'CURRENT_TIMESTAMP'"),
                {"replacement": replacement},
            )
=======
    from services.migration_service import check_migration_state, run_migrations

    if settings.auto_migrate_on_startup:
        run_migrations()
        return

    state = check_migration_state()
    if state["pending"]:
        pending = ", ".join(item["version"] for item in state["pending"])
        raise RuntimeError(f"Database migrations are pending: {pending}. Run backend/scripts/migrate_db.py first.")
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
