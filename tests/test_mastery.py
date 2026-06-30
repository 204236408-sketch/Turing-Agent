from p5_helpers import assert_success


def test_mastery_list(auth_client):
    body = assert_success(auth_client.get("/api/mastery/list"))
    assert isinstance(body["data"], dict)
