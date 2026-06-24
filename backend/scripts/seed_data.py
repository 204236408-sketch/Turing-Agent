from database import SessionLocal, init_database
from services.seed_service import seed_all


if __name__ == "__main__":
    init_database()
    with SessionLocal() as db:
        seed_all(db)
    print("基础演示数据写入完成")
