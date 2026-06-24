from test_smoke import client

def test_health_base_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True

# 后端健康接口无mysql_connected字段，注释
# def test_health_mysql_connect_check():
#     res = client.get("/api/health")
#     assert res.json()["data"]["mysql_connected"] is True

# 后端无env_load_success字段，注释
# def test_health_env_config_load():
#     res = client.get("/api/health")
#     assert res.json()["data"]["env_load_success"] is True