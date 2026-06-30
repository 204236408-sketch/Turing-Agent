from p5_helpers import assert_has_keys, assert_success


def test_health_returns_ok_and_data(client):
    body = assert_success(client.get("/api/health"))
    assert isinstance(body["data"], dict)


def test_demo_account_can_login(client):
    body = assert_success(client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"}))
    assert_has_keys(body["data"], ["access_token", "user"])


def test_database_config_readable():
    import config

    settings = config.get_settings()
    assert settings.database_url or settings.mysql_url


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
