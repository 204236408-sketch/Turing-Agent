from test_smoke import client


def test_forum_posts():
    res = client.get("/api/forum/posts")
    assert res.status_code == 200
    assert res.json()["ok"] is True