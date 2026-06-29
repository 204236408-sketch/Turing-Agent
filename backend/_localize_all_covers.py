"""把 seed + realtime 视频的 B 站图床 cover_url 下载到本地，统一走 /covers/* 路径。

彻底解决 B 站图床防盗链问题：
- crawl_wangdao: 已本地化 ✅
- seed: 487 个，用 https://i0.hdslb.com/... → 下载到本地
- realtime: 665 个，用 https://i0.hdslb.com/... → 下载到本地

用法：
  python _localize_all_covers.py            # 下载并更新
  python _localize_all_covers.py --overwrite # 强制重新下载
"""
import argparse
import hashlib
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import VideoResource

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True, stream=sys.stdout)
logger = logging.getLogger("localize_covers")

COVERS_DIR = Path(__file__).resolve().parent.parent / "frontend" / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "image/*,*/*",
}


def download_and_save(url: str, local_path: Path) -> bool:
    """下载 B 站图床 URL 并保存为本地 jpg。"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        # 转 RGB（避免 PNG 带 alpha 通道）
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        # 限制最大尺寸（避免太大文件）
        max_w = 480
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
        img.save(local_path, "JPEG", quality=88)
        return True
    except Exception as e:
        logger.warning(f"  下载失败 {url[:80]}: {e}")
        return False


def process_video(vid: int, cover_url: str, overwrite: bool) -> tuple[int, str]:
    """处理一个视频：下载 B 站图床 URL → 保存本地 → 返回新 cover_url。"""
    if not cover_url or not cover_url.startswith("http"):
        return vid, ""

    # 用 URL hash 作为文件名（避免冲突）
    url_hash = hashlib.md5(cover_url.encode()).hexdigest()[:16]
    local_path = COVERS_DIR / f"seed_{url_hash}.jpg"

    if local_path.exists() and not overwrite:
        return vid, f"/covers/seed_{url_hash}.jpg"

    if download_and_save(cover_url, local_path):
        return vid, f"/covers/seed_{url_hash}.jpg"
    return vid, ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    # 查所有用 B 站图床 URL 的视频（seed + realtime）
    videos = db.query(VideoResource).filter(
        VideoResource.is_deleted == False,
        VideoResource.cover_url.like("http%"),
    ).all()
    logger.info(f"待本地化视频: {len(videos)}")

    # 转为普通 tuple 避免线程访问 ORM
    video_tuples = [(v.id, v.cover_url) for v in videos]

    def task(vid: int, cover_url: str):
        try:
            return process_video(vid, cover_url, args.overwrite)
        except Exception as e:
            logger.error(f"  video {vid} 失败: {e}")
            return vid, ""

    ok = err = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(task, vid, url): vid for vid, url in video_tuples}
        for fut in as_completed(futures):
            vid, new_url = fut.result()
            if new_url:
                db.query(VideoResource).filter(VideoResource.id == vid).update({"cover_url": new_url})
                ok += 1
            else:
                err += 1
            if (ok + err) % 100 == 0:
                db.commit()
                logger.info(f"进度: ok={ok} err={err} total={ok + err}/{len(video_tuples)}")
    db.commit()
    logger.info(f"完成: ok={ok} err={err} total={len(video_tuples)}")
    db.close()


if __name__ == "__main__":
    main()
