"""
为每个王道分 P 视频生成独立的本地封面。

原因：B 站合集下所有分 P 共用一张合集主封面，导致同科目视频封面全相同。
解决：调 videoshot API 拿每个分 P 的雪碧图（10x10 网格 160x90），
      PIL 裁剪左上角第一个截图，保存到 frontend/covers/{cid}.jpg，
      更新 cover_url = /covers/{cid}.jpg。

用法：
  python _fix_wangdao_covers.py            # 处理所有
  python _fix_wangdao_covers.py --overwrite  # 强制重新生成
"""
import argparse
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import VideoResource

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True, stream=sys.stdout)
logger = logging.getLogger("fix_covers")

# B 站 view + videoshot API
VIEW_API = "https://api.bilibili.com/x/web-interface/view"
VIDEOSHOT_API = "https://api.bilibili.com/x/player/videoshot"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
}

COVERS_DIR = Path(__file__).resolve().parent.parent / "frontend" / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# 缓存每个 bv 的 (cid, page_num) 映射
_bv_pages_cache: dict[str, list[dict]] = {}


def fetch_bv_pages(bvid: str) -> list[dict]:
    """调 view API 拿合集下所有分 P 的 cid 列表。"""
    if bvid in _bv_pages_cache:
        return _bv_pages_cache[bvid]
    try:
        r = requests.get(VIEW_API, params={"bvid": bvid}, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json().get("data") or {}
        pages = data.get("pages") or []
        result = [{"cid": p["cid"], "page": p["page"], "part": p.get("part", "")} for p in pages]
        _bv_pages_cache[bvid] = result
        logger.info(f"  view {bvid}: {len(result)} pages")
        return result
    except Exception as e:
        logger.error(f"  view {bvid} 失败: {e}")
        return []


def fetch_videoshot_url(bvid: str, cid: int) -> str | None:
    """调 videoshot API 拿分 P 雪碧图 URL。"""
    try:
        r = requests.get(VIDEOSHOT_API, params={"bvid": bvid, "cid": cid}, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json().get("data") or {}
        images = data.get("image") or []
        if not images:
            return None
        url = images[0]
        if url.startswith("//"):
            url = "https:" + url
        return url
    except Exception as e:
        logger.warning(f"  videoshot {bvid}/{cid} 失败: {e}")
        return None


def _pick_best_cell(sprite: Image.Image, cell_w: int, cell_h: int, cols: int, rows: int) -> Image.Image:
    """从雪碧图 10x10 网格里选一张内容最丰富的截图作为封面。

    策略：跳过第 0 格（通常是开头黑屏/标题页），在前 10 格内选颜色方差最大的
    （方差大 = 画面内容丰富，避免纯黑/纯白/PPT 空白页）。
    """
    import numpy as np

    candidates: list[tuple[float, int, int]] = []  # (score, col, row)
    # 检查前 10 格（跳过第 0 格）
    for i in range(1, min(11, cols * rows)):
        cx = (i % cols) * cell_w
        cy = (i // cols) * cell_h
        cell = sprite.crop((cx, cy, cx + cell_w, cy + cell_h))
        arr = np.asarray(cell.convert("L"))
        # 方差越大 = 画面越丰富；同时排除过暗/过亮
        mean = arr.mean()
        if mean < 15 or mean > 240:  # 太黑或太白
            continue
        score = arr.std()  # 标准差作为丰富度
        candidates.append((float(score), i, 0))

    # 如果前 10 格都不合适，回退到第 0 格
    if not candidates:
        return sprite.crop((0, 0, cell_w, cell_h))

    # 选方差最大的
    candidates.sort(reverse=True)
    best_i = candidates[0][1]
    cx = (best_i % cols) * cell_w
    cy = (best_i // cols) * cell_h
    return sprite.crop((cx, cy, cx + cell_w, cy + cell_h))


def process_video_by_id(vid: int, bvid: str, page_num: int, pages: list[dict], overwrite: bool) -> tuple[int, str]:
    """处理一个视频：拿 cid → 拿雪碧图 → 选最佳截图 → 保存本地 → 返回新 cover_url。"""
    # 找 cid
    cid = None
    for p in pages:
        if p["page"] == page_num:
            cid = p["cid"]
            break
    if cid is None:
        return vid, ""

    # 本地文件已存在且不强制重写 → 直接返回
    local_path = COVERS_DIR / f"{cid}.jpg"
    if local_path.exists() and not overwrite:
        return vid, f"/covers/{cid}.jpg"

    # 拿雪碧图 URL
    shot_url = fetch_videoshot_url(bvid, cid)
    if not shot_url:
        return vid, ""

    # 下载雪碧图
    try:
        r = requests.get(shot_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        sprite = Image.open(BytesIO(r.content))
    except Exception as e:
        logger.warning(f"  下载 {shot_url} 失败: {e}")
        return vid, ""

    # 计算网格尺寸（雪碧图通常是 10x10，每格 img_x_size x img_y_size）
    sprite_w, sprite_h = sprite.size
    cols = max(1, sprite_w // 480)
    rows = max(1, sprite_h // 270)
    # 实际每格尺寸
    cell_w = sprite_w // cols
    cell_h = sprite_h // rows

    # 选最佳截图（跳过第 0 格，选内容最丰富的）
    crop = _pick_best_cell(sprite, cell_w, cell_h, cols, rows)
    # 缩放到 480x270（保持 16:9，清晰度足够）
    if crop.size != (480, 270):
        crop = crop.resize((480, 270), Image.LANCZOS)
    crop.save(local_path, "JPEG", quality=88)
    return vid, f"/covers/{cid}.jpg"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    videos = db.query(VideoResource).filter(
        VideoResource.crawl_source == "crawl_wangdao",
        VideoResource.is_deleted == False,
    ).all()
    logger.info(f"待处理视频: {len(videos)}")

    # 按 bv 分组，预先缓存 pages
    bv_set: set[str] = set()
    video_tuples: list[tuple[int, str]] = []  # (id, url)
    for v in videos:
        m = re.match(r"https://www.bilibili.com/video/(\w+)\?p=(\d+)", v.url or "")
        if not m:
            continue
        bv_set.add(m.group(1))
        video_tuples.append((v.id, v.url))
    for bv in bv_set:
        fetch_bv_pages(bv)

    # 并发处理（传普通 tuple，避免线程访问 ORM）
    def task(vid: int, url: str):
        m = re.match(r"https://www.bilibili.com/video/(\w+)\?p=(\d+)", url or "")
        if not m:
            return vid, ""
        bv, p = m.group(1), int(m.group(2))
        pages = _bv_pages_cache.get(bv, [])
        try:
            return process_video_by_id(vid, bv, p, pages, args.overwrite)
        except Exception as e:
            logger.error(f"  video {vid} 失败: {e}")
            return vid, ""

    ok = err = skip = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(task, vid, url): vid for vid, url in video_tuples}
        for fut in as_completed(futures):
            vid, new_url = fut.result()
            if new_url:
                db.query(VideoResource).filter(VideoResource.id == vid).update({"cover_url": new_url})
                ok += 1
            else:
                err += 1
            if (ok + err) % 50 == 0:
                db.commit()
                logger.info(f"进度: ok={ok} err={err} total={ok + err}/{len(video_tuples)}")
    db.commit()
    logger.info(f"完成: ok={ok} err={err} total={len(video_tuples)}")
    db.close()


if __name__ == "__main__":
    main()
