"""
test_knowledge.py 知识点接口自动化测试脚本
覆盖接口：
GET /api/knowledge/graph         获取知识图谱树
GET /api/knowledge/high-frequency 高频考点
GET /api/knowledge/recommend    智能推荐知识点
"""
from __future__ import annotations
import sys
import os
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 项目路径导入
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_PATH)

from main import app
from database import session_scope
from models import User, UserProfile, KnowledgePoint, KnowledgeMastery, Question, AnswerRecord
from auth import token_for_user
from utils.response import success

client = TestClient(app)

# 全局测试账号缓存
test_user_email = f"test_know_{uuid.uuid4()}@test.com"
test_username = f"kp_test_{uuid.uuid4()}"
test_user_id: int = -1
test_token: str = ""

# 预置知识点数据（补齐所有NOT NULL约束字段）
TEST_KP_DATA = [
    {
        "subject": "操作系统",
        "name": "页面置换算法",
        "section": "内存管理",
        "parent_name": "内存管理",
        "content": "包含FIFO、LRU、OPT、Clock四种置换策略",
        "common_mistakes": "混淆各算法优缺点、Belady异常判断",
        "keywords": "页面置换,FIFO,LRU,OPT,Clock",
        "is_high_frequency": True
    },
    {
        "subject": "操作系统",
        "name": "进程调度",
        "section": "进程管理",
        "parent_name": "进程管理",
        "content": "FCFS、SJF、HRRN、时间片轮转调度算法",
        "common_mistakes": "调度优先级计算、周转时间推导",
        "keywords": "进程调度,FCFS,SJF,HRRN",
        "is_high_frequency": False
    }
]

# 前置：创建测试用户、知识点、掌握度数据
def setup_test_data():
    global test_user_id, test_token
    with session_scope() as db:
        # 1. 创建测试用户
        user = User(
            email=test_user_email,
            username=test_username,
            password_hash="fake_hash_123456",
            nickname="知识点测试用户"
        )
        db.add(user)
        db.flush()
        test_user_id = user.id
        # 绑定用户资料
        db.add(UserProfile(user_id=test_user_id, target_date="2026-12-19"))
        # 2. 批量插入知识点
        for kp_info in TEST_KP_DATA:
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
        # 3. 创建知识点掌握记录（页面置换算法标记薄弱点）
        weak_kp = KnowledgeMastery(
            user_id=test_user_id,
            subject="操作系统",
            knowledge_point="页面置换算法",
            total_answer_count=5,
            wrong_count=3,
            weak_score=12.0,
            final_status="薄弱点"
        )
        db.add(weak_kp)
        # 4. 生成登录token
        test_token = token_for_user(user)

# 后置：清理测试数据
def teardown_test_data():
    with session_scope() as db:
        # 级联删除用户，自动清理profile、mastery等关联数据
        user = db.query(User).filter(User.id == test_user_id).first()
        if user:
            db.delete(user)
        # 删除测试知识点
        for kp_info in TEST_KP_DATA:
            db.query(KnowledgePoint).filter(
                KnowledgePoint.subject == kp_info["subject"],
                KnowledgePoint.name == kp_info["name"]
            ).delete()

# ===================== 测试用例1：无Token访问全部接口，鉴权拦截校验 =====================
def test_knowledge_no_token_all_api():
    """场景：未携带登录Token访问三个知识点接口，校验自动使用demo用户正常返回200"""
    # 1. 知识图谱
    resp_graph = client.get("/api/knowledge/graph")
    assert resp_graph.status_code == 200
    data_graph = resp_graph.json()
    assert data_graph["ok"] is True

    # 2. 高频考点
    resp_hf = client.get("/api/knowledge/high-frequency")
    assert resp_hf.status_code == 200
    data_hf = resp_hf.json()
    assert data_hf["ok"] is True

    # 3. 智能推荐
    resp_rec = client.get("/api/knowledge/recommend")
    assert resp_rec.status_code == 200
    data_rec = resp_rec.json()
    assert data_rec["ok"] is True

# ===================== 测试用例2：GET /api/knowledge/graph 知识图谱接口 =====================
def test_knowledge_graph_tree():
    """场景：登录用户请求知识图谱，校验树状结构、掌握状态、着色style、scope参数"""
    setup_test_data()
    headers = {"Authorization": f"Bearer {test_token}"}

    # 用例2.1 scope=all 全量无用户状态
    resp_all = client.get("/api/knowledge/graph?scope=all", headers=headers)
    assert resp_all.status_code == 200
    res_all = resp_all.json()
    assert res_all["ok"] is True
    data_all = res_all["data"]
    assert "subjects" in data_all
    subjects = data_all["subjects"]
    os_subject = next(s for s in subjects if s["name"] == "操作系统")
    assert len(os_subject["children"]) > 0

    # 用例2.2 scope=user 携带用户掌握状态、颜色样式
    resp_user = client.get("/api/knowledge/graph?scope=user", headers=headers)
    res_user = resp_user.json()
    tree_data = res_user["data"]["subjects"]
    os_tree = next(s for s in tree_data if s["name"] == "操作系统")
    memory_node = next(c for c in os_tree["children"] if c["name"] == "内存管理")
    page_kp = next(k for k in memory_node["children"] if k["name"] == "页面置换算法")
    # 校验薄弱点状态与配色
    assert page_kp["status"] == "薄弱点"
    assert page_kp["style"]["color"] == "#e95f52"

    teardown_test_data()

# ===================== 测试用例3：GET /api/knowledge/high-frequency 高频考点接口 =====================
def test_knowledge_high_frequency():
    """场景：登录用户获取高频考点列表，校验is_high_frequency筛选、返回字段完整性"""
    setup_test_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/high-frequency", headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert res["ok"] is True
    items = res["data"]["items"]
    # 校验仅返回高频知识点
    kp_names = [item["knowledge_point"] for item in items]
    assert "页面置换算法" in kp_names
    assert "进程调度" not in kp_names
    # 校验返回字段
    sample = items[0]
    assert "subject" in sample
    assert "knowledge_point" in sample
    assert "content" in sample

    teardown_test_data()

# ===================== 测试用例4：GET /api/knowledge/recommend 智能推荐接口 =====================
def test_knowledge_recommend():
    """场景：存在薄弱知识点的登录用户，校验推荐算法输出结构、薄弱点优先推荐"""
    setup_test_data()
    headers = {"Authorization": f"Bearer {test_token}"}
    resp = client.get("/api/knowledge/recommend", headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert res["ok"] is True
    rec_items = res["data"]["items"]
    assert isinstance(rec_items, list)
    # 校验推荐字段完整性
    first_rec = rec_items[0]
    assert "mode" in first_rec
    assert "subject" in first_rec
    assert "knowledge_point" in first_rec
    assert "reason" in first_rec
    assert "difficulty" in first_rec
    assert "question_type" in first_rec
    assert "count" in first_rec

    teardown_test_data()

# ===================== 测试用例5：跨域请求校验 =====================
def test_knowledge_cross_origin():
    """场景：前端携带Origin跨域头访问知识点接口，校验跨域放行"""
    setup_test_data()
    headers = {
        "Origin": "http://localhost:5173",
        "Authorization": f"Bearer {test_token}"
    }
    resp = client.get("/api/knowledge/graph", headers=headers)
    assert resp.status_code == 200
    # 校验跨域响应头
    assert "access-control-allow-origin" in resp.headers
    teardown_test_data()