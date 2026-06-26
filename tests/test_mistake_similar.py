import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from database import get_db
from main import app
from models import Mistake, User
# 修正：如果后端文件名是 mistake_service.py 则保留，若为其他名称同步修改
# from services.mistake_service import ChromaService
from services.chroma_service import ChromaService

TEST_USER_ID = 1
SUBJECT_OS = "操作系统"
KP_PAGE = "页面置换算法"
TEST_HEADER = {"Authorization": "Bearer test-token"}
client = TestClient(app)

@pytest.fixture
def db_session():
    db = next(get_db())
    yield db
    db.rollback()

@pytest.fixture
def mock_auth():
    # 已修复路由patch路径 mistake → mistake_router
    with patch("routers.mistake_router.get_current_user") as mu:
        mu.return_value = User(id=TEST_USER_ID, username="test")
        yield mu

# 场景1：Chroma向量库正常启用，返回向量检索相似错题
def test_similar_chroma_enabled_normal_query(db_session, mock_auth):
    mock_chroma = MagicMock()
    mock_chroma.enabled = True
    mock_chroma.query.return_value = {
        "items": [{"id": "mistake_1001", "text": "FIFO算法缺页次数计算错误", "metadata": {"subject": SUBJECT_OS, "knowledge_point": KP_PAGE}}],
        "fallback": False
    }
    # 修复点：services.mistake_service 不存在，改为直接patch chroma_service，或修正为真实服务文件名
    with patch("services.chroma_service", mock_chroma):
        resp = client.get("/api/mistake/similar", params={"mistake_id": 1001}, headers=TEST_HEADER)
        assert resp.status_code == 200
        res_items = resp.json()["data"]["items"]
        assert len(res_items) == 1
        assert res_items[0]["knowledge_point"] == KP_PAGE

# 场景2：Chroma不可用，降级查询同知识点历史错题兜底
def test_similar_chroma_disabled_fallback_same_kp(db_session, mock_auth):
    mock_chroma = MagicMock()
    mock_chroma.enabled = False
    # 插入同知识点错题兜底数据
    db_session.add(Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=1002, error_type="OPT与LRU混淆"))
    db_session.commit()
    with patch("services.chroma_service", mock_chroma):
        resp = client.get("/api/mistake/similar", params={"mistake_id": 1002}, headers=TEST_HEADER)
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) >= 1

# 场景3：无任何相似错题，返回空数组
def test_similar_no_matching_data_return_empty(db_session, mock_auth):
    mock_chroma = MagicMock()
    mock_chroma.enabled = True
    mock_chroma.query.return_value = {"items": [], "fallback": False}
    with patch("services.chroma_service", mock_chroma):
        resp = client.get("/api/mistake/similar", params={"mistake_id": 9999}, headers=TEST_HEADER)
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0