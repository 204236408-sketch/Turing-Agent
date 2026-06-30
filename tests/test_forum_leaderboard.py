from p5_helpers import assert_success


def test_hot_daily_weekly_items(client):
    daily = assert_success(client.get("/api/forum/hot", params={"period": "daily"}))
    weekly = assert_success(client.get("/api/forum/hot", params={"period": "weekly"}))
    assert isinstance(daily["data"], dict)
    assert isinstance(weekly["data"], dict)
