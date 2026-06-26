import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from datetime import datetime

# 业务导入
from database import get_db
from main import app
from models import AnswerRecord, ForumPost, KnowledgeMastery, KnowledgePoint, Mistake, User, UserMemory
from services.mastery_service import get_or_create_mastery, recalculate_mastery, synchronize_user_mastery, apply_manual_feedback

# 全局常量
TEST_USER_ID = 1
SUBJECT_OS = "操作系统"
KP_PAGE_REPLACE = "页面置换算法"
TEST_AUTH_HEADER = {"Authorization": "Bearer test-jwt-token"}
client = TestClient(app)

# ------------------------------
# 数据库Fixture：每次用例独立事务，执行完毕强制回滚，隔离脏数据
# ------------------------------
@pytest.fixture
def db_session() -> Session:
    db = next(get_db())
    yield db
    db.rollback()
    db.expire_all()

@pytest.fixture
def base_knowledge_point(db_session: Session):
    """修复：补充content、common_mistakes、keywords三个必填字段"""
    kp = KnowledgePoint(
        subject=SUBJECT_OS,
        name=KP_PAGE_REPLACE,
        content="页面置换算法：OPT、FIFO、LRU、Clock算法对比",
        common_mistakes="混淆四种置换算法适用场景、忽略缺页中断代价",
        keywords="页面置换,FIFO,LRU,OPT,Clock,缺页中断",
        is_high_frequency=True
    )
    db_session.add(kp)
    db_session.commit()
    return kp

# ------------------------------
# 单元测试1：get_or_create_mastery 自动新建/复用知识点掌握记录
# ------------------------------
def test_mastery_create_or_reuse(db_session: Session):
    m1 = get_or_create_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m1.id is not None
    assert m1.user_id == TEST_USER_ID
    m2 = get_or_create_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m2.id == m1.id

# ------------------------------
# 单元测试2：5种掌握状态完整判定规则 + 优先级校验（薄弱点 > 不会 > 不熟 > 掌握 > 未学）
# ------------------------------
def test_mastery_status_priority_rule(db_session: Session):
    # 全局清空当前用户所有业务数据，彻底消除跨用例残留
    db_session.query(AnswerRecord).filter(AnswerRecord.user_id == TEST_USER_ID).delete()
    db_session.query(Mistake).filter(Mistake.user_id == TEST_USER_ID).delete()
    db_session.query(UserMemory).filter(UserMemory.user_id == TEST_USER_ID).delete()
    db_session.commit()
    db_session.rollback()

    # 场景1：无任何行为数据 → 未学（先执行空场景，无前置数据污染）
    m_empty = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m_empty.final_status == "未学"

    # 清空事务，隔离下一个场景
    db_session.rollback()

    # 场景2：连续答错3次 → 薄弱点（最高优先级）
    for _ in range(3):
        ar = AnswerRecord(
            user_id=TEST_USER_ID,
            subject=SUBJECT_OS,
            knowledge_point=KP_PAGE_REPLACE,
            question_id=1,
            is_correct=False,
            create_time=datetime.utcnow()
        )
        db_session.add(ar)
    db_session.commit()
    m_weak = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m_weak.final_status == "薄弱点"
    assert m_weak.continuous_wrong_count == 3
    assert m_weak.weak_score >= 10

    db_session.rollback()

    # 场景3：正确率<50%，连续错2次 → 不会
    ar1 = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=False)
    ar2 = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=False)
    db_session.add_all([ar1, ar2])
    db_session.commit()
    m_unknown = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m_unknown.final_status == "不会"
    total = m_unknown.total_answer_count
    correct = m_unknown.correct_count
    correct_rate = correct / total if total else 0
    assert correct_rate < 0.5
    assert m_unknown.continuous_wrong_count == 2

    db_session.rollback()

    # 场景4：答题2次，1对1错，正确率50% → 不熟
    ar_ok = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=True)
    ar_err = AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=False)
    db_session.add_all([ar_ok, ar_err])
    db_session.commit()
    m_unfamiliar = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m_unfamiliar.final_status == "不熟"
    total = m_unfamiliar.total_answer_count
    correct = m_unfamiliar.correct_count
    correct_rate = correct / total if total else 0
    assert 0.5 <= correct_rate < 0.8

    db_session.rollback()

    # 场景5：答题≥3次，正确率≥80%，错≤1，无薄弱记忆 → 掌握
    ars = [
        AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=True),
        AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=True),
        AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=True),
        AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=False),
    ]
    db_session.add_all(ars)
    db_session.commit()
    m_mastered = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m_mastered.final_status == "掌握"
    assert m_mastered.total_answer_count >= 3
    total = m_mastered.total_answer_count
    correct = m_mastered.correct_count
    correct_rate = correct / total if total else 0
    assert correct_rate >= 0.8
    assert m_mastered.wrong_count <= 1

# ------------------------------
# 单元测试3：weak_score 完整加权计算逻辑校验
# ------------------------------
def test_weak_score_calculate_weight(db_session: Session):
    # 前置清空残留数据
    db_session.query(AnswerRecord).filter(AnswerRecord.user_id == TEST_USER_ID).delete()
    db_session.query(Mistake).filter(Mistake.user_id == TEST_USER_ID).delete()
    db_session.commit()
    db_session.rollback()

    # 构造答题记录，补全question_id
    for _ in range(4):
        db_session.add(AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=False))
    db_session.add(AnswerRecord(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1, is_correct=True))
    db_session.commit()
    # OCR错题
    for _ in range(2):
        db_session.add(Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, input_type="ocr", error_type="概念理解错误", question_id=1))
    db_session.commit()
    # 论坛提问：修复补充category、title两个必填字段
    for _ in range(3):
        db_session.add(ForumPost(
            user_id=TEST_USER_ID,
            subject=SUBJECT_OS,
            knowledge_point=KP_PAGE_REPLACE,
            status="normal",
            category="408操作系统",
            title="页面置换算法OPT与FIFO区别咨询",
            content="混淆两种置换算法的缺页率表现，求区分方法"
        ))
    db_session.commit()

    m = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m.wrong_count == 4
    assert m.correct_count == 1
    assert m.ocr_mistake_count == 2
    assert m.forum_count == 3
    assert m.weak_score >= 4*3 + 2*3 + 3 - 1
    assert m.final_status == "薄弱点"

# ------------------------------
# 单元测试4：手动标记掌握状态 apply_manual_feedback 流转校验
# ------------------------------
def test_manual_mark_mastery_flow(db_session: Session):
    db_session.rollback()
    mk = Mistake(
        user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, question_id=1,
        error_type="概念混淆", mastery_status="未标记", status="active"
    )
    db_session.add(mk)
    db_session.commit()

    m1 = apply_manual_feedback(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE, "不会", mistake_id=mk.id)
    assert m1.user_mark_status == "不会"
    db_session.refresh(mk)
    assert mk.mastery_status == "不会"

    m2 = apply_manual_feedback(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE, "不熟", mistake_id=mk.id)
    assert m2.user_mark_status == "不熟"
    db_session.refresh(mk)
    assert mk.mastery_status == "不熟"

    m3 = apply_manual_feedback(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE, "掌握", mistake_id=mk.id)
    assert m3.user_mark_status == "掌握"
    db_session.refresh(mk)
    assert mk.mastery_status == "掌握"

# ------------------------------
# 单元测试5：synchronize_user_mastery 批量同步全知识点掌握度
# ------------------------------
def test_sync_all_knowledge_mastery(db_session: Session, base_knowledge_point):
    points_list = [(base_knowledge_point.subject, base_knowledge_point.name)]
    sync_result = synchronize_user_mastery(db_session, TEST_USER_ID, points_list)
    assert len(sync_result) == 1
    item = sync_result[0]
    assert item.subject == SUBJECT_OS
    assert item.knowledge_point == KP_PAGE_REPLACE
    assert item.final_status == "未学"

# ------------------------------
# 接口测试：/api/mastery 全接口链路校验（修复patch路由导入：mastery → mastery_router）
# ------------------------------
def test_mastery_api_full_cycle(db_session: Session, base_knowledge_point):
    # 修复：原routers.mastery 改为 routers.mastery_router，匹配后端真实路由文件名
    with patch("routers.mastery_router.get_current_user") as mock_auth:
        mock_user = User(id=TEST_USER_ID, email="test@test.com", username="test", nickname="test")
        mock_auth.return_value = mock_user

        resp_list = client.get("/api/mastery/list", headers=TEST_AUTH_HEADER)
        assert resp_list.status_code == 200
        list_data = resp_list.json()["data"]
        assert len(list_data["items"]) >= 1

        resp_recalc = client.post(
            "/api/mastery/recalculate",
            params={"subject": SUBJECT_OS, "knowledge_point": KP_PAGE_REPLACE},
            headers=TEST_AUTH_HEADER
        )
        assert resp_recalc.status_code == 200
        recalc_item = resp_recalc.json()["data"]["item"]
        assert recalc_item["knowledge_point"] == KP_PAGE_REPLACE

        resp_detail = client.get(
            "/api/mastery/detail",
            params={"subject": SUBJECT_OS, "knowledge_point": KP_PAGE_REPLACE},
            headers=TEST_AUTH_HEADER
        )
        assert resp_detail.status_code == 200
        assert resp_detail.json()["data"]["item"] is not None

        resp_summary = client.get("/api/mastery/summary", headers=TEST_AUTH_HEADER)
        assert resp_summary.status_code == 200
        summary = resp_summary.json()["data"]["summary"]
        assert set(summary.keys()) == {"未学", "掌握", "不熟", "不会", "薄弱点"}

# ------------------------------
# 边界场景测试：多错因重复、OCR错题、长期薄弱记忆提升weak_score
# ------------------------------
def test_mastery_edge_weak_scenario(db_session: Session):
    # 1. 先清空当前用户所有Mistake，消除跨用例数据残留
    db_session.query(Mistake).filter(Mistake.user_id == TEST_USER_ID).delete()
    db_session.commit()
    db_session.rollback()

    # 2. 新建2条错题，仅1条OCR类型
    db_session.add(Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, error_type="概念理解错误", input_type="ocr", question_id=1))
    db_session.add(Mistake(user_id=TEST_USER_ID, subject=SUBJECT_OS, knowledge_point=KP_PAGE_REPLACE, error_type="概念理解错误", input_type="system", question_id=1))
    # UserMemory补充完整content
    db_session.add(UserMemory(
        user_id=TEST_USER_ID,
        subject=SUBJECT_OS,
        knowledge_point=KP_PAGE_REPLACE,
        memory_type="weak_point",
        status="active",
        content="页面置换算法混淆FIFO与OPT，属于长期薄弱点"
    ))
    db_session.commit()

    m = recalculate_mastery(db_session, TEST_USER_ID, SUBJECT_OS, KP_PAGE_REPLACE)
    assert m.final_status == "薄弱点"
    assert m.weak_score > 6
    assert m.ocr_mistake_count >= 1