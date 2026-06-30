import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for path in (str(ROOT), str(BACKEND)):
    if path not in sys.path:
        sys.path.insert(0, path)

if "bs4" not in sys.modules:
    mock_bs4 = MagicMock()
    mock_bs4.BeautifulSoup = MagicMock()
    sys.modules["bs4"] = mock_bs4


@pytest.fixture(scope="function")
def client():
    from fastapi.testclient import TestClient
    from backend.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def anon_client(client):
    return client


@pytest.fixture(scope="function")
def auth_client(client):
    from p5_helpers import authed_client

    return authed_client(client)


@pytest.fixture(scope="function")
def auth_headers(client):
    from p5_helpers import demo_auth_headers

    return demo_auth_headers(client)


@pytest.fixture(scope="function")
def db_session():
    from database import SessionLocal, init_database

    init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
