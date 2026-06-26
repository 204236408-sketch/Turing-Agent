from database import init_database, SessionLocal
from services.seed_service import seed_all


def main():
    init_database()
    with SessionLocal() as db:
        seed_all(db)
    print("数据库表和演示数据初始化完成")


if __name__ == "__main__":
    main()
