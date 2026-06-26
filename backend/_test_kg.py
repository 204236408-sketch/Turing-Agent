import requests, json, sys
base = 'http://127.0.0.1:8000'
r = requests.post(base+'/api/auth/login', json={'username':'demo','password':'123456'}, timeout=10)
token = r.json()['data']['access_token']
h = {'Authorization': 'Bearer '+token}

print("=== /api/home/overview knowledge_graph ===")
r = requests.get(base+'/api/home/overview', headers=h, timeout=30)
d = r.json()
if d.get('ok'):
    kg = d['data']['knowledge_graph']
    print("status_style:", list(kg.get('status_style', {}).keys()))
    for subj, nodes in kg['subjects'].items():
        names = [n['name'] for n in nodes]
        print(f"  {subj} ({len(nodes)} nodes): {names}")
else:
    print("Error:", d)

print("\n=== /api/knowledge/graph (flat) ===")
r = requests.get(base+'/api/knowledge/graph', headers=h, timeout=30)
d = r.json()
if d.get('ok'):
    for subj, nodes in d['data']['subjects'].items():
        names = [n['name'] for n in nodes[:10]]
        print(f"  {subj} ({len(nodes)} total): {names}")
else:
    print("Error:", d)
