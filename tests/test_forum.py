from p5_helpers import assert_success


def test_forum_posts_contract(client):
    body = assert_success(client.get("/api/forum/posts"))
    assert isinstance(body["data"], dict)


def test_forum_categories_contract(client):
    body = assert_success(client.get("/api/forum/categories"))
    assert isinstance(body["data"], dict)
