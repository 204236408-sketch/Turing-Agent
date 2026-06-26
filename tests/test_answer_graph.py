import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from agents.answer_check_agent import check_answer
from database import get_db
from main import app
from models import AnswerRecord, Question, User
from schemas import AnswerCheckRequest

# 全局常量
TEST_USER_ID = 1
TEST_SUBJECT = "操作系统"
TEST_KP = "页面置换算法"
TEST_USER_ANSWER = "OPT置换算法是最优置换"
TEST_AUTH_HEADER = {"Authorization": "Bearer fake-test-token"}

client = TestClient(app)

# ------------------------------
# 数据库Fixture：每次测试自动回滚，所有写入全部作废，彻底解决主键冲突
# ------------------------------
@pytest.fixture
def db_session() -> Session:
    db = next(get_db())
    yield db
    # 测试结束全部回滚，不会持久化任何Question/AnswerRecord
    db.rollback()

@pytest.fixture
def mock_llm_correct() -> dict:
    """正常正确作答mock返回"""
    return {
        "question_id": 0,
        "knowledge_point": TEST_KP,
        "is_correct": True,
        "standard_answer": "OPT算法能获得最少缺页次数，是最优页面置换算法",
        "feedback": "回答正确，核心要点完整",
        "error_type": "",
        "suggestion": "",
        "record_id": 0
    }

@pytest.fixture
def mock_llm_wrong() -> dict:
    """错误作答mock返回，齐全error_type字段"""
    return {
        "question_id": 0,
        "knowledge_point": TEST_KP,
        "is_correct": False,
        "standard_answer": "OPT算法能获得最少缺页次数，是最优页面置换算法",
        "feedback": "回答错误，混淆了OPT与FIFO",
        "error_type": "概念理解错误",
        "suggestion": "区分四种置换算法的优缺点",
        "record_id": 0
    }

@pytest.fixture
def mock_llm_timeout() -> dict:
    """LLM超时兜底返回，is_correct=None"""
    return {
        "question_id": 0,
        "knowledge_point": TEST_KP,
        "is_correct": None,
        "standard_answer": "",
        "feedback": "AI服务暂时不可用，请稍后重试",
        "error_type": "服务超时",
        "suggestion": "",
        "record_id": 0
    }

# ------------------------------
# 单元测试：check_answer 业务函数（每个用例内部新建题目，回滚自动销毁）
# ------------------------------
def test_check_answer_agent_normal(db_session: Session, mock_llm_correct):
    # 新建临时题目，不自定义id，使用数据库自增主键，杜绝UNIQUE冲突
    q = Question(
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        question_text="哪个页面置换算法最优？",
        options_json='["A.FIFO","B.LRU","C.OPT","D.CLOCK"]',
        standard_answer="C",
        explanation="OPT预读未来访问，缺页最少"
    )
    db_session.add(q)
    db_session.flush()  # 拿到自增question_id，不提交
    q_id = q.id
    mock_llm_correct["question_id"] = q_id

    # mock LLM服务
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_llm_correct
        mock_res.error = ""
        mock_chat.return_value = mock_res

        # 纯位置传参，无关键字
        res = check_answer(db_session, TEST_USER_ID, q_id, TEST_USER_ANSWER)
        # 断言匹配mock返回True
        assert res["is_correct"] is True
        assert res["question_id"] == q_id
        record = db_session.query(AnswerRecord).filter(AnswerRecord.id == res["record_id"]).first()
        assert record is not None

def test_check_answer_agent_wrong_answer(db_session: Session, mock_llm_wrong):
    q = Question(
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        question_text="哪个页面置换算法最优？",
        options_json='["A.FIFO","B.LRU","C.OPT","D.CLOCK"]',
        standard_answer="C",
        explanation="OPT预读未来访问，缺页最少"
    )
    db_session.add(q)
    db_session.flush()
    q_id = q.id
    mock_llm_wrong["question_id"] = q_id

    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_llm_wrong
        mock_res.error = ""
        mock_chat.return_value = mock_res

        res = check_answer(db_session, TEST_USER_ID, q_id, "FIFO是最优置换")
        assert res["is_correct"] is False
        assert res["error_type"] == "概念理解错误"

def test_check_answer_agent_llm_timeout_fallback(db_session: Session, mock_llm_timeout):
    q = Question(
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        question_text="哪个页面置换算法最优？",
        options_json='["A.FIFO","B.LRU","C.OPT","D.CLOCK"]',
        standard_answer="C",
        explanation="OPT预读未来访问，缺页最少"
    )
    db_session.add(q)
    db_session.flush()
    q_id = q.id
    mock_llm_timeout["question_id"] = q_id

    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = False
        mock_res.error = "timed out after 60s"
        mock_res.data = mock_llm_timeout
        mock_chat.return_value = mock_res

        res = check_answer(db_session, TEST_USER_ID, q_id, TEST_USER_ANSWER)
        assert res["is_correct"] is None
        assert "AI服务暂时不可用" in res["feedback"]

# ------------------------------
# 接口测试：修正patch路径 routers.answers.get_current_user，解决401与AttributeError
# ------------------------------
def test_api_answer_check(mock_llm_correct):
    # 双patch：路由层鉴权依赖 + agent函数
    with patch("agents.answer_check_agent.check_answer") as mock_check, \
         patch("routers.answers.get_current_user") as mock_auth:
        mock_check.return_value = mock_llm_correct
        # 模拟登录用户，绕过JWT校验
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test", nickname="test")
        body = {"question_id": 999, "user_answer": TEST_USER_ANSWER}
        resp = client.post("/api/answers/check", json=body, headers=TEST_AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

def test_api_answer_history_empty():
    with patch("routers.answers.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test", nickname="test")
        resp = client.get("/api/answers/history", headers=TEST_AUTH_HEADER)
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

def test_api_answer_history_has_data(db_session: Session, mock_llm_correct):
    # 插入题目+答题记录
    q = Question(
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        question_text="哪个页面置换算法最优？",
        options_json='["A.FIFO","B.LRU","C.OPT","D.CLOCK"]',
        standard_answer="C",
        explanation="OPT预读未来访问，缺页最少"
    )
    db_session.add(q)
    db_session.flush()
    q_id = q.id
    rec = AnswerRecord(
        user_id=TEST_USER_ID,
        question_id=q_id,
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        user_answer=TEST_USER_ANSWER,
        is_correct=True,
        feedback=mock_llm_correct["feedback"]
    )
    db_session.add(rec)
    db_session.commit()

    with patch("routers.answers.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test", nickname="test")
        resp = client.get("/api/answers/history", headers=TEST_AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 1
        assert data["items"][0]["question_id"] == q_id

def test_api_answer_check_no_token():
    # 无token访问，预期401，修正断言
    body = {"question_id": 999, "user_answer": TEST_USER_ANSWER}
    resp = client.post("/api/answers/check", json=body)
    assert resp.status_code == 401