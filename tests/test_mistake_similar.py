from p5_helpers import assert_success


def test_mistake_detail_missing_returns_404_or_empty(auth_client):
    response = auth_client.get("/api/mistakes/999999")
    assert response.status_code in (200, 404)


def test_mistake_notebook_chroma_unavailable_does_not_500(auth_client):
    body = assert_success(auth_client.get("/api/mistakes/notebook"))
    assert isinstance(body["data"], dict)
