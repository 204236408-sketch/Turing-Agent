import requests, json
base = 'http://127.0.0.1:8000'
r = requests.post(base+'/api/auth/login', json={'username':'demo','password':'123456'}, timeout=10)
token = r.json()['data']['access_token']
h = {'Authorization': 'Bearer '+token}

# Test various knowledge points
test_cases = [
    ("操作系统", "内存管理"),
    ("操作系统", "进程与线程"),
    ("数据结构", "栈、队列和数组"),
    ("计算机组成原理", "输入输出系统"),
    ("计算机网络", "传输层"),
]
for subj, kp in test_cases:
    print(f"\n=== {subj} / {kp} ===")
    r = requests.get(f'{base}/api/videos/recommend?subject={requests.utils.quote(subj)}&knowledge_point={requests.utils.quote(kp)}', headers=h, timeout=10)
    vd = r.json()
    if vd.get('ok'):
        items = vd['data']['items']
        print(f"Found {len(items)} videos:")
        for v in items[:4]:
            print(f"  [{v['match_level']}] {v['knowledge_point']} | {v['title'][:40]}")
            print(f"    url: {v['url'][:80]}")
    else:
        print("Error:", vd)
