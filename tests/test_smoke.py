from pathlib import Path

from config import FRONTEND_DIR
from p5_helpers import assert_error, assert_success, route_paths


def test_openapi_and_core_routes_exist(client):
    paths = route_paths(client)
    for path in ["/api/health", "/api/auth/login", "/api/home/overview", "/api/qa/chat", "/api/questions/generate"]:
        assert path in paths


def test_frontend_version_b_served(client):
    assert (Path(FRONTEND_DIR) / "version-b.html").exists()
    response = client.get("/version-b.html")
    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_health_smoke(client):
    assert_success(client.get("/api/health"))


def test_unknown_route_404(client):
    response = client.get("/api/not-exist-p5")
    assert response.status_code == 404


def test_protected_route_401_without_token(client):
    assert_error(client.get("/api/auth/me"), status=401)
