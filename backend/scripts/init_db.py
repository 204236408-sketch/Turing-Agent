<<<<<<< HEAD
from database import init_database, SessionLocal
=======
from database import SessionLocal
from services.migration_service import run_migrations
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
from services.seed_service import seed_all


def main():
<<<<<<< HEAD
    init_database()
    with SessionLocal() as db:
        seed_all(db)
    print("数据库表和演示数据初始化完成")
=======
    result = run_migrations()
    with SessionLocal() as db:
        seed_all(db)
    print(f"Database migrations executed: {len(result['executed'])}")
    print("Database tables and demo data initialized")
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)


if __name__ == "__main__":
    main()
