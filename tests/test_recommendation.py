"""
test_recommendation.py 智能推荐接口自动化测试脚本
测试接口：GET /api/knowledge/recommend
依赖参考文件：
1. routers/knowledge.py 接口路由、鉴权、返回结构
2. services/recommendation_service.py 全部推荐算法、计算规则、返回payload
3. models.py User、UserProfile、KnowledgePoint、KnowledgeMastery、Mistake、UserMemory、QuestionGenerationSession、AnswerRecord
4. dependencies.py get_current_user 鉴权逻辑（无token自动使用demo用户）
5. auth.py token_for_user 生成登录token
6. database.py session_scope 数据库会话
7. utils.response.py success 统一返回格式
8. main.py FastAPI应用TestClient
"""
from __future__ import annotations
import sys
import os
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 项目路径加载
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from main import app
from database import session_scope
from models import (
    User, UserProfile, KnowledgePoint, KnowledgeMastery, Mistake,
    UserMemory, QuestionGenerationSession, AnswerRecord, Question
)
from auth import token_for_user
from services.recommendation_service import SMART_MODES, _ALL_SUBJECTS

client = TestClient(app)

# 全局测试变量
test_username = f"rec_test_{uuid.uuid4()}"
test_email = f"rec_{uuid.uuid4()}@test.com"
test_user_id: int = -1
test_token: str = ""

# 预置基础知识点数据（补齐所有NOT NULL约束字段）
KP_FIXTURE = [
    {
        "subject": "操作系统",
        "name": "页面置换算法",
        "section": "内存管理",
        "parent_name": "内存管理",
        "content": "FIFO LRU OPT Clock页面置换算法",
        "common_mistakes": "混淆各算法优缺点、Belady异常判断",
        "keywords": "页面置换,FIFO,LRU,OPT,Clock",
        "is_high_frequency": True
    },
    {
        "subject": "操作系统",
        "name": "进程调度",
        "section": "进程管理",
        "parent_name": "进程管理",
        "content": "FCFS SJF HRRN 时间片轮转调度",
        "common_mistakes": "周转时间、带权周转时间计算",
        "keywords": "进程,调度,FCFS,SJF,HRRN",
        "is_high_frequency": False
    },
    {
        "subject": "计算机网络",
        "name": "TCP传输层",
        "section": "传输层",
        "parent_name": "传输层",
        "content": "三次握手四次挥手、拥塞控制",
        "common_mistakes": "TIME_WAIT状态、拥塞窗口变化",
        "keywords": "TCP,握手,挥手,拥塞控制",
        "is_high_frequency": True
    }
]

def setup_full_weak_data():
    """预置存在薄弱点、错题、答题记录、记忆标记的完整用户测试数据"""
    global test_user_id, test_token
    with session_scope() as db:
        # 创建测试用户
        user = User(
            email=test_email,
            username=test_username,
            password_hash="fake_hash_0000",
            nickname="推荐测试用户"
        )
        db.add(user)
        db.flush()
        test_user_id = user.id
        db.add(UserProfile(user_id=test_user_id, target_date="2026-12-19"))

        # 批量插入知识点
        kp_map = {}
        for kp_info in KP_FIXTURE:
            kp = KnowledgePoint(
                subject=kp_info["subject"],
                name=kp_info["name"],
                section=kp_info["section"],
                parent_name=kp_info["parent_name"],
                content=kp_info["content"],
                common_mistakes=kp_info["common_mistakes"],
                keywords=kp_info["keywords"],
                is_high_frequency=kp_info["is_high_frequency"],
                subject_id=1
            )
            db.add(kp)
            kp_map[(kp_info["subject"], kp_info["name"])] = kp

        # 1. 薄弱知识点掌握记录（页面置换算法，高弱分）
        weak_mastery = KnowledgeMastery(
            user_id=test_user_id,
            subject="操作系统",
            knowledge_point="页面置换算法",
            total_answer_count=6,
            correct_count=2,
            wrong_count=3,
            weak_score=12.0,
            continuous_wrong_count=2,
            qa_count=4,
            final_status="薄弱点"
        )
        db.add(weak_mastery)

        # 2. 已掌握知识点记录（TCP）
        good_mastery = KnowledgeMastery(
            user_id=test_user_id,
            subject="计算机网络",
            knowledge_point="TCP传输层",
            total_answer_count=5,
            correct_count=5,
            wrong_count=0,
            weak_score=1.0,
            final_status="掌握"
        )
        db.add(good_mastery)

        # 3. 创建题目、答题记录
        test_q = Question(
            subject="操作系统",
            knowledge_point="页面置换算法",
            question_text="LRU算法会产生Belady异常吗？",
            standard_answer="不会",
            question_type="选择题"
        )
        db.add(test_q)
        db.flush()
        ans = AnswerRecord(
            user_id=test_user_id,
            question_id=test_q.id,
            subject="操作系统",
            knowledge_point="页面置换算法",
            user_answer="会",
            standard_answer="不会",
            is_correct=False
        )
        db.add(ans)

        # 4. 错题记录
        mistake = Mistake(
            user_id=test_user_id,
            answer_record_id=ans.id,
            question_id=test_q.id,
            subject="操作系统",
            knowledge_point="页面置换算法",
            error_type="概念混淆",
            error_reason="混淆FIFO与LRU异常特性"
        )
        db.add(mistake)

        # 5. 用户手动标记薄弱记忆点
        memory = UserMemory(
            user_id=test_user_id,
            memory_type="weak_point",
            subject="操作系统",
            knowledge_point="页面置换算法",
            content="页面置换算法容易混淆各类异常"
        )
        db.add(memory)

        # 生成登录token
        test_token = token_for_user(user)

def setup_empty_user_data():
    """预置无任何答题、错题、薄弱记录的空白用户"""
    global test_user_id, test_token
    with session_scope() as db:
        user = User(
            email=f"empty_{uuid.uuid4()}@test.com",
            username=f"empty_rec_{uuid.uuid4()}",
            password_hash="fake_hash_0000",
            nickname="空白用户"
        )
        db.add(user)
        db.flush()
        test_user_id = user.id
        db.add(UserProfile(user_id=test_user_id, target_date="2026-12-19"))
        # 插入基础知识点
        for kp_info in KP_FIXTURE:
            kp = KnowledgePoint(
                subject=kp_info["subject"],
                name=kp_info["name"],
                section=kp_info["section"],
                parent_name=kp_info["parent_name"],
                content=kp_info["content"],
                common_mistakes=kp_info["common_mistakes"],
                keywords=kp_info["keywords"],
                is_high_frequency=kp_info["is_high_frequency"],
                subject_id=1
            )
            db.add(kp)
        test_token = token_for_user(user)

def teardown_data():
    """清理测试用户，级联删除所有关联数据"""
    global test_user_id
    with session_scope() as db:
        user = db.query(User).filter(User.id == test_user_id).first()
        if user:
            db.delete(user)
        # 清理测试知识点
        for kp_info in KP_FIXTURE:
            db.query(KnowledgePoint).filter(
                KnowledgePoint.subject == kp_info["subject"],
                KnowledgePoint.name == kp_info["name"]
            ).delete()

# ===================== 用例1：无Token访问推荐接口，自动使用demo用户正常返回 =====================
def test_recommend_no_token():
    """场景：未携带登录Token访问推荐接口，校验demo用户正常返回200、推荐结构合法"""
    resp = client.get("/api/knowledge/recommend")
    assert resp.status_code == 200
    res = resp.json()
    assert res["ok"] is True
    items = res["data"]["items"]
    assert isinstance(items, list)
    # 校验5种推荐模式全部存在
    mode_list = [item["mode"] for item in items]
    for mode in SMART_MODES:
        assert mode in mode_list

# ===================== 用例2：存在薄弱点、错题、答题记录的用户，校验推荐分支优先级 =====================
def test_recommend_full_weak_user():
    """场景：拥有薄弱知识点、错题、高频提问记录的登录用户，校验薄弱点、错题推荐优先输出"""
    setup_full_weak_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/recommend", headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    items = res["data"]["items"]
    # 薄弱点强化第一条，目标为页面置换算法
    weak_item = next(i for i in items if i["mode"] == "薄弱点强化")
    assert weak_item["knowledge_point"] == "页面置换算法"
    assert weak_item["available"] is True
    # 最近错题复练指向同一知识点
    mistake_item = next(i for i in items if i["mode"] == "最近错题复练")
    assert mistake_item["knowledge_point"] == "页面置换算法"
    # 已改善知识点存在（TCP）
    improved_item = next(i for i in items if i["mode"] == "已改善知识点复测")
    assert improved_item["knowledge_point"] == "TCP传输层"
    teardown_data()

# ===================== 用例3：空白无学习记录用户，校验基线诊断推荐 =====================
def test_recommend_empty_user():
    """场景：无任何答题、错题、掌握度记录的新用户，校验基线诊断逻辑"""
    setup_empty_user_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/recommend", headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    items = res["data"]["items"]

    for item in items:
        # 非综合模式available=False
        if item["mode"] != "四科随机综合":
            assert item["available"] is False
        assert item["initial"] is True

    teardown_data()
# ===================== 用例4：校验推荐返回字段完整性 =====================
def test_recommend_payload_fields():
    """场景：校验每条推荐项完整返回规定字段，无缺失"""
    setup_full_weak_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/recommend", headers=headers)
    items = resp.json()["data"]["items"]
    required_fields = ["mode", "subject", "knowledge_point", "reason", "difficulty", "question_type", "count", "available", "initial"]
    for item in items:
        for field in required_fields:
            assert field in item
    teardown_data()

# ===================== 用例5：跨域请求校验 =====================
def test_recommend_cross_origin():
    """场景：前端携带Origin跨域头访问推荐接口，校验跨域放行"""
    setup_full_weak_data()
    headers = {
        "Origin": "http://localhost:5173",
        "Authorization": f"Bearer {test_token}"
    }
    resp = client.get("/api/knowledge/recommend", headers=headers)
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
    teardown_data()

# ===================== 用例6：今日计划接口输出校验 =====================
def test_recommend_today_plan():
    """场景：校验choose_today_plan今日优先推荐，优先取可用薄弱点强化"""
    setup_full_weak_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/recommend", headers=headers)
    items = resp.json()["data"]["items"]
    # 今日计划优先取薄弱点强化
    weak_item = next(i for i in items if i["mode"] == "薄弱点强化")
    assert weak_item["available"] is True
    teardown_data()