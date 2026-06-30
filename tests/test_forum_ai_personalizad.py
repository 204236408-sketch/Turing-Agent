from p5_helpers import assert_success, make_forum_post


def test_forum_ai_answer_personalized_section(auth_client, monkeypatch):
    monkeypatch.setattr("routers.forum_router.ai_answer_for_post", lambda *a, **k: {
        "answer": {"content": "个性化回答"},
        "answer_id": 1,
        "personalized_section": {"weak_points": []},
        "should_followup": False,
    })
    post_id = make_forum_post(auth_client)
    body = assert_success(auth_client.post(f"/api/forum/posts/{post_id}/ai-answer", json={"question": "如何复习操作系统？"}))
    assert "personalized_section" in body["data"]
