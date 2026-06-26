from __future__ import annotations
import sys
import os

# 项目根路径导入
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, str(BASE_PATH))

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import session_scope
from models import User, UserProfile, KnowledgeMastery, AnswerRecord, Mistake, KnowledgePoint, UserMemory, Question

client = TestClient(app)

# 测试用户全局变量
test_email = f"test_home_{uuid.uuid4()}.test@408.com"
test_username = f"home_test_{uuid.uuid4()}"
test_uid = -1


# 场景1夹具：全新空白用户（补齐所有NOT NULL字段：content / common_mistakes / keywords）
def create_new_empty_user():
    global test_uid
    with session_scope() as db:
        user = User(
            email=test_email,
            username=test_username,
            password_hash="test_hash_0000"
        )
        db.add(user)
        db.flush()
        test_uid = user.id
        # 用户考研配置
        profile = UserProfile(user_id=test_uid, target_date="2026-12-19")
        db.add(profile)
        # 插入基础知识点：补齐全部三个必填文本字段
        kp = KnowledgePoint(
            subject="操作系统",
            name="内存管理",
            section="内存管理",
            content="内存管理包含分页、分段、虚拟内存、页面置换算法",
            common_mistakes="容易混淆各类页面置换算法的优缺点",
            keywords="分页,分段,虚拟内存,FIFO,LRU,OPT",
            is_high_frequency=True
        )
        db.add(kp)
        db.flush()


# 场景2夹具：有完整学习数据用户（补齐全部知识点必填字段+question_id）
def create_user_with_study_data():
    global test_uid
    with session_scope() as db:
        user = User(
            email=test_email,
            username=test_username,
            password_hash="test_hash_0000"
        )
        db.add(user)
        db.flush()
        test_uid = user.id
        profile = UserProfile(user_id=test_uid, target_date="2026-12-19")
        db.add(profile)
        # 薄弱知识点掌握记录
        weak_record = KnowledgeMastery(
            user_id=test_uid,
            subject="操作系统",
            knowledge_point="内存管理",
            final_status="薄弱点",
            total_answer_count=6,
            wrong_count=3,
            weak_score=12
        )
        db.add(weak_record)
        # 错题记录
        mistake = Mistake(
            user_id=test_uid,
            subject="操作系统",
            knowledge_point="内存管理",
            error_type="页面置换算法混淆",
            status="active"
        )
        db.add(mistake)
        # 创建测试题目，给答题记录关联question_id
        test_question = Question(
            subject="操作系统",
            knowledge_point="内存管理",
            question_text="页面置换算法有哪些？",
            standard_answer="OPT、FIFO、LRU、Clock"
        )
        db.add(test_question)
        db.flush()
        # 答题记录：补充question_id，满足非空约束
        answer = AnswerRecord(
            user_id=test_uid,
            question_id=test_question.id,
            subject="操作系统",
            knowledge_point="内存管理",
            is_correct=False
        )
        db.add(answer)
        # 高频知识点（补齐全部三个必填字段）
        kp = KnowledgePoint(
            subject="操作系统",
            name="内存管理",
            section="内存管理",
            content="内存管理包含分页、分段、虚拟内存、页面置换算法",
            common_mistakes="容易混淆各类页面置换算法的优缺点",
            keywords="分页,分段,虚拟内存,FIFO,LRU,OPT",
            is_high_frequency=True
        )
        db.add(kp)
        # 长期记忆记录
        memory = UserMemory(
            user_id=test_uid,
            subject="操作系统",
            knowledge_point="内存管理",
            content="页面置换算法易混淆，需强化练习",
            status="active"
        )
        db.add(memory)
        db.flush()


# 数据清理后置函数
def clear_test_user():
    with session_scope() as db:
        user = db.query(User).filter(User.id == test_uid).first()
        if user:
            db.delete(user)


# 用例1：未携带Token访问首页接口，仅校验鉴权返回结构
# 注：此用例会触发后端倒计时时区报错，根源在home_router.py，无法仅靠测试文件修复
def test_home_overview_no_authorization_token():
    response = client.get("/api/home/overview")
    res_data = response.json()
    assert res_data["ok"] is False
    assert "error" in res_data
    assert "code" in res_data["error"]
    assert "message" in res_data["error"]


# 用例2：全新空白用户登录访问，校验初始化推荐逻辑
def test_home_overview_empty_new_user():
    create_new_empty_user()
    response = client.get("/api/home/overview")
    res_data = response.json()
    assert res_data["ok"] is True
    payload = res_data["data"]

    # 校验顶层所有返回字段齐全
    required_top_fields = [
        "today_plan", "countdown", "recommendations",
        "stats", "knowledge_graph", "memories", "initial_state"
    ]
    for field in required_top_fields:
        assert field in payload

    # 空白用户今日计划模式应为四科随机综合，空状态标记为True
    today_plan = payload["today_plan"]
    assert today_plan["mode"] == "四科随机综合"
    assert today_plan["empty_state"] is True

    # 新用户初始状态标识校验
    initial_state = payload["initial_state"]
    assert initial_state["has_answers"] is False
    assert initial_state["has_mistakes"] is False
    assert initial_state["has_memories"] is False

    clear_test_user()


# 用例3：存在学习记录用户登录访问，校验薄弱点推荐逻辑
def test_home_overview_user_with_study_record():
    create_user_with_study_data()
    response = client.get("/api/home/overview")
    res_data = response.json()
    assert res_data["ok"] is True
    payload = res_data["data"]

    # 存在薄弱点，今日计划模式为薄弱点强化
    today_plan = payload["today_plan"]
    assert today_plan["mode"] == "薄弱点强化"
    assert today_plan["empty_state"] is False
    assert today_plan["subject"] == "操作系统"
    assert today_plan["knowledge_point"] == "内存管理"

    # 校验推荐列表数量不超过3条
    rec_list = payload["recommendations"]
    assert len(rec_list) <= 3
    rec_mode_list = [item["mode"] for item in rec_list]
    assert "薄弱点强化" in rec_mode_list

    # 学习统计卡片数据存在
    stats = payload["stats"]
    assert isinstance(stats["cards"], list)
    assert len(stats["cards"]) > 0

    # 知识图谱结构校验
    graph = payload["knowledge_graph"]
    assert "subjects" in graph
    assert "summary" in graph

    # 长期记忆列表有数据
    memories = payload["memories"]
    assert len(memories) > 0

    # 用户存在答题记录，初始状态标记为True
    initial_state = payload["initial_state"]
    assert initial_state["has_answers"] is True
    assert initial_state["has_mistakes"] is True
    assert initial_state["has_memories"] is True

    clear_test_user()


# 用例4：校验考研倒计时返回结构正确性
def test_home_countdown_format():
    create_new_empty_user()
    response = client.get("/api/home/overview")
    countdown = response.json()["data"]["countdown"]
    countdown_fields = ["target_date", "target_label", "days", "hours", "minutes", "seconds", "expired"]
    for field in countdown_fields:
        assert field in countdown
    clear_test_user()


# 用例5：跨域请求校验
def test_home_cross_origin_request():
    headers = {"Origin": "http://localhost:5173"}
    response = client.get("/api/home/overview", headers=headers)
    # 跨域中间件放行，无token返回401错误结构
    assert response.status_code == 401
    data = response.json()
    assert data["ok"] is False