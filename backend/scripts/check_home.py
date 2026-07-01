import json, sys, urllib.request

token = "eyJzdWIiOiI4IiwidXNlcm5hbWUiOiJzbW9rZV91c2VyIiwiZXhwIjoxNzgzNDI5NzU1fQ.R4gkRMUt3e4h7AfwAHyuhY51ssIyv1yo0aibAHhTKaI"
req = urllib.request.Request("http://127.0.0.1:8123/api/home/overview", headers={"Authorization": f"Bearer {token}"})
resp = urllib.request.urlopen(req, timeout=10)
d = json.loads(resp.read().decode("utf-8"))
p = d["data"]["today_plan"]
print("=== today_plan ===")
for k in ("knowledge_point", "subject", "empty_state", "initial_state", "title", "count", "available", "mode", "difficulty", "question_type"):
    print(f"  {k:18s} = {p.get(k)!r}")
print()
print("=== recommendations ===")
for r in d["data"]["recommendations"]:
    print(f"  {r['mode']:12s} kp={r.get('knowledge_point')!r:20s} available={r.get('available')} initial={r.get('initial')} reason={r.get('reason','')[:40]!r}")
