"""Replace search URLs in seed_video_resources.json with real Bilibili video URLs.

Usage:
    python scripts/enrich_seed_video_urls.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.video_crawler_service import _search_bilibili, _relevance_score

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"


def main():
    if not SEED_PATH.exists():
        print(f"Not found: {SEED_PATH}")
        return

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    total = len(entries)
    replaced = 0
    skipped = 0

    for i, entry in enumerate(entries):
        title = entry["title"]
        subject = entry["subject"]
        knowledge_point = entry["knowledge_point"]

        # 跳过已经是真实视频链接的
        cur_url = entry.get("url", "")
        if "/video/" in cur_url or "b23.tv" in cur_url:
            skipped += 1
            print(f"  [{i+1}/{total}] SKIP (already real): {title[:30]}")
            continue

        keyword = f"408 {subject} {title}"
        results = _search_bilibili(keyword, page=1, limit=5)

        if not results:
            print(f"  [{i+1}/{total}] NO RESULTS: {title[:30]}")
            time.sleep(0.5)
            continue

        # 按相关性排序取最佳
        for v in results:
            v["_rel"] = _relevance_score(v, subject, knowledge_point)
        results.sort(key=lambda v: v["_rel"], reverse=True)
        best = results[0]
        real_url = best.get("url", "")

        if real_url and best["_rel"] >= 0.3:
            old_url = entry["url"]
            entry["url"] = real_url
            entry["cover_url"] = best.get("cover_url", "")
            entry["duration"] = best.get("duration", entry.get("duration", ""))
            entry["author"] = best.get("author", entry.get("author", ""))
            replaced += 1
            print(f"  [{i+1}/{total}] REPLACED: {title[:30]} -> {real_url[:50]}")
        else:
            print(f"  [{i+1}/{total}] LOW RELEVANCE ({best['_rel']:.2f}): {title[:30]}")

        time.sleep(0.5)  # B站 API 礼貌间隔

    print(f"\nDone. Total={total}, Replaced={replaced}, Skipped={skipped}")

    with open(SEED_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Updated: {SEED_PATH}")


if __name__ == "__main__":
    main()
