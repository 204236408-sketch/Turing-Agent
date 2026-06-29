import requests
import json

# Login
r = requests.post("http://127.0.0.1:8000/api/auth/login",
                  json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
print(f"login: {r.status_code}")
data = r.json()
print(f"  data: {data}")
token = data.get("data", {}).get("access_token") or data.get("access_token")
user = data.get("data", {}).get("user") or data.get("user")
print(f"  token[:30]: {token[:30] if token else 'None'}")
print(f"  user: {user}")

# Verify /me
r2 = requests.get("http://127.0.0.1:8000/api/auth/me",
                  headers={"Authorization": f"Bearer {token}"}, timeout=10)
print(f"\n/me: {r2.status_code}")
print(f"  body: {r2.text[:200]}")
