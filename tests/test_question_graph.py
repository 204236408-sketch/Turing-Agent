# tests/test_question_graph.py
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
# 修复：正确导入generate_questions
from agents.question_graph import get_question_graph, set_db, generate_questions
from agents.graph_state import QuestionState
from database import SessionLocal
from main import app
from models import Question, QuestionGenerationSession, KnowledgeMastery, User
from utils.response import success

client = TestClient(app)

# 全局测试用户ID
TEST_USER_ID = 1
TEST_SUBJECT = "操作系统"
TEST_KP = "页面置换算法"
TEST_DIFF = "中等"
TEST_QTYPE = "选择题"
TEST_COUNT = 3

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def mock_llm_json():
    """模拟LLM正常返回标准题目JSON"""
    return {
        "questions": [
            {
                "question_text": "3个页框LRU，访问序列1,2,3,1,4,2,5缺页次数？",
                "options": ["A.4次", "B.5次", "C.6次", "D.7次"],
                "standard_answer": "C",
                "score": 2,
                "explanation": "命中更新LRU顺序，共6次缺页",
                "easy_mistakes": "忽略命中后更新顺序，算成5次",
                "hints": ["先初始化3个页框", "命中页面刷新最近使用"],
                "recommend_reason": "薄弱点强化，针对页面置换算法高频错题",
                "video_link": "https://www.bilibili.com/video/BV1maJJ6DE2Z"
            }
        ]
    }

def test_question_graph_workflow_normal(db_session: Session, mock_llm_json):
    """测试完整出题链路：正常LLM生成流程"""
    set_db(db_session)
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_llm_json
        mock_res.error = ""
        mock_chat.return_value = mock_res

        # 纯位置顺序传参，无任何 key=
        result = generate_questions(
            db_session,
            TEST_USER_ID,
            "薄弱点强化",
            TEST_SUBJECT,
            TEST_KP,
            TEST_DIFF,
            TEST_QTYPE,
            TEST_COUNT
        )
        # 校验逻辑不变
        assert result["session_id"] is not None
        assert len(result["questions"]) > 0
        assert result["llm_used"] is True
        assert result["llm_error"] == ""
        assert len(result["agent_steps"]) > 0
        session = db_session.query(QuestionGenerationSession).filter(
            QuestionGenerationSession.id == result["session_id"]
        ).first()
        assert session is not None
        assert session.subject == TEST_SUBJECT
        qs = db_session.query(Question).filter(Question.session_id == session.id).all()
        assert len(qs) >= 1

def test_question_graph_llm_timeout_fallback(db_session: Session):
    """测试LLM超时，自动降级本地模板题目"""
    set_db(db_session)
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = False
        mock_res.error = "timed out after 60s"
        mock_chat.return_value = mock_res

        result = generate_questions(
            db=db_session,
            user_id=TEST_USER_ID,
            mode="自由选择",
            subject=TEST_SUBJECT,
            knowledge_point=TEST_KP,
            difficulty=TEST_DIFF,
            question_type=TEST_QTYPE,
            count=TEST_COUNT
        )
        assert result["llm_used"] is False
        assert "timed out" in result["llm_error"]
        assert len(result["questions"]) == TEST_COUNT
        session_id = result["session_id"]
        qs = db_session.query(Question).filter(Question.session_id == session_id).all()
        for q in qs:
            assert q.source == "agent_fallback"

def test_question_graph_validate_mismatch_fallback(db_session: Session):
    """测试LLM生成题目与知识点不匹配，触发降级"""
    set_db(db_session)
    wrong_json = {
        "questions": [
            {
                "question_text": "二叉树前序遍历特点",
                "options": ["A.根左右", "B.左根右", "C.左右根", "D.根右左"],
                "standard_answer": "A",
                "explanation": "",
                "hints": ["记住遍历顺序"]
            }
        ]
    }
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = wrong_json
        mock_res.error = ""
        mock_chat.return_value = mock_res

        result = generate_questions(
            db=db_session,
            user_id=TEST_USER_ID,
            mode="薄弱点强化",
            subject=TEST_SUBJECT,
            knowledge_point=TEST_KP,
            difficulty=TEST_DIFF,
            question_type=TEST_QTYPE,
            count=TEST_COUNT
        )
        assert result["llm_used"] is False
        assert "知识点不匹配" in result["llm_error"]
        qs = db_session.query(Question).filter(Question.session_id == result["session_id"]).all()
        for q in qs:
            assert TEST_KP in q.question_text

def test_question_graph_fill_essay_comprehensive(db_session: Session):
    """测试填空题/简答题/综合题生成逻辑"""
    set_db(db_session)
    # 填空题
    res_fill = generate_questions(
        db=db_session,
        user_id=TEST_USER_ID,
        mode="自由选择",
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        difficulty="简单",
        question_type="填空题",
        count=2
    )
    assert len(res_fill["questions"]) == 2
    for q in res_fill["questions"]:
        assert "options" not in q or len(q["options"]) == 0

    # 简答题
    res_essay = generate_questions(
        db=db_session,
        user_id=TEST_USER_ID,
        mode="自由选择",
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        difficulty="较难",
        question_type="简答题",
        count=1
    )
    assert len(res_essay["questions"]) == 1

    # 综合题
    res_comp = generate_questions(
        db=db_session,
        user_id=TEST_USER_ID,
        mode="薄弱点强化",
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        difficulty="困难",
        question_type="综合题",
        count=1
    )
    assert len(res_comp["questions"][0]["sub_questions"]) > 0

def test_question_graph_agent_steps_complete(db_session: Session, mock_llm_json):
    """校验Graph完整节点链路全部执行"""
    set_db(db_session)
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_llm_json
        mock_res.error = ""
        mock_chat.return_value = mock_res

        result = generate_questions(
            db=db_session,
            user_id=TEST_USER_ID,
            mode="薄弱点强化",
            subject=TEST_SUBJECT,
            knowledge_point=TEST_KP,
            difficulty=TEST_DIFF,
            question_type=TEST_QTYPE,
            count=1
        )
        step_names = [s["name"] for s in result["agent_steps"]]
        expect_nodes = [
            "analyze_user_state",
            "select_target",
            "retrieve_question_context",
            "generate_questions",
            "validate_questions",
            "save_questions"
        ]
        for node in expect_nodes:
            assert node in step_names

def test_api_generate_question_normal():
    """接口：手动出题 /api/questions/generate 正常流程"""
    payload = {
        "mode": "自由选择",
        "subject": TEST_SUBJECT,
        "knowledge_point": TEST_KP,
        "difficulty": TEST_DIFF,
        "question_type": TEST_QTYPE,
        "count": 2
    }
    # 模拟登录鉴权
    resp = client.post("/api/questions/generate", json=payload, headers={"Authorization": "Bearer test_token"})
    # 不校验真实业务数据，仅校验返回结构
    assert resp.status_code in (200, 401)
    data = resp.json()
    if resp.status_code == 200:
        assert "data" in data
        assert "session_id" in data["data"]
        assert "questions" in data["data"]

def test_api_generate_smart_question():
    """接口：智能推荐出题 /api/questions/generate-smart"""
    payload = {
        "recommend_mode": "薄弱点强化",
        "count": 2
    }
    resp = client.post("/api/questions/generate-smart", json=payload, headers={"Authorization": "Bearer test_token"})
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        assert "recommendation" in resp.json()["data"]

def test_api_question_session_detail():
    """接口：获取出题批次详情 /api/questions/session/{session_id}"""
    resp = client.get("/api/questions/session/1", headers={"Authorization": "Bearer test_token"})
    assert resp.status_code in (200, 404, 401)

def test_api_question_detail():
    """接口：题目详情 /api/questions/detail/{question_id}"""
    resp = client.get("/api/questions/detail/1")
    assert resp.status_code in (200, 404)

def test_api_question_hints():
    """接口：题目提示 /api/questions/{id}/hints"""
    resp = client.get("/api/questions/1/hints")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert "hints" in resp.json()["data"]

def test_api_question_videos():
    """接口：题目配套视频 /api/questions/{id}/videos"""
    resp = client.get("/api/questions/1/videos")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert "items" in resp.json()["data"]

def test_api_question_mastery_feedback():
    """接口：单题掌握度标记 /api/questions/{id}/mastery"""
    payload = {
        "status": "不会",
        "mistake_id": None
    }
    resp = client.post("/api/questions/1/mastery", json=payload, headers={"Authorization": "Bearer test_token"})
    assert resp.status_code in (200, 401, 404)

def test_api_question_mastery_global():
    """接口：通用掌握度标记 /api/questions/mastery"""
    payload = {
        "subject": TEST_SUBJECT,
        "knowledge_point": TEST_KP,
        "status": "掌握",
        "question_id": 1
    }
    resp = client.post("/api/questions/mastery", json=payload, headers={"Authorization": "Bearer test_token"})
    assert resp.status_code in (200, 401)

def test_api_question_interaction_empty():
    """接口：交互记录空实现 /api/questions/{id}/interaction"""
    resp = client.post("/api/questions/1/interaction")
    assert resp.status_code == 200
    assert resp.json()["data"]["logged"] is True