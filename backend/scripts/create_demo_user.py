from database import SessionLocal, init_database
from services.seed_service import seed_demo_user


if __name__ == "__main__":
    init_database()
    with SessionLocal() as db:
        user = seed_demo_user(db)
        db.commit()
    print(f"演示账号已创建：{user.email} / 123456")
