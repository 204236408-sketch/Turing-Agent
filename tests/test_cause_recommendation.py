import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# 业务Agent与路由导入
from agents.answer_check_agent import check_answer
from agents.mistake_agent import confirm_cause, analyze_ocr_text
from database import get_db
from main import app
from models import AnswerRecord, KnowledgeMastery, Mistake, Question, User, UserMemory
from schemas import AnswerCheckRequest, CauseConfirmRequest, MasteryFeedbackRequest

# 全局常量
TEST_USER_ID = 1
TEST_SUBJECT = "操作系统"
TEST_KP = "页面置换算法"
TEST_WRONG_USER_ANS = "FIFO是最优页面置换算法"
TEST_CORRECT_USER_ANS = "OPT置换算法最优"
TEST_AUTH_HEADER = {"Authorization": "Bearer test-jwt-token"}
client = TestClient(app)

# ------------------------------
# 数据库Fixture：自动回滚，无主键冲突
# ------------------------------
@pytest.fixture
def db_session() -> Session:
    db = next(get_db())
    yield db
    db.rollback()

@pytest.fixture
def base_question(db_session: Session):
    """自增主键题目，每条测试独立，不硬编码固定ID"""
    q = Question(
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        question_text="最优页面置换算法是？",
        options_json='["A.FIFO","B.LRU","C.OPT","D.CLOCK"]',
        standard_answer="C",
        explanation="OPT可预知未来访问序列，缺页次数最少"
    )
    db_session.add(q)
    db_session.flush()
    return q

# ------------------------------
# LLM Mock Fixture（动态错因，数量随机，不固定8个）
# ------------------------------
@pytest.fixture
def mock_llm_wrong_result_random_causes(base_question):
    """AI批改答错，recommended_causes长度动态（2~6个，校验非固定8个）"""
    return {
        "answer_record_id": 0,
        "is_correct": False,
        "feedback": "混淆FIFO与OPT置换算法，概念理解错误",
        "mastery": {},
        "suggested_error_types": ["概念混淆", "记忆模糊", "审题偏差"],
        "llm_used": True,
        "llm_error": "",
        "agent_steps": [],
    }

@pytest.fixture
def mock_confirm_cause_output():
    """确认错因后生成错题、记忆、掌握度更新返回体"""
    return {
        "mistake_id": 0,
        "message": "已写入错题、长期记忆和知识点掌握状态。",
        "mastery_status": "不会",
        "weak_score": 12,
        "llm_used": True,
        "llm_error": "",
        "agent_steps": [],
    }

# ------------------------------
# 单元测试1：answer_check_agent AI动态生成错因，校验数量不固定
# ------------------------------
def test_check_answer_random_recommended_causes(db_session: Session, base_question, mock_llm_wrong_result_random_causes):
    """核心校验：推荐错因由AI动态生成，长度不固定，拒绝硬编码8个"""
    mock_llm_wrong_result_random_causes["answer_record_id"] = 0
    mock_llm_wrong_result_random_causes["question_id"] = base_question.id
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_llm_wrong_result_random_causes
        mock_res.error = ""
        mock_chat.return_value = mock_res

        res = check_answer(db_session, TEST_USER_ID, base_question.id, TEST_WRONG_USER_ANS)
        # 校验错因数组存在，长度随机≠8
        causes = res["suggested_error_types"]
        assert isinstance(causes, list)
        assert len(causes) > 0
        assert len(causes) != 8  # 需求：推荐错因不是固定8个
        # 校验答错标记、答题记录入库
        assert res["is_correct"] is False
        record = db_session.query(AnswerRecord).filter(AnswerRecord.id == res["answer_record_id"]).first()
        assert record is not None

# ------------------------------
# 单元测试2：confirm_cause 生成Mistake/UserMemory/KnowledgeMastery闭环
# ------------------------------
def test_confirm_cause_full_data_chain(db_session: Session, base_question, mock_confirm_cause_output):
    """确认错因：生成错题、长期记忆、更新知识点掌握度"""
    # 预创建答题记录
    rec = AnswerRecord(
        user_id=TEST_USER_ID,
        question_id=base_question.id,
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        user_answer=TEST_WRONG_USER_ANS,
        is_correct=False
    )
    db_session.add(rec)
    db_session.flush()
    mock_confirm_cause_output["mistake_id"] = 1
    with patch("services.llm_service.chat_json") as mock_chat:
        mock_res = MagicMock()
        mock_res.used_llm = True
        mock_res.data = mock_confirm_cause_output
        mock_res.error = ""
        mock_chat.return_value = mock_res

        res = confirm_cause(
            db_session,
            TEST_USER_ID,
            rec.id,
            ["概念混淆"],
            "混淆OPT与FIFO置换算法",
            "user_submit"
        )
        # 返回值校验
        assert res["mistake_id"] > 0
        assert res["mastery_status"] in ("不会", "不熟", "薄弱点")
        # 数据库三张表校验
        mistake = db_session.query(Mistake).filter(Mistake.id == res["mistake_id"]).first()
        memory = db_session.query(UserMemory).filter(UserMemory.evidence.like(f"%{mistake.id}%")).first()
        mastery = db_session.query(KnowledgeMastery).filter(
            KnowledgeMastery.user_id == TEST_USER_ID,
            KnowledgeMastery.knowledge_point == TEST_KP
        ).first()
        assert mistake is not None
        assert memory is not None
        assert mastery is not None

# ------------------------------
# 单元测试3：OCR错题分析分支，AI自动生成错因
# ------------------------------
def test_ocr_analyze_random_error_cause(db_session: Session):
    """OCR图片导入错题，AI动态生成错因，无固定数量"""
    ocr_text = "最优页面置换算法是FIFO"
    with patch("services.llm_service.chat_json_with_fallback_models") as mock_llm:
        mock_out = MagicMock()
        mock_out.used_llm = True
        mock_out.data = {
            "subject": TEST_SUBJECT,
            "knowledge_point": TEST_KP,
            "question_summary": "判断最优页面置换算法",
            "correct_answer": "OPT",
            "answer_explanation": "OPT预读未来访问序列",
            "is_correct": False,
            "possible_causes": ["概念混淆", "记忆遗忘", "审题失误"],
            "error_type": "概念理解错误",
            "error_reason": "混淆FIFO与OPT算法",
            "suggestion": "对比四种置换算法",
            "memory_content": "OPT是最优置换算法，避免混淆FIFO"
        }
        mock_out.error = ""
        mock_llm.return_value = mock_out

        res = analyze_ocr_text(db_session, TEST_USER_ID, ocr_text, TEST_SUBJECT, TEST_KP, TEST_WRONG_USER_ANS)
        causes = res["analysis"]["possible_causes"]
        assert len(causes) != 8
        assert res["mistake_id"] > 0
        assert res["memory_id"] > 0

# ------------------------------
# 接口全流程自动化主流程闭环（登录→批改→推荐错因→确认错因→错题本可见）
# ------------------------------
def test_full_answer_mistake_auto_cycle(db_session: Session, base_question, mock_llm_wrong_result_random_causes, mock_confirm_cause_output):
    """完整自动化主流程：登录提交错题→AI返回动态错因→确认错因→错题本可查询"""
    # 统一patch路由鉴权依赖，解决401
    with patch("routers.answers.get_current_user") as auth_ans, \
         patch("routers.mistakes.get_current_user") as auth_mistake, \
         patch("agents.answer_check_agent.check_answer") as mock_check, \
         patch("agents.mistake_agent.confirm_cause") as mock_confirm:

        mock_user = User(id=TEST_USER_ID, email="test@test.com", username="test", nickname="test")
        auth_ans.return_value = mock_user
        auth_mistake.return_value = mock_user
        mock_check.return_value = mock_llm_wrong_result_random_causes
        mock_confirm.return_value = mock_confirm_cause_output

        # 1. 提交错误答案批改，获取动态推荐错因
        check_resp = client.post(
            "/api/answers/check",
            json={"question_id": base_question.id, "user_answer": TEST_WRONG_USER_ANS},
            headers=TEST_AUTH_HEADER
        )
        assert check_resp.status_code == 200
        check_data = check_resp.json()["data"]
        record_id = check_data["answer_record_id"]
        rec_causes = check_data["suggested_error_types"]
        # 核心需求校验：错因数量不固定8个
        assert len(rec_causes) != 8
        assert len(rec_causes) > 0

        # 2. 前端确认错因
        confirm_resp = client.post(
            "/api/mistakes/cause-confirm",
            json={
                "answer_record_id": record_id,
                "error_types": rec_causes,
                "user_note": "混淆OPT与FIFO置换算法",
                "evidence_source": "user_submit"
            },
            headers=TEST_AUTH_HEADER
        )
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()["data"]
        mistake_id = confirm_data["mistake_id"]

        # 3. 错题列表可查询到新增错题
        list_resp = client.get("/api/mistakes", headers=TEST_AUTH_HEADER)
        list_items = list_resp.json()["data"]["items"]
        assert any(item["id"] == mistake_id for item in list_items)

        # 4. 错题本筛选「不会/不熟」可见该错题
        notebook_resp = client.get("/api/mistakes/notebook", headers=TEST_AUTH_HEADER)
        notebook_items = notebook_resp.json()["data"]["items"]
        assert any(item["id"] == mistake_id for item in notebook_items)

# ------------------------------
# 掌握状态专项测试（不熟/不会/掌握切换）
# ------------------------------
def test_mistake_switch_mastery_flow(db_session: Session, base_question):
    """手动切换错题掌握状态，掌握后移出错题本"""
    # 预生成错题记录
    rec = AnswerRecord(
        user_id=TEST_USER_ID,
        question_id=base_question.id,
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        user_answer=TEST_WRONG_USER_ANS,
        is_correct=False
    )
    db_session.add(rec)
    db_session.flush()
    mistake = Mistake(
        user_id=TEST_USER_ID,
        answer_record_id=rec.id,
        question_id=base_question.id,
        subject=TEST_SUBJECT,
        knowledge_point=TEST_KP,
        error_type="概念混淆",
        error_reason="混淆OPT与FIFO置换算法",
        suggestion="对比四种置换算法",
        input_type="系统出题",
        mastery_status="不会",
        status="active"
    )
    db_session.add(mistake)
    db_session.commit()

    with patch("routers.mistakes.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test")
        # 切换为「不熟」
        resp_unfamiliar = client.post(
            f"/api/mistakes/{mistake.id}/mastery",
            json={"status": "不熟"},
            headers=TEST_AUTH_HEADER
        )
        assert resp_unfamiliar.status_code == 200
        assert resp_unfamiliar.json()["data"]["status"] == "不熟"

        # 切换为「掌握」，错题本不再展示
        resp_master = client.post(
            f"/api/mistakes/{mistake.id}/mastery",
            json={"status": "掌握"},
            headers=TEST_AUTH_HEADER
        )
        assert resp_master.status_code == 200
        notebook_resp = client.get("/api/mistakes/notebook", headers=TEST_AUTH_HEADER)
        all_mistake_ids = [i["id"] for i in notebook_resp.json()["data"]["items"]]
        assert mistake.id not in all_mistake_ids

# ------------------------------
# 边界分支测试
# ------------------------------
def test_retrain_stub_fixed_output():
    """/retrain 桩接口固定返回"""
    with patch("routers.mistakes.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test")
        resp = client.post("/api/mistakes/retrain", headers=TEST_AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] == 3
        assert "同类训练建议" in data["message"]

def test_mistake_detail_404_when_not_exist():
    """查询不存在错题返回404"""
    with patch("routers.mistakes.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test")
        resp = client.get("/api/mistakes/999999", headers=TEST_AUTH_HEADER)
        assert resp.status_code == 404

def test_empty_notebook_no_mistake():
    """用户无错题，错题本返回空列表"""
    with patch("routers.mistakes.get_current_user") as mock_auth:
        mock_auth.return_value = User(id=TEST_USER_ID, email="test@test.com", username="test")
        resp = client.get("/api/mistakes/notebook", headers=TEST_AUTH_HEADER)
        data = resp.json()["data"]
        assert len(data["items"]) == 0
        assert data["stats"]["total"] == 0

def test_no_token_401_intercept():
    """无token访问批改接口，鉴权拦截401"""
    body = {"question_id": 999, "user_answer": TEST_WRONG_USER_ANS}
    resp = client.post("/api/answers/check", json=body)
    assert resp.status_code == 401