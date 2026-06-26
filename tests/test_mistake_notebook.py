import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import datetime

from database import get_db
from main import app
from models import Mistake, KnowledgeMastery, AnswerRecord, User, UserMemory
from services.mastery_service import recalculate_mastery, apply_manual_feedback

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
    db.expire_all()

@pytest.fixture
def mock_auth():
    # 修复：routers.mistake → routers.mistake_router 匹配后端真实路由文件名
    with patch("routers.mistake_router.get_current_user") as mock_u:
        mock_u.return_value = User(id=TEST_USER_ID, username="test", email="test@test.com")
        yield mock_u

# 1. 手动标记「不会」进入不会题本
def test_manual_mark_unknown_in_notebook(db_session, mock_auth):
    mk = Mistake(
        user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE,
        question_id=1, error_type="概念错误", mastery_status="不会", status="active"
    )
    db_session.add(mk)
    db_session.commit()
    resp = client.get("/api/mistake/notebook", params={"filter_type": "不会"}, headers=TEST_HEADER)
    assert resp.status_code == 200
    data = resp.json()["data"]["items"]
    assert len(data) == 1
    assert data[0]["mastery_status"] == "不会"

# 2. 手动标记「不熟」进入熟题本
def test_manual_mark_unfamiliar_in_notebook(db_session, mock_auth):
    mk = Mistake(
        user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE,
        question_id=2, error_type="计算错误", mastery_status="不熟", status="active"
    )
    db_session.add(mk)
    db_session.commit()
    resp = client.get("/api/mistake/notebook", params={"filter_type": "不熟"}, headers=TEST_HEADER)
    assert len(resp.json()["data"]["items"]) == 1

# 3. 手动标记「掌握」自动从两类题本全部移出
def test_manual_mark_master_auto_remove(db_session, mock_auth):
    mk = Mistake(
        user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE,
        question_id=3, error_type="混淆算法", mastery_status="不会", status="active"
    )
    db_session.add(mk)
    db_session.commit()
    # 手动标记掌握
    apply_manual_feedback(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE, "掌握", mistake_id=mk.id)
    db_session.refresh(mk)
    assert mk.mastery_status == "掌握"
    # 不会/不熟题库均无数据
    resp_unknown = client.get("/api/mistake/notebook", params={"filter_type": "不会"}, headers=TEST_HEADER)
    resp_unfam = client.get("/api/mistake/notebook", params={"filter_type": "不熟"}, headers=TEST_HEADER)
    assert len(resp_unknown.json()["data"]["items"]) == 0
    assert len(resp_unfam.json()["data"]["items"]) == 0

# 4. 连续答对自动提升掌握状态，错题本自动移除
def test_continuous_correct_auto_upgrade_status(db_session, mock_auth):
    # 前置：创建不会错题
    mk = Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=4, mastery_status="不会", status="active")
    db_session.add(mk)
    # 连续3次答对
    for _ in range(3):
        db_session.add(AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=4, is_correct=True))
    db_session.commit()
    # 重算掌握度
    recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    db_session.refresh(mk)
    # 自动更新为掌握，题本无数据
    assert mk.mastery_status == "掌握"
    resp = client.get("/api/mistake/notebook", params={"filter_type": "不会"}, headers=TEST_HEADER)
    assert len(resp.json()["data"]["items"]) == 0

# 5. 薄弱点仅为知识点标签，不会进入不熟/不会题本
def test_weak_point_only_kp_tag_not_in_notebook(db_session, mock_auth):
    # 构造薄弱点条件：连续3次答错
    for _ in range(3):
        db_session.add(AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=5, is_correct=False))
    db_session.commit()
    mastery = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE)
    assert mastery.final_status == "薄弱点"
    # 新建错题，未手动标记，默认无状态，不会自动划入题本
    mk = Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE, question_id=5, error_type="缺页计算错误", status="active")
    db_session.add(mk)
    db_session.commit()
    resp_all = client.get("/api/mistake/notebook", params={"filter_type": "all"}, headers=TEST_HEADER)
    # 无手动标记状态，不展示在不熟/不会题本
    assert len(resp_all.json()["data"]["items"]) == 0