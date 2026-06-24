from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
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

    Base.metadata.create_all(bind=engine)
    _ensure_compatibility_columns()


def _ensure_compatibility_columns() -> None:
    """Add columns introduced by the PDF-aligned data model to existing SQLite DBs."""
    if not settings.active_database_url.startswith("sqlite"):
        return
    additions = {
        "question_generation_session": {
            "recommend_mode": "VARCHAR(64) DEFAULT ''",
        },
        "knowledge_mastery": {
            "mastered_count": "INTEGER DEFAULT 0",
            "user_mark_status": "VARCHAR(32) DEFAULT ''",
            "continuous_wrong_count": "INTEGER DEFAULT 0",
            "last_answer_time": "DATETIME",
        },
        "question": {
            "variant_type": "VARCHAR(32) DEFAULT 'choice'",
            "sub_questions_json": "TEXT DEFAULT '[]'",
        },
        "mistake": {
            "mastery_status": "VARCHAR(32) DEFAULT ''",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"))
