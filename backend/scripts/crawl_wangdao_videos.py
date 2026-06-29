"""
王道官方 408 四科视频爬虫

按 B 站合集主 BV 号拉取所有分 P，写入 video_resource 表。
字段映射：
  - subject         : 4 科中文名
  - section         : 解析后的章/节号（如 "1.1"），保留可读性
  - knowledge_point : B 站分 P 标题作为最细粒度知识点
  - title           : B 站原始分 P 标题
  - url             : https://www.bilibili.com/video/{BV}?p={n}
  - cover_url       : 合集主封面
  - duration        : mm:ss
  - author          : 王道计算机教育
  - description     : 合集描述
  - play_count      : 合集主播放量
  - platform        : Bilibili
  - crawl_source    : crawl_wangdao
  - quality_score   : 85（官方权威，默认高分）
  - reason          : 王道官方 408 课程视频

用法：
  python scripts/crawl_wangdao_videos.py                       # 拉全部 4 科
  python scripts/crawl_wangdao_videos.py --subject 数据结构      # 只拉一门
  python scripts/crawl_wangdao_videos.py --dry-run              # 仅打印不入库
  python scripts/crawl_wangdao_videos.py --rewrite              # 重建（删除已有同源）
"""
import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("crawl_wangdao_videos")

# 4 科目的官方 B 站合集主 BV 号
WANGDAO_COLLECTIONS = [
    ("数据结构", "BV1b7411N798"),
    ("计算机组成原理", "BV1ps4y1d73V"),
    ("计算机网络", "BV19E411D78Q"),
    ("操作系统", "BV1YE411D7nH"),
]

BILI_VIEW_API = "https://api.bilibili.com/x/web-interface/view"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 标题前缀：形如 "1.0_" "1.1.1+1.1.2 " "1.1_2_"
SECTION_NUM_RE = re.compile(r"^\d+(?:\.\d+)*(?:\+\d+(?:\.\d+)*)*$")


def _parse_title(raw_title: str) -> tuple[str, str]:
    """把 B 站分 P 标题解析成 (section, knowledge_point)。

    规则：按 `_` 或空白拆 token；
    开头连续的数字+点号/加号组合并为 section（如 "1.1" "1.1.2" "1.1.1+1.1.2"）；
    一旦遇到非数字 token 即停止 section 收集，剩余 token 重新用 `_` 拼回 kp。

    例子：
      "1.1_数据结构的基本概念"        -> ("1.1",     "数据结构的基本概念")
      "1.1.1+1.1.2 操作系统的概念…"  -> ("1.1.1+1.1.2", "操作系统的概念、功能和目标")
      "1.1_2_数据结构的三要素（旧版）"-> ("1.1.2",   "数据结构的三要素（旧版）")
      "2.2.1_顺序表的定义"            -> ("2.2.1",   "顺序表的定义")
      "1.0_开篇_数据结构在学什么"      -> ("1.0",     "开篇_数据结构在学什么")
      "0.0 课程白嫖指南"              -> ("0.0",     "课程白嫖指南")
      "课程白嫖指南"                  -> ("",        "课程白嫖指南")
    """
    title = (raw_title or "").strip()
    if not title:
        return "", ""

    # 统一分隔符：下划线与空白都按 token 边界
    tokens = re.split(r"[_\s]+", title)
    section_parts: list[str] = []
    rest_start = 0
    for i, t in enumerate(tokens):
        if t and SECTION_NUM_RE.match(t):
            section_parts.append(t)
            rest_start = i + 1
        else:
            break

    section = ".".join(section_parts) if section_parts else ""
    # 还原 kp 时把原本的下划线/空白替换回单下划线更易读
    kp = "_".join(t for t in tokens[rest_start:] if t).strip("_")
    if not kp:
        kp = title
    return section, kp


def _format_duration(raw) -> str:
    try:
        seconds = int(raw)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except (ValueError, TypeError):
        return str(raw or "")


def _http_get_json(url: str, params: dict, retries: int = 3, backoff: float = 2.0) -> dict | None:
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=20)
            r.raise_for_status()
            data = r.json()
            if data.get("code") == 0:
                return data.get("data") or {}
            logger.warning("B 站 API 非零返回 code=%s msg=%s", data.get("code"), data.get("message"))
            return None
        except Exception as exc:  # noqa
            last_err = exc
            logger.warning("HTTP 第 %d 次失败: %s", i + 1, exc)
            time.sleep(backoff ** i)
    logger.error("HTTP 最终失败: %s", last_err)
    return None


def fetch_collection(bvid: str) -> dict | None:
    """调用 B 站 view 接口拿合集主信息 + 全部分 P。"""
    return _http_get_json(BILI_VIEW_API, {"bvid": bvid})


def collect_pages(meta: dict) -> list[dict]:
    """将 view 返回的 pages 列表展开成统一结构。"""
    pages = meta.get("pages") or []
    out = []
    for p in pages:
        out.append({
            "page": int(p.get("page", 0) or 0),
            "part": (p.get("part") or "").strip(),
            "duration": _format_duration(p.get("duration")),
            "cid": p.get("cid"),
        })
    out.sort(key=lambda x: x["page"])
    return out


def upsert_videos(db, subject: str, bvid: str, meta: dict, pages: list[dict], *, dry_run: bool, rewrite: bool) -> dict:
    """把一个合集的所有 P 写入 video_resource。返回统计字典。"""
    cover = meta.get("pic") or ""
    if cover.startswith("//"):
        cover = "https:" + cover
    elif cover.startswith("http://"):
        # 统一为 https，避免前端 HTTPS 页被混合内容拦截
        cover = "https://" + cover[len("http://"):]
    owner = (meta.get("owner") or {}).get("name") or "王道计算机教育"
    desc = (meta.get("desc") or "").strip()
    stat = meta.get("stat") or {}
    play_total = int(stat.get("view") or 0)
    title_collection = meta.get("title") or subject

    stats = {"inserted": 0, "skipped": 0, "rewritten": 0, "failed": 0}

    for p in pages:
        page_num = p["page"]
        if page_num <= 0:
            continue
        url = f"https://www.bilibili.com/video/{bvid}?p={page_num}"
        raw_part = p["part"]
        section, kp = _parse_title(raw_part)
        full_title = f"{title_collection} - {raw_part}" if raw_part else title_collection

        # 查重
        from models import VideoResource, VideoCrawlLog  # 局部 import 兼容多入口

        existing = (
            db.query(VideoResource)
            .filter(VideoResource.url == url, VideoResource.is_deleted == False)
            .first()
        )

        if dry_run:
            logger.info("  [DRY] P%d %s -> section=%r kp=%r", page_num, url, section, kp)
            stats["skipped"] += 1
            continue

        if existing:
            if not rewrite:
                stats["skipped"] += 1
                continue
            existing.is_deleted = True
            db.flush()
            stats["rewritten"] += 1

        try:
            resource = VideoResource(
                subject=subject,
                knowledge_point=kp or subject,
                section=section or "",
                title=full_title[:180],
                platform="Bilibili",
                url=url,
                cover_url=cover,
                duration=p["duration"],
                author=owner,
                description=desc,
                quality_score=85,
                play_count=play_total,
                reason=f"王道官方 408 课程 · {title_collection} · 分P{page_num}",
                crawl_source="crawl_wangdao",
                is_active=True,
                is_deleted=False,
                last_verify_time=datetime.utcnow(),
            )
            db.add(resource)
            db.flush()
            db.add(VideoCrawlLog(
                subject=subject,
                knowledge_point=resource.knowledge_point,
                section=resource.section,
                url=url,
                platform="Bilibili",
                status="success",
                error_msg=f"crawl_wangdao p{page_num}",
            ))
            stats["inserted"] += 1
        except Exception as exc:  # noqa
            logger.exception("写入失败 P%d %s: %s", page_num, url, exc)
            db.rollback()
            stats["failed"] += 1
            break

    return stats


def main():
    parser = argparse.ArgumentParser(description="王道官方 408 视频爬虫")
    parser.add_argument("--subject", type=str, default="", help="可选：仅爬取一门（数据结构/计算机组成原理/计算机网络/操作系统）")
    parser.add_argument("--dry-run", action="store_true", help="只解析不入库")
    parser.add_argument("--rewrite", action="store_true", help="重建：删除同 URL 旧记录后重新插入")
    parser.add_argument("--sleep", type=float, default=1.5, help="合集之间的间隔秒数")
    args = parser.parse_args()

    sys.path.insert(0, "backend")
    from database import SessionLocal, init_database
    from models import VideoResource, VideoCrawlLog  # noqa: F401

    init_database()

    targets = [c for c in WANGDAO_COLLECTIONS if not args.subject or c[0] == args.subject]
    if args.subject and not targets:
        logger.error("未识别的 subject: %s（可选：%s）", args.subject, "/".join(s for s, _ in WANGDAO_COLLECTIONS))
        return

    grand_total = {"inserted": 0, "skipped": 0, "rewritten": 0, "failed": 0}

    with SessionLocal() as db:
        for idx, (subject, bvid) in enumerate(targets):
            logger.info("=" * 60)
            logger.info("开始爬取 %s | %s", subject, bvid)
            meta = fetch_collection(bvid)
            if not meta:
                logger.error("合集 %s 拉取失败，跳过", bvid)
                continue

            pages = collect_pages(meta)
            logger.info(
                "%s | 标题=%s | 分P=%d | 播放=%d | UP=%s",
                subject, meta.get("title"), len(pages),
                (meta.get("stat") or {}).get("view", 0),
                (meta.get("owner") or {}).get("name"),
            )

            stats = upsert_videos(
                db, subject, bvid, meta, pages,
                dry_run=args.dry_run, rewrite=args.rewrite,
            )
            for k, v in stats.items():
                grand_total[k] += v
            logger.info("  %s 统计: %s", subject, stats)

            try:
                db.commit()
            except Exception as exc:  # noqa
                logger.exception("提交失败: %s", exc)
                db.rollback()

            if idx < len(targets) - 1:
                time.sleep(args.sleep)

    logger.info("=" * 60)
    logger.info("完成。总计: %s", grand_total)


if __name__ == "__main__":
    main()
