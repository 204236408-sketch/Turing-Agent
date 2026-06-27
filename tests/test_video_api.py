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