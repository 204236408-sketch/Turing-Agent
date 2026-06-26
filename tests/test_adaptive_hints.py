import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from database import get_db
from main import app
from models import KnowledgeMastery, User, Question, AnswerRecord
from services.mastery_service import recalculate_mastery

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
    with patch("routers.question_router.get_current_user") as mu:
        mu.return_value = User(id=TEST_USER_ID, username="test")
        yield mu

# 薄弱点：三层完整详细提示
def test_hint_layer_weak_point(db_session, mock_auth):
    # 全表清空，彻底消除历史脏数据
    db_session.query(AnswerRecord).delete()
    db_session.commit()

    for _ in range(3):
        db_session.add(AnswerRecord(
            user_id=TEST_USER_ID,
            subject=SUBJECT_OS,
            knowledge_point=KP_PAGE,
            question_id=1,
            is_correct=False
        ))
    db_session.commit()
    mastery = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    assert mastery.final_status == "薄弱点"

    mock_agent = MagicMock()
    mock_agent.gen_adaptive_hint.return_value = {
        "layer1": "页面置换算法基础概念",
        "layer2": "四大置换算法缺页差异",
        "layer3": "计算题完整分步推导"
    }
    # 匹配真实项目路径 backend.agents
    with patch("backend.agents.question_agent", mock_agent):
        resp = client.get(
            "/api/question/hint",
            params={"question_id": 1, "subject": SUBJECT_OS, "knowledge_point": KP_PAGE},
            headers=TEST_HEADER
        )
        assert resp.status_code == 200
        hint_data = resp.json()["data"]
        assert {"layer1", "layer2", "layer3"}.issubset(hint_data.keys())

# 不会：两层中等提示
def test_hint_layer_unknown(db_session, mock_auth):
    # 全表清空，彻底消除历史脏数据
    db_session.query(AnswerRecord).delete()
    db_session.commit()

    db_session.add(AnswerRecord(
        user_id=TEST_USER_ID,
        subject=SUBJECT_OS,
        knowledge_point=KP_PAGE,
        question_id=1,
        is_correct=False
    ))
    db_session.commit()
    mastery = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    assert mastery.final_status == "不会"

    mock_agent = MagicMock()
    mock_agent.gen_adaptive_hint.return_value = {"layer1": "基础定义", "layer2": "高频易错点"}
    with patch("backend.agents.question_agent", mock_agent):
        resp = client.get(
            "/api/question/hint",
            params={"question_id": 1, "subject": SUBJECT_OS, "knowledge_point": KP_PAGE},
            headers=TEST_HEADER
        )
        assert len(resp.json()["data"]) == 2

# 不熟：两层精简提示
def test_hint_layer_unfamiliar(db_session, mock_auth):
    # 全表清空，彻底消除历史脏数据
    db_session.query(AnswerRecord).delete()
    db_session.commit()

    ar1 = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=1, is_correct=True)
    ar2 = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=2, is_correct=False)
    db_session.add_all([ar1, ar2])
    db_session.commit()
    mastery = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    assert mastery.final_status == "不熟"

    mock_agent = MagicMock()
    mock_agent.gen_adaptive_hint.return_value = {"layer1": "解题入口", "layer2": "简化思路"}
    with patch("backend.agents.question_agent", mock_agent):
        resp = client.get(
            "/api/question/hint",
            params={"question_id": 1, "subject": SUBJECT_OS, "knowledge_point": KP_PAGE},
            headers=TEST_HEADER
        )
        assert len(resp.json()["data"]) == 2

# 掌握：仅单层极简提示
def test_hint_layer_mastered(db_session, mock_auth):
    # 全表清空，彻底消除历史脏数据
    db_session.query(AnswerRecord).delete()
    db_session.commit()

    ar_list = [
        AnswerRecord(
            user_id=TEST_USER_ID,
            subject=SUBJECT_OS,
            knowledge_point=KP_PAGE,
            question_id=i,
            is_correct=True
        )
        for i in range(3)
    ]
    db_session.add_all(ar_list)
    db_session.commit()
    mastery = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    assert mastery.final_status == "掌握"

    mock_agent = MagicMock()
    mock_agent.gen_adaptive_hint.return_value = {"layer1": "简短解题提示"}
    with patch("backend.agents.question_agent", mock_agent):
        resp = client.get(
            "/api/question/hint",
            params={"question_id": 1, "subject": SUBJECT_OS, "knowledge_point": KP_PAGE},
            headers=TEST_HEADER
        )
        assert len(resp.json()["data"]) == 1