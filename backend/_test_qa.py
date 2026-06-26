import requests, json, sys
base = 'http://127.0.0.1:8000'
r = requests.post(base+'/api/auth/login', json={'username':'demo','password':'123456'}, timeout=10)
token = r.json()['data']['access_token']
h = {'Authorization': 'Bearer '+token}

print("=== QA chat test (RAG from Chroma) ===")
r = requests.post(base+'/api/qa/chat', json={
    'question': '什么是死锁？死锁的四个必要条件是什么？',
    'subject': '操作系统',
    'knowledge_point': '进程与线程'
}, headers=h, timeout=120)
d = r.json()
print("ok:", d.get('ok'))
if d.get('ok'):
    answer = d['data'].get('answer', '')
    if isinstance(answer, dict):
        answer = answer.get('content', '')
    print("Answer length:", len(answer))
    print("Answer (first 300):", answer[:300])
else:
    print("Error:", json.dumps(d, ensure_ascii=False)[:500])
