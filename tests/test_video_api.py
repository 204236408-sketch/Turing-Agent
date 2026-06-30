from p5_helpers import assert_success


def test_video_recommend_contract(auth_client):
    body = assert_success(auth_client.get("/api/videos/recommend", params={"subject": "操作系统", "knowledge_point": "页面置换算法"}))
    assert isinstance(body["data"], dict)


def test_video_list_contract(auth_client):
    body = assert_success(auth_client.get("/api/videos/list"))
    assert isinstance(body["data"], dict)


def test_video_click_contract(auth_client):
    response = auth_client.post("/api/videos/click", json={"video_id": 999999})
    assert response.status_code < 500
