from p5_helpers import assert_error, assert_success, make_answer_record


def test_answer_wrong_returns_recommended_causes(auth_client):
    result = make_answer_record(auth_client)
    assert "recommended_causes" in result["answer"]
    assert isinstance(result["answer"]["recommended_causes"], list)


def test_mistake_notebook_contract(auth_client):
    body = assert_success(auth_client.get("/api/mistakes/notebook"))
    assert isinstance(body["data"], dict)


def test_mistake_requires_auth(client):
    assert_error(client.get("/api/mistakes/notebook"), status=401)
