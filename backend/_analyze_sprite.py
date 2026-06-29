"""分析雪碧图结构"""
import sys, requests, re
sys.path.insert(0, '.')
from database import SessionLocal
from models import VideoResource
from PIL import Image
from io import BytesIO

db = SessionLocal()
v = db.query(VideoResource).filter(
    VideoResource.crawl_source == 'crawl_wangdao',
    VideoResource.is_deleted == False,
).filter(VideoResource.knowledge_point == '进程控制').first()
print(f'kp={v.knowledge_point} cover={v.cover_url}')

m = re.match(r'https://www.bilibili.com/video/(\w+)\?p=(\d+)', v.url)
bv, p = m.group(1), int(m.group(2))
print(f'bv={bv} p={p}')

r = requests.get('https://api.bilibili.com/x/web-interface/view', params={'bvid': bv}, headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'})
pages = r.json()['data']['pages']
cid = next(pp['cid'] for pp in pages if pp['page'] == p)
print(f'cid={cid}')

r2 = requests.get('https://api.bilibili.com/x/player/videoshot', params={'bvid': bv, 'cid': cid}, headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'})
data = r2.json()['data']
print('keys:', list(data.keys()))
print('image:', data.get('image'))
print(f'img_x_len={data.get("img_x_len")} img_y_len={data.get("img_y_len")}')
print(f'img_x_size={data.get("img_x_size")} img_y_size={data.get("img_y_size")}')
idx = data.get('index') or []
print(f'index count={len(idx)} first 5={idx[:5]}')
vs = data.get('video_shots') or {}
print(f'video_shots type={type(vs).__name__} keys={list(vs.keys())[:5] if isinstance(vs, dict) else "list"}')

img_url = data['image'][0]
if img_url.startswith('//'): img_url = 'https:' + img_url
r3 = requests.get(img_url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'})
sprite = Image.open(BytesIO(r3.content))
print(f'sprite size: {sprite.size}')
xsize, ysize = data['img_x_size'], data['img_y_size']
cols = sprite.width // xsize
rows = sprite.height // ysize
print(f'cols={cols} rows={rows} total_cells={cols*rows}')

# 保存整张雪碧图
sprite.save(r'c:\Users\Sophia\Desktop\turing\backend\_dbg_sprite.png')
print('saved _dbg_sprite.png')

# 保存前 9 格为对比图
for i in range(min(9, cols*rows)):
    cx = (i % cols) * xsize
    cy = (i // cols) * ysize
    cell = sprite.crop((cx, cy, cx+xsize, cy+ysize))
    cell = cell.resize((320, 180), Image.LANCZOS)
    cell.save(rf'c:\Users\Sophia\Desktop\turing\backend\_dbg_cell_{i}.png')
print('saved _dbg_cell_0..8.png')

db.close()
