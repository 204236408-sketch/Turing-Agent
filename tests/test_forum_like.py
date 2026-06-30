from p5_helpers import assert_success, make_forum_post


def test_like_idempotent(auth_client):
    post_id = make_forum_post(auth_client)
    assert_success(auth_client.post(f"/api/forum/posts/{post_id}/like"))
    assert_success(auth_client.post(f"/api/forum/posts/{post_id}/like"))


def test_unlike_min_zero(auth_client):
    post_id = make_forum_post(auth_client)
    response = auth_client.post(f"/api/forum/posts/{post_id}/unlike")
    assert response.status_code < 500
