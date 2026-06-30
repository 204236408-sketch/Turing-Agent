from p5_helpers import assert_error, assert_success


def test_mistake_notebook_requires_auth(client):
    assert_error(client.get("/api/mistakes/notebook"), status=401)


def test_mistake_notebook_contract(auth_client):
    body = assert_success(auth_client.get("/api/mistakes/notebook"))
    assert isinstance(body["data"], dict)


def test_mistake_list_contract(auth_client):
    body = assert_success(auth_client.get("/api/mistakes"))
    assert isinstance(body["data"], dict)
