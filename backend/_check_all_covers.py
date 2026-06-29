"""检查所有视频来源的 cover_url 状态"""
import sys
sys.path.insert(0, '.')
from database import SessionLocal
from models import VideoResource
from sqlalchemy import func

db = SessionLocal()

print('=== 按 crawl_source 分组 ===')
rows = db.query(VideoResource.crawl_source, func.count()).filter(
    VideoResource.is_deleted == False
).group_by(VideoResource.crawl_source).all()
for src, cnt in rows:
    print(f'  {src}: {cnt}')

print()
print('=== cover_url 状态 ===')
for src in ['seed', 'crawl_wangdao', 'crawl']:
    total = db.query(VideoResource).filter(
        VideoResource.crawl_source == src, VideoResource.is_deleted == False
    ).count()
    empty = db.query(VideoResource).filter(
        VideoResource.crawl_source == src, VideoResource.is_deleted == False,
        (VideoResource.cover_url.is_(None)) | (VideoResource.cover_url == '')
    ).count()
    local = db.query(VideoResource).filter(
        VideoResource.crawl_source == src, VideoResource.is_deleted == False,
        VideoResource.cover_url.like('/covers/%')
    ).count()
    bili = db.query(VideoResource).filter(
        VideoResource.crawl_source == src, VideoResource.is_deleted == False,
        VideoResource.cover_url.like('http%')
    ).count()
    print(f'  {src}: total={total} empty={empty} local=/covers/* ({local}) bili={bili}')

print()
print('=== seed 视频示例 ===')
for v in db.query(VideoResource).filter(
    VideoResource.crawl_source == 'seed', VideoResource.is_deleted == False
).limit(10).all():
    cv = v.cover_url[:60] if v.cover_url else '(empty)'
    print(f'  id={v.id} kp=[{v.knowledge_point}] cover=[{cv}]')
    print(f'      url={v.url}')
    print(f'      title={v.title[:60] if v.title else ""}')

print()
print('=== crawl 视频示例（如果有）===')
for v in db.query(VideoResource).filter(
    VideoResource.crawl_source == 'crawl', VideoResource.is_deleted == False
).limit(5).all():
    cv = v.cover_url[:60] if v.cover_url else '(empty)'
    print(f'  id={v.id} kp=[{v.knowledge_point}] cover=[{cv}] url={v.url[:80]}')

db.close()
