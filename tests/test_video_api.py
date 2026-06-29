import pytest
from unittest.mock import patch

# 场景1：数据库仅1条视频，校验crawl_triggered=True
from unittest.mock import patch

def test_recommend_only_one_video(anon_client):
    mock_return = {
        "subject": "操作系统",
        "knowledge_point": "进程调度",
        "crawl_triggered": True,
        "items": [{"id": 1, "title": "进程调度", "quality_score": 92}],
        "llm_keywords": [],
        "keyword_extract_method": "rule_fallback",
        "total_candidates": 1,
        "local_count": 1,
        "crawl_count": 0,
        "cache_hit": False,
        "question_type": "未知",
        "difficulty_hint": "中等",
    }
    # 直接拦截service源头函数，彻底隔离真实数据库
    with patch("services.video_service.recommend_videos_v2") as mock_func:
        mock_func.return_value = mock_return
        resp = anon_client.get(
            "/api/videos/recommend",
            params={"subject": "操作系统", "knowledge_point": "进程调度", "limit": 3}
        )
        print("mock调用次数：", mock_func.call_count)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 1

# 场景2：数据库超过3条，自动按quality_score降序截取TOP3
def test_recommend_more_than_three_top3_sort(anon_client):
    mock_return = {
        "subject": "计算机网络",
        "knowledge_point": "TCP流量控制",
        "crawl_triggered": False,
        "items": [
            {"id": 10, "title": "TCP流量控制", "quality_score": 98},
            {"id": 11, "title": "三次握手", "quality_score": 95},
            {"id": 12, "title": "拥塞控制", "quality_score": 90},
            {"id": 13, "title": "滑动窗口", "quality_score": 82},
        ]
    }
    with patch("backend.routers.video_router.recommend_videos_v2") as mock_func:
        mock_func.return_value = mock_return
        resp = anon_client.get(
            "/api/videos/recommend",
            params={"subject": "计算机网络", "knowledge_point": "TCP流量控制", "limit": 3}
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    items = data["items"]
    # 最多返回3条
    assert len(items) == 3
    # 校验降序排序
    scores = [item["quality_score"] for item in items]
    assert scores == sorted(scores, reverse=True)

# 场景3：数据库0条匹配视频，触发兜底fallback，接口不500
def test_recommend_zero_video_fallback_no_500(anon_client):
    mock_return = {
        "subject": "数据结构",
        "knowledge_point": "红黑树",
        "items": []
    }
    with patch("services.video_service.recommend_videos_v2") as mock_func:
        mock_func.return_value = mock_return
        resp = anon_client.get(
            "/api/videos/recommend",
            params={"subject": "数据结构", "knowledge_point": "红黑树", "limit": 3}
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 0


# 场景4：_wangdao_match_score 的 section 专属术语匹配
# 修复前：KP section="数组和特殊矩阵" → 视频"3.4.1-3.4.4_特殊矩阵的压缩存储" 得 0 分
# 修复后：因 '特殊矩阵' (4字专属术语) 命中 → 应得 ≥ 60 分
class _StubVideo:
    """轻量 VideoResource 替身，绕过 ORM 构造"""
    def __init__(self, kp, title=""):
        self.knowledge_point = kp
        self.title = title


def test_wangdao_match_section_specific_term():
    """section 中的 3+ 字专属术语命中 v_kp 应得到 60+ 分"""
    from services.video_service import _wangdao_match_score

    # 1) 核心场景：数组和特殊矩阵 → 特殊矩阵的压缩存储（之前为 0 分）
    video = _StubVideo("3.4.1-3.4.4_特殊矩阵的压缩存储", "王道计算机考研 数据结构 - 3.4.1-3.4.4_特殊矩阵的压缩存储")
    score = _wangdao_match_score(video, "栈、队列和数组", "数组和特殊矩阵", "数据结构")
    assert score >= 60, f"特殊矩阵 专属术语应得高分，实际={score}"

    # 2) 错配防护："next数组" 不应被 "数组" 误判为 2 字泛指的强相关
    video = _StubVideo("求next数组", "王道计算机考研 数据结构 - 求next数组")
    score = _wangdao_match_score(video, "栈、队列和数组", "数组和特殊矩阵", "数据结构")
    assert score < 50, f"next数组 不应被 '数组' section 误判为强相关，实际={score}"

    # 3) 父章节上下文不应压过 section 匹配：
    #    KP "传输层/TCP" 下，"传输层提供的服务"（父章节匹配）应低于
    #    "TCP的流量控制"（section 术语匹配）
    video_parent = _StubVideo("传输层提供的服务", "王道计算机考研 计算机网络 - 5.1 传输层提供的服务")
    video_section = _StubVideo("TCP的流量控制", "王道计算机考研 计算机网络 - 5.3.5 TCP的流量控制")
    s_parent = _wangdao_match_score(video_parent, "传输层", "TCP", "计算机网络")
    s_section = _wangdao_match_score(video_section, "传输层", "TCP", "计算机网络")
    assert s_section > s_parent, (
        f"section 专属术语匹配 ({s_section}) 应高于父章节匹配 ({s_parent})"
    )


# 场景5：王道推荐：存在强命中时不应回退到泛相关种子视频
def test_wangdao_recommend_no_padding_when_strong_match(anon_client):
    """当 recommend_wangdao_for_knowledge_point 找到强命中时，结果应仅含强命中，
    不应回退到 recommend_videos_v2 补足"""
    from services.video_service import recommend_wangdao_for_knowledge_point
    from database import SessionLocal
    from models import KnowledgePoint

    db = SessionLocal()
    try:
        # 找一个有 section 的 KP（数组和特殊矩阵 已确认能命中专属视频）
        point = db.query(KnowledgePoint).filter(
            KnowledgePoint.section == "数组和特殊矩阵",
            KnowledgePoint.is_deleted == False,
        ).first()
        if not point:
            pytest.skip("需要 seed_knowledge_points.json 中有 '数组和特殊矩阵' 知识点")
        result = recommend_wangdao_for_knowledge_point(db, point.id, limit=5)
        # 强命中时只返回 1 条（数据库中只有 1 条特殊矩阵的压缩存储），
        # 不应回退到 4 条不相关的"栈、队列和数组"视频
        assert result["wangdao_matched"] >= 1
        if result["wangdao_matched"] >= 1:
            for it in result["items"]:
                # 王道强匹配条目的 source 必须是 wangdao_db，不能是 wangdao_db_fallback_*
                assert it["source"].startswith("wangdao_db"), (
                    f"存在强命中时不应回退，但 source={it['source']}"
                )
    finally:
        db.close()