from __future__ import annotations

import io
from typing import Iterable


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
    b"\x00\x05\xfe\x02\xfeA\xe2\x1f\xbc\x00\x00\x00\x00IEND\xaeB`\x82"
)


def json_body(response) -> dict:
    assert response.headers.get("content-type", "").startswith("application/json"), response.text
    body = response.json()
    assert isinstance(body, dict), body
    return body


def assert_success(response, *, status: int = 200) -> dict:
    assert response.status_code == status, response.text
    body = json_body(response)
    assert body.get("ok") is True, body
    assert "data" in body, body
    return body


def assert_error(response, *, status: int) -> dict:
    assert response.status_code == status, response.text
    body = json_body(response)
    assert body.get("ok") is False, body
    return body


def assert_no_500(response) -> dict:
    assert response.status_code < 500, response.text
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return {}


def assert_has_keys(data: dict, keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in data]
    assert not missing, f"缺少字段: {missing}; 实际字段: {sorted(data.keys())}"


def route_paths(client) -> set[str]:
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    return set(response.json().get("paths", {}).keys())


def demo_auth_headers(client) -> dict:
    response = client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
    body = assert_success(response)
    token = body["data"].get("access_token") or body["data"].get("token")
    assert token, body
    return {"Authorization": f"Bearer {token}"}


def authed_client(client):
    client.headers.update(demo_auth_headers(client))
    return client


def make_question(client) -> dict:
    response = client.post(
        "/api/questions/generate",
        json={
            "subject": "操作系统",
            "knowledge_point": "页面置换算法",
            "count": 1,
            "difficulty": "中等",
            "question_type": "选择题",
        },
    )
    body = assert_success(response)
    questions = body["data"].get("questions") or []
    assert questions, body
    question = questions[0]
    assert "id" in question, question
    return question


def make_answer_record(client) -> dict:
    question = make_question(client)
    response = client.post("/api/answers/check", json={"question_id": question["id"], "user_answer": "A"})
    body = assert_success(response)
    return {"question": question, "answer": body["data"]}


def make_forum_post(client) -> int:
    response = client.post(
        "/api/forum/posts",
        json={"title": "P5验收帖子", "content": "用于P5论坛验收", "category": "经验分享"},
    )
    body = assert_success(response)
    data = body["data"]
    post_id = data.get("id") or data.get("post_id") or data.get("post", {}).get("id")
    assert post_id, body
    return post_id


def image_file(name: str = "p5.png"):
    return {"file": (name, io.BytesIO(PNG_1X1), "image/png")}
