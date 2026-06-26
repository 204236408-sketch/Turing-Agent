import json
from pathlib import Path
import sys
sys.path.insert(0, '.')

p = Path('data/seed_video_resources.json')
with open(p,'r',encoding='utf-8') as f:
    data = json.load(f)
print(f'Total videos in JSON: {len(data)}')
subjects = {}
for v in data:
    subj = v.get('subject','')
    subjects[subj] = subjects.get(subj,0)+1
print('By subject:', subjects)
print()
for v in data[:8]:
    title = v.get("title","")[:60]
    print(f'  {v["subject"]} / {v["knowledge_point"]}: {title}')
