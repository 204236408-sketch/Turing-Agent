from __future__ import annotations
import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from main import app
from database import session_scope
from config import settings
from models import (
    User, UserProfile, KnowledgePoint, UserMemory,
    Conversation, ConversationMessage, KnowledgeMastery
)
from auth import token_for_user
from services.chroma_service import delete_collection, upsert_document
from services.hybrid_retriever import hybrid_retrieve
from services.llm_service import chat_completion, LLMResult
from services.rag_service import retrieve_user_memory
from services.mastery_service import recalculate_mastery

client = TestClient(app)
TEST_COLLECTION = "knowledge_base_408"

# 预置向量测试数据
VECTOR_FIXTURE = [
    {
        "doc_id": "kp_os_001",
        "text": "LRU页面置换不会出现Belady异常，FIFO会产生Belady异常",
        "metadata": {
            "subject": "操作系统",
            "knowledge_point": "页面置换算法",
            "section": "内存管理"
        }
    }
]

# 数据库知识点固定数据
DB_KP_FIXTURE = [
    {
        "subject": "操作系统",
        "name": "页面置换算法",
        "section": "内存管理",
        "content": "FIFO、LRU、OPT、Clock四种页面置换算法",
        "common_mistakes": "混淆Belady异常产生条件",
        "keywords": "页面置换,LRU,FIFO,Belady",
        "is_high_frequency": True,
        "is_deleted": False
    }
]

# pytest 函数级隔离fixture，每个用例独立用户、数据，失败自动清理
@pytest.fixture(scope="function")
def rag_test_env():
    uid = str(uuid.uuid4())
    username = f"rag_fallback_{uid}"
    email = f"rag_{uid}@test.com"
    user_id = -1
    token = ""

    # 初始化数据库测试数据
    with session_scope() as db:
        user = User(
            email=email,
            username=username,
            password_hash="test_hash_0000",
            nickname="RAG降级测试用户"
        )
        db.add(user)
        db.flush()
        user_id = user.id
        db.add(UserProfile(user_id=user_id, target_date="2026-12-31"))

        # 插入知识点
        for kp in DB_KP_FIXTURE:
            db.add(KnowledgePoint(**kp))

        # 预置用户薄弱记忆
        mem = UserMemory(
            user_id=user_id,
            memory_type="weak_point",
            subject="操作系统",
            knowledge_point="页面置换算法",
            content="经常混淆FIFO与LRU的Belady异常",
            status="active"
        )
        db.add(mem)
        db.commit()
        token = token_for_user(user)

    # 写入向量库数据
    for vec in VECTOR_FIXTURE:
        upsert_document(
            collection=TEST_COLLECTION,
            document_id=vec["doc_id"],
            text=vec["text"],
            metadata=vec["metadata"]
        )

    yield {"user_id": user_id, "token": token}

    # 后置清理，无论用例成功/失败必执行
    with session_scope() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
        for kp_info in DB_KP_FIXTURE:
            db.query(KnowledgePoint).filter(
                KnowledgePoint.subject == kp_info["subject"],
                KnowledgePoint.name == kp_info["name"]
            ).delete()
        db.commit()
    delete_collection(TEST_COLLECTION)


# ===================== 用例1：LLM密钥未配置 llm_enabled=False 全局RAG降级 =====================
def test_rag_fallback_llm_disabled(monkeypatch, rag_test_env):
    from config import Settings
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    payload = {"conversation_id": None, "question": "什么是LRU置换算法"}
    # 冻结dataclass只能patch类，不能patch实例
    monkeypatch.setattr(Settings, "siliconflow_api_key", "")
    resp = client.post("/api/qa/chat", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["llm_used"] is False
    assert "系统暂时无法处理该问题" in data["answer"]
    assert len(data["retrieved_knowledge"]) == 0
    assert len(data["memories_used"]) == 0
    # 兜底流程仍生成标准步骤数组，满足agent_steps≥4规范
    assert len(data["agent_steps"]) >= 4
    conv_id = data["conversation_id"]
    msg_resp = client.get(f"/api/conversation/detail/{conv_id}", headers=headers)
    assert msg_resp.json()["data"]["messages"]

# ===================== 用例2：LLM接口HTTP异常/超时，触发外层全局异常降级 =====================
def test_rag_fallback_llm_http_error(rag_test_env, monkeypatch):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    payload = {"conversation_id": None, "question": "TCP四次挥手流程"}

    # 模拟LLM调用抛出异常
    def mock_chat_completion(*args, **kwargs):
        raise Exception("LLM接口504 Gateway Timeout")

    monkeypatch.setattr("services.llm_service.chat_completion", mock_chat_completion)
    resp = client.post("/api/qa/chat", json=payload, headers=headers)

    data = resp.json()["data"]
    assert data["llm_used"] is False
    assert "AI 服务异常，已降级本地回答" in str(data["agent_steps"])
    assert data["answer"] == "系统暂时无法处理该问题，请稍后重试。"
    assert len(data["agent_steps"]) >= 4

# ===================== 用例3：向量库全部删除，混合检索仅降级使用MySQL关键词检索 =====================
def test_rag_fallback_chroma_empty(rag_test_env):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    # 清空向量库集合
    delete_collection(TEST_COLLECTION)

    payload = {"conversation_id": None, "question": "页面置换算法Belady异常"}
    resp = client.post("/api/qa/chat", json=payload, headers=headers)
    data = resp.json()["data"]
    retrieved = data["retrieved_knowledge"]

    # 无chromadb来源，仅mysql关键词数据
    sources = [item.get("source", "") for item in retrieved]
    assert "chromadb" not in sources
    assert "mysql" in sources
    assert len(data["agent_steps"]) >= 4

# ===================== 用例4：检索无任何匹配数据，RAG上下文为空，仅保留用户记忆 =====================
def test_rag_fallback_no_retrieve_result(rag_test_env):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    # 提问完全不匹配任何知识点
    payload = {"conversation_id": None, "question": "汽车发动机气缸工作原理"}
    resp = client.post("/api/qa/chat", json=payload, headers=headers)
    data = resp.json()["data"]

    # 知识库检索为空，但用户记忆正常加载
    assert len(data["retrieved_knowledge"]) == 0
    assert len(data["memories_used"]) > 0
    assert data["memories_used"][0]["knowledge_point"] == "页面置换算法"
    assert len(data["agent_steps"]) >= 4

# ===================== 用例5：用户记忆读取异常，RAG跳过记忆仅使用知识库检索 =====================
def test_rag_fallback_memory_read_fail(rag_test_env, monkeypatch):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    payload = {"conversation_id": None, "question": "FIFO和LRU区别"}

    # 模拟记忆读取函数抛出异常
    def mock_retrieve_memory(*args, **kwargs):
        raise Exception("UserMemory 查询数据库失败")

    # 正确路径：原始定义文件 services.rag_service
    monkeypatch.setattr("services.rag_service.retrieve_user_memory", mock_retrieve_memory)
    resp = client.post("/api/qa/chat", json=payload, headers=headers)
    data = resp.json()["data"]

    # 记忆列表为空，知识库检索正常返回
    assert len(data["memories_used"]) == 0
    assert len(data["retrieved_knowledge"]) > 0
    assert len(data["agent_steps"]) >= 4

# ===================== 用例6：会话ID不存在，新建会话兜底，不阻断问答流程 =====================
def test_rag_fallback_conversation_not_exist(rag_test_env):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    # 传入不存在的非法会话ID
    payload = {"conversation_id": 9999999, "question": "进程调度算法"}
    resp = client.post("/api/qa/chat", json=payload, headers=headers)

    data = resp.json()["data"]
    # 自动创建全新会话，正常返回回答
    assert data["conversation_id"] != 9999999
    assert len(data["agent_steps"]) >= 4

# ===================== 用例7：掌握度更新逻辑异常，不影响主问答返回（局部降级） =====================
def test_rag_fallback_mastery_update_error(rag_test_env, monkeypatch):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    payload = {"conversation_id": None, "question": "页面置换算法"}

    # 模拟掌握度计算函数报错
    def mock_recalculate(*args, **kwargs):
        raise Exception("掌握度计算数据库写入失败")

    monkeypatch.setattr("services.mastery_service.recalculate_mastery", mock_recalculate)
    resp = client.post("/api/qa/chat", json=payload, headers=headers)

    # 主流程正常返回，无500报错
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "answer" in data
    assert len(data["agent_steps"]) >= 4

# ===================== 用例8：无Token登录，使用demo用户兜底RAG流程 =====================
def test_rag_fallback_no_token_demo_user():
    payload = {"conversation_id": None, "question": "什么是TIME_WAIT"}
    resp = client.post("/api/qa/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # demo用户无预置数据，检索为空，正常返回兜底回答
    assert isinstance(data["retrieved_knowledge"], list)
    assert len(data["agent_steps"]) >= 4

# ===================== 用例9：多轮追问，兼容检索为空不越界 =====================
def test_rag_fallback_multi_turn_followup_inherit_kp(rag_test_env):
    headers = {"Authorization": f"Bearer {rag_test_env['token']}"}
    # 第一轮提问
    first_payload = {"conversation_id": None, "question": "什么是LRU页面置换算法"}
    first_resp = client.post("/api/qa/chat", json=first_payload, headers=headers)
    assert first_resp.status_code == 200
    first_data = first_resp.json()["data"]
    conv_id = first_data["conversation_id"]
    retrieved_list = first_data["retrieved_knowledge"]

    # 兼容检索为空场景，避免直接[0]下标越界
    first_kp = None
    if retrieved_list:
        first_kp = retrieved_list[0]["knowledge_point"]

    # 第二轮追问
    follow_payload = {"conversation_id": conv_id, "question": "那它和FIFO有什么区别？"}
    follow_resp = client.post("/api/qa/chat", json=follow_payload, headers=headers)
    follow_data = follow_resp.json()["data"]
    follow_retrieved = follow_data["retrieved_knowledge"]

    # 仅当两轮都有知识点时校验继承一致
    if first_kp and follow_retrieved:
        follow_kp = follow_retrieved[0]["knowledge_point"]
        assert follow_kp == first_kp

    # 硬性验收标准：agent_steps >=4
    assert len(follow_data["agent_steps"]) >= 4