import requests, json
base = 'http://127.0.0.1:8000'
r = requests.post(base+'/api/auth/login', json={'username':'demo','password':'123456'}, timeout=10)
token = r.json()['data']['access_token']
h = {'Authorization': 'Bearer '+token}

# 1. Get recommendations to generate questions
print("=== Smart recommendations ===")
r = requests.get(base+'/api/questions/recommendations', headers=h, timeout=10)
recs = r.json()['data']['items']
print(json.dumps(recs, ensure_ascii=False, indent=2))

# 2. Generate questions (to get real question IDs)
print("\n=== Generate questions (智能推荐) ===")
r = requests.post(base+'/api/questions/generate-smart', json={'count':2}, headers=h, timeout=60)
gen = r.json()
if gen.get('ok'):
    qs = gen['data']['questions']
    print(f"Generated {len(qs)} questions")
    for q in qs[:2]:
        qid = q['id']
        subj = q.get('subject','')
        kp = q.get('knowledge_point','')
        title = q.get('title','')[:50]
        print(f"\n  Q{qid}: {subj} / {kp}")
        print(f"  Title: {title}")
        # 3. Get video recommendations for this question
        vr = requests.get(f'{base}/api/questions/{qid}/videos', headers=h, timeout=10)
        vd = vr.json()
        if vd.get('ok'):
            items = vd['data']['items']
            print(f"  Videos found: {len(items)}")
            for v in items[:5]:
                ml = v.get('match_level','')
                print(f"    [{ml}] {v['platform']} | {v['title'][:45]} (kp={v['knowledge_point']})")
        else:
            print(f"  Error: {vd}")
else:
    print("Error:", json.dumps(gen, ensure_ascii=False)[:500])

# 4. Test /api/videos/recommend directly
print("\n=== /api/videos/recommend?subject=操作系统&knowledge_point=内存管理 ===")
r = requests.get(base+'/api/videos/recommend?subject=操作系统&knowledge_point=内存管理', headers=h, timeout=10)
vd = r.json()
if vd.get('ok'):
    items = vd['data']['items']
    print(f"Found {len(items)} videos")
    for v in items[:5]:
        print(f"  [{v['match_level']}] {v['knowledge_point']} | {v['title'][:50]}")
