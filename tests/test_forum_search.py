from p5_helpers import assert_success


def test_forum_search_backend_full(client):
    body = assert_success(client.get("/api/forum/posts", params={"keyword": "408"}))
    assert isinstance(body["data"], dict)


def test_forum_category_filter(client):
    body = assert_success(client.get("/api/forum/posts", params={"category": "经验分享"}))
    assert isinstance(body["data"], dict)


def test_forum_pagination_params(client):
    body = assert_success(client.get("/api/forum/posts", params={"page": 1, "page_size": 5}))
    assert isinstance(body["data"], dict)
