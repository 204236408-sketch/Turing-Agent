"""Recalculate quality_score for seed videos using new popularity-aware weights,
and replace invalid/unpopular URLs with better Bilibili videos.

Usage:
    python scripts/refresh_seed_videos.py
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.video_crawler_service import score_video, _search_bilibili, _format_duration

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"
VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def _extract_video_id(url: str) -> str | None:
    m = re.search(r'/av(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'/video/(BV\w+)', url)
    if m:
        return m.group(1)
    m = re.search(r'[?&]aid=(\d+)', url)
    if m:
        return m.group(1)
    return None


def _fetch_video_stats(url: str) -> dict | None:
    vid = _extract_video_id(url)
    if not vid:
        return None
    params = {"bvid": vid} if vid.startswith("BV") else {"aid": vid}
    try:
        resp = requests.get(VIEW_URL, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("code") != 0:
            return None
        d = data["data"]
        stat = d.get("stat", {})
        return {
            "platform": "Bilibili",
            "title": d.get("title", ""),
            "tag": "",
            "description": d.get("desc", ""),
            "play_count": stat.get("view", 0) or 0,
            "like_count": stat.get("like", 0) or 0,
            "danmaku_count": stat.get("danmaku", 0) or 0,
            "publish_time": d.get("pubdate", 0),
            "author": d.get("owner", {}).get("name", ""),
        }
    except requests.RequestException:
        return None
    except (KeyError, json.JSONDecodeError):
        return None


def _search_replacement(subject: str, title: str, knowledge_point: str) -> dict | None:
    for keyword in [
        f"408 {subject} {title}",
        f"{subject} {title}",
        f"408 {subject} {knowledge_point}",
        f"{subject} {knowledge_point}考研",
    ]:
        results = _search_bilibili(keyword, page=1, limit=10)
        if not results:
            time.sleep(0.5)
            continue
        for v in results:
            v["score"] = score_video(v, subject, knowledge_point)
        results.sort(key=lambda v: v["score"], reverse=True)
        best = results[0]
        if best["score"] >= 0.3:
            return best
        time.sleep(0.5)
    return None


def main():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    stats = {"recalc": 0, "replaced": 0, "failed": 0, "skipped": 0, "total": len(data)}

    for i, entry in enumerate(data):
        url = entry.get("url", "")
        subject = entry["subject"]
        kp = entry["knowledge_point"]
        title_short = entry["title"][:30]
        print(f"[{i+1}/{len(data)}] {title_short} ... ", end="")

        if "/video/av" not in url and "/video/BV" not in url:
            print(f"bad URL, searching replacement ...")
            best = _search_replacement(subject, entry["title"], kp)
            if best and best.get("url"):
                entry["url"] = best["url"]
                entry["cover_url"] = best.get("cover_url", "")
                entry["duration"] = best.get("duration", "")
                entry["author"] = best.get("author", "")
                entry["quality_score"] = round(best["score"] * 100)
                stats["replaced"] += 1
                print(f"  -> REPLACED: {best['url'][:55]} (score={best['score']:.2f})")
            else:
                stats["failed"] += 1
                print(f"  -> FAILED (no replacement found)")
            continue

        # Valid video URL — fetch stats and recalc quality_score
        video_stats = _fetch_video_stats(url)
        if video_stats is None:
            print(f"API fail, searching replacement ...")
            best = _search_replacement(subject, entry["title"], kp)
            if best and best.get("url"):
                entry["url"] = best["url"]
                entry["cover_url"] = best.get("cover_url", "")
                entry["duration"] = best.get("duration", "")
                entry["author"] = best.get("author", "")
                entry["quality_score"] = round(best["score"] * 100)
                stats["replaced"] += 1
                print(f"  -> REPLACED: {best['url'][:55]} (score={best['score']:.2f})")
            else:
                stats["failed"] += 1
                print(f"  -> FAILED (no replacement)")
            time.sleep(1)
            continue

        old_score = entry.get("quality_score", 0)
        old_author = entry.get("author", "")
        new_score = score_video(video_stats, subject, kp)
        new_score_int = round(new_score * 100)
        entry["quality_score"] = new_score_int
        api_author = video_stats.get("author", "")
        if api_author and api_author != old_author:
            entry["author"] = api_author
        stats["recalc"] += 1
        play = video_stats.get("play_count", 0)
        author_note = f" author: {old_author} -> {api_author}" if api_author and api_author != old_author else ""
        print(f"score {old_score} -> {new_score_int} (play={play}){author_note}")
        time.sleep(0.3)

    SEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone: {json.dumps(stats, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
