from p5_helpers import assert_success


def test_answer_history(auth_client):
    body = assert_success(auth_client.get("/api/answers/history"))
    assert isinstance(body["data"], dict)
