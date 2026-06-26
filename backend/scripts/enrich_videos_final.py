"""Enrich ALL seed videos with real Bilibili BV URLs using improved crawler.

Strategy:
- Search by "408考研 {subject} {kp} {title}" order=click duration=2/3 (10-60min)
- Filter out playlists/长合集
- Pick best by combined score (relevance + popularity)
- Save BV URLs back to JSON
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.video_crawler_service import _search_bilibili, score_video

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"

BAD_KEYWORDS = ["领学班", "全程班", "完整版全集", "全套课程", "大合集", "课程完整版", "付费课程", "内部课程"]


def parse_dur(s: str) -> int:
    if not s:
        return 0
    p = s.split(":")
    try:
        p = [int(x) for x in p]
    except ValueError:
        return 0
    if len(p) == 3:
        return p[0] * 3600 + p[1] * 60 + p[2]
    if len(p) == 2:
        return p[0] * 60 + p[1]
    return 0


def is_good_video(v: dict) -> bool:
    title = v.get("title", "")
    for kw in BAD_KEYWORDS:
        if kw in title:
            return False
    dur = parse_dur(v.get("duration", ""))
    if dur and dur < 180:
        return False
    if dur and dur > 5400:
        return False
    return True


def pick_best(results: list[dict], subject: str, kp: str) -> dict | None:
    scored = []
    for v in results:
        if is_good_video(v):
            v["_score"] = score_video(v, subject, kp)
            scored.append(v)
    if scored:
        scored.sort(key=lambda x: (x["_score"], x.get("play_count", 0)), reverse=True)
        return scored[0]
    for v in results:
        v["_score"] = score_video(v, subject, kp)
    results.sort(key=lambda x: (x["_score"], x.get("play_count", 0)), reverse=True)
    return results[0] if results else None


def search_for(subject: str, kp: str, title: str) -> dict | None:
    kw1 = f"408考研 {subject} {kp} {title}"
    results = _search_bilibili(kw1, limit=15, order="click", duration=2)
    time.sleep(0.3)
    if not results:
        results = _search_bilibili(kw1, limit=15, order="click", duration=3)
        time.sleep(0.3)
    if not results:
        kw2 = f"408考研 {subject} {kp}"
        results = _search_bilibili(kw2, limit=15, order="click", duration=3)
        time.sleep(0.3)
    if not results:
        kw3 = f"408 {subject} {kp}"
        results = _search_bilibili(kw3, limit=15, order="click", duration=0)
        time.sleep(0.3)
    if not results:
        return None
    return pick_best(results, subject, kp)


def main():
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    total = len(entries)
    ok = 0
    fail = 0
    skipped = 0

    for i, entry in enumerate(entries):
        title = entry["title"]
        subject = entry["subject"]
        kp = entry["knowledge_point"]
        cur_url = entry.get("url", "")

        is_real = cur_url.startswith("https://www.bilibili.com/video/BV") or cur_url.startswith("https://www.bilibili.com/video/av")
        if is_real and is_good_video({"title": title, "duration": entry.get("duration", "")}):
            skipped += 1
            print(f"  [{i+1}/{total}] SKIP (already real BV): {title[:30]}")
            continue

        best = search_for(subject, kp, title)
        if not best:
            fail += 1
            print(f"  [{i+1}/{total}] FAIL: {kp}/{title[:30]}")
            time.sleep(2)
            continue

        entry["url"] = best["url"]
        if best.get("cover_url"):
            entry["cover_url"] = best["cover_url"]
        if best.get("duration"):
            entry["duration"] = best["duration"]
        if best.get("author"):
            entry["author"] = best["author"]
        entry["quality_score"] = int(best["_score"] * 100)
        ok += 1
        print(f"  [{i+1}/{total}] OK ({best['_score']:.2f}, {best.get('play_count',0)}p, {best.get('duration','')}, {best.get('author','')[:8]}): {title[:22]} -> {best['url']}")
        time.sleep(2.0)

    print(f"\nDone. Total={total}, OK={ok}, Skipped={skipped}, Failed={fail}")
    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Saved to {SEED_PATH}")


if __name__ == "__main__":
    main()
