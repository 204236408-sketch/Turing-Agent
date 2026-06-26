import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import datetime

# 全部补齐顶层包 backend
from backend.database import get_db
from backend.main import app
from backend.models import Question, QuestionInteractionLog, User
from backend.schemas import QuestionCollectReq

TEST_USER_ID = 1
TEST_HEADER = {"Authorization": "Bearer test-token"}
client = TestClient(app)

@pytest.fixture
def db_session():
    db = next(get_db())
    yield db
    db.rollback()

@pytest.fixture
def mock_auth():
    # 完整路由模块路径
    with patch("backend.routers.question_router.get_current_user") as mu:
        mu.return_value = User(id=TEST_USER_ID, username="test")
        yield mu

@pytest.fixture
def test_question(db_session):
    q = Question(
        subject="操作系统", knowledge_point="页面置换算法",
        title="LRU置换算法计算题", content="给定页序列求缺页次数",
        answer="缺页6次", difficulty="中等", question_type="计算题"
    )
    db_session.add(q)
    db_session.commit()
    return q

def test_collect_question_persist(db_session, mock_auth, test_question):
    req = QuestionCollectReq(question_id=test_question.id, is_favorite=True)
    resp = client.post("/api/question/favorite", json=req.model_dump(), headers=TEST_HEADER)
    assert resp.status_code == 200
    log = db_session.query(QuestionInteractionLog).filter(
        QuestionInteractionLog.user_id == TEST_USER_ID,
        QuestionInteractionLog.question_id == test_question.id
    ).first()
    assert log is not None
    assert log.is_favorite == True

def test_cancel_favorite(db_session, mock_auth, test_question):
    client.post("/api/question/favorite", json={"question_id": test_question.id, "is_favorite": True}, headers=TEST_HEADER)
    resp_cancel = client.post("/api/question/favorite", json={"question_id": test_question.id, "is_favorite": False}, headers=TEST_HEADER)
    assert resp_cancel.status_code == 200
    log = db_session.query(QuestionInteractionLog).filter(
        QuestionInteractionLog.user_id == TEST_USER_ID,
        QuestionInteractionLog.question_id == test_question.id
    ).first()
    assert log.is_favorite == False

def test_list_favorite_questions(db_session, mock_auth, test_question):
    client.post("/api/question/favorite", json={"question_id": test_question.id, "is_favorite": True}, headers=TEST_HEADER)
    resp_list = client.get("/api/question/favorite/list", headers=TEST_HEADER)
    assert resp_list.status_code == 200
    items = resp_list.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["question_id"] == test_question.id