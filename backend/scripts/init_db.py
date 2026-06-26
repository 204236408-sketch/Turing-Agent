from database import SessionLocal
from services.migration_service import run_migrations
from services.seed_service import seed_all


def main():
    result = run_migrations()
    with SessionLocal() as db:
        seed_all(db)
    print(f"Database migrations executed: {len(result['executed'])}")
    print("Database tables and demo data initialized")


if __name__ == "__main__":
    main()
