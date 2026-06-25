import sys
from pathlib import Path
from uuid import uuid4
root_path = Path(__file__).parent.parent
backend_path = root_path / "backend"
sys.path.append(str(root_path))
sys.path.append(str(backend_path))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app

@pytest.fixture(scope="session")
def client():
    c = TestClient(app)
    yield c

@pytest.fixture(scope="session")
def auth_client(client):
    uname = f"test_{uuid4()}"
    reg_resp = client.post("/api/auth/register", json={"username": uname, "password": "123456"})
    login_resp = client.post("/api/auth/login", json={"username": uname, "password": "123456"})
    login_data = login_resp.json()
    print("完整登录返回：", login_data)
    data_part = login_data["data"]
    print("data内部字段：", list(data_part.keys()))

    # 兼容两种常见key
    if "access_token" in data_part:
        token = data_part["access_token"]
    elif "token" in data_part:
        token = data_part["token"]
    else:
        raise Exception(f"data里无token，所有key：{list(data_part.keys())}")

    client.headers["Authorization"] = f"Bearer {token}"
    return client
@pytest.fixture()
def mock_chroma_fail():
    with patch("backend.services.chroma_service.get_client") as mock_get:
        mock_get.side_effect = Exception("Chroma disconnect")
        yield

@pytest.fixture()
def mock_llm_fail():
    mock_llm = MagicMock()
    mock_llm.chat.side_effect = Exception("LLM api error")
    with patch("backend.agents.qa_agent.get_llm", return_value=mock_llm):
        yield