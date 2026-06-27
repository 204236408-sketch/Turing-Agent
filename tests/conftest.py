import sys
from unittest.mock import MagicMock
from pathlib import Path
import pytest


# 1. 先清空所有models缓存
for mod in list(sys.modules.keys()):
    if mod == "models" or mod.startswith("backend.models"):
        del sys.modules[mod]

# mock bs4 解决爬虫依赖缺失
if "bs4" not in sys.modules:
    mock_bs = MagicMock()
    mock_bs.BeautifulSoup = MagicMock()
    sys.modules["bs4"] = mock_bs

# 路径配置
root_path = Path(__file__).parent.parent
backend_path = root_path / "backend"
sys.path.append(str(root_path))
sys.path.append(str(backend_path))

# 2. 关键：mock answer_graph 阻断顶层models导入
sys.modules["backend.agents.answer_graph"] = MagicMock()

# 客户端夹具：scope 改为 function，每个用例重建App，消除路由提前缓存
@pytest.fixture(scope="function")
def client():
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)

@pytest.fixture(scope="function")
def anon_client(client):
    return client

@pytest.fixture(scope="function")
def auth_client(client):
    from uuid import uuid4
    uname = f"test_{uuid4()}"
    client.post("/api/auth/register", json={"username": uname, "password": "123456"})
    login_resp = client.post("/api/auth/login", json={"username": uname, "password": "123456"})
    data = login_resp.json()["data"]
    token = data.get("access_token") or data.get("token")
    client.headers["Authorization"] = f"Bearer {token}"
    return client

# 数据库会话，自动回滚
@pytest.fixture(scope="function")
def db_session():
    from backend.database import SessionLocal, init_database
    init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# 自动剔除video_view_log不存在的source字段，解决sql报错
@pytest.fixture(scope="function", autouse=True)
def strip_source_field(db_session, monkeypatch):
    origin_add = db_session.add
    def patched_add(obj):
        from backend.models import VideoViewLog
        if isinstance(obj, VideoViewLog) and hasattr(obj, "source"):
            delattr(obj, "source")
        return origin_add(obj)
    monkeypatch.setattr(db_session, "add", patched_add)
    yield

# chroma 服务故障mock
@pytest.fixture()
def mock_chroma_fail():
    from unittest.mock import patch
    with patch("backend.services.chroma_service.get_client") as m:
        m.side_effect = Exception("Chroma disconnect")
        yield

# LLM 接口故障mock，补齐闭合
@pytest.fixture()
def mock_llm_fail():
    from unittest.mock import patch, MagicMock
    mock_llm = MagicMock()
    mock_llm.chat.side_effect = Exception("LLM api error")
    with patch("backend.agents.qa_agent.get_llm") as m:
        m.return_value = mock_llm
        yield