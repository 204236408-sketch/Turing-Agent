from p5_helpers import assert_success


def test_video_crawl_failure_or_mock_not_500(auth_client):
    response = auth_client.post("/api/videos/crawl", json={"keyword": "页面置换算法"})
    assert response.status_code < 500


def test_zero_video_recommend_fallback(auth_client):
    body = assert_success(auth_client.get("/api/videos/recommend", params={"subject": "不存在学科", "knowledge_point": "不存在知识点"}))
    assert isinstance(body["data"], dict)
