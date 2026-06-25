import pytest
import uuid
from test_smoke import client
from database import SessionLocal
from models import User

@pytest.fixture(scope="function")
def auth_headers():
    random_email = f"test_{uuid.uuid4()}@test.com"
    register_resp = client.post("/api/auth/register", json={
        "email": random_email,
        "username": "testuser",
        "password": "12345678"
    })
    login_resp = client.post("/api/auth/login", json={
        "account": random_email,
        "password": "12345678"
    })
    token = login_resp.json()["token"]
    yield {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    db.query(User).filter(User.email == random_email).delete()
    db.commit()
    db.close()