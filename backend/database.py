from contextlib import contextmanager
from sqlalchemy import create_engine
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

    from services.migration_service import check_migration_state, run_migrations

    if settings.auto_migrate_on_startup:
        run_migrations()
        return

    state = check_migration_state()
    if state["pending"]:
        pending = ", ".join(item["version"] for item in state["pending"])
        raise RuntimeError(f"Database migrations are pending: {pending}. Run backend/scripts/migrate_db.py first.")
