"""Second pass: replace remaining search/invalid URLs with real Bilibili video URLs,
with author-aware matching and validation of existing video URLs.

Key improvements over v1:
  - Validates existing av/BV URLs via Bilibili view API (author check)
  - Multi-tier search: includes author name in keywords for precision
  - Author match bonus in scoring (0.4 boost when author matches)
  - Auto-corrects platform label based on actual URL pattern
  - Only accepts results where author matches the intended one (when possible)
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.video_crawler_service import _format_duration, score_video

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://search.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://search.bilibili.com",
    "Connection": "keep-alive",
}

SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
VIEW_URL = "https://api.bilibili.com/x/web-interface/view"
SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_video_resources.json"


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


def _author_matches(actual: str, expected: str) -> bool:
    if not actual or not expected:
        return False
    a, e = actual.strip().lower(), expected.strip().lower()
    if a == e:
        return True
    if len(a) >= 2 and len(e) >= 2 and (a in e or e in a):
        return True
    return False


def _validate_existing_url(url: str, expected_author: str) -> tuple[bool, str]:
    vid = _extract_video_id(url)
    if not vid:
        return False, "cannot_parse_id"
    params = {"bvid": vid} if vid.startswith("BV") else {"aid": vid}
    try:
        resp = requests.get(VIEW_URL, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return False, f"http_{resp.status_code}"
        data = resp.json()
        if data.get("code") != 0:
            return False, f"api_{data['code']}"
        owner = data.get("data", {}).get("owner", {})
        actual_author = (owner or {}).get("name", "")
        if not actual_author:
            return False, "no_owner_info"
        if _author_matches(actual_author, expected_author):
            return True, actual_author
        return False, f"author_mismatch:expected={expected_author},actual={actual_author}"
    except requests.RequestException as e:
        return False, f"request_error:{e}"
    except (KeyError, json.JSONDecodeError) as e:
        return False, f"parse_error:{e}"


def _search_bilibili(keyword: str, page: int = 1, limit: int = 10) -> list[dict]:
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"search_type": "video", "keyword": keyword, "page": page, "page_size": limit},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        result = resp.json()
        if result.get("code") != 0:
            return []
        return (result.get("data", {}).get("result", []) or [])
    except Exception:
        return []


def _score_candidate(v: dict, subject: str, knowledge_point: str, expected_author: str) -> dict:
    title = v.get("title", "").replace('<em class="keyword">', "").replace("</em>", "")
    actual_author = v.get("author", "")
    normalized = {
        "platform": "Bilibili",
        "title": title,
        "tag": v.get("tag", ""),
        "description": v.get("description", ""),
        "play_count": v.get("play", 0) or 0,
        "like_count": v.get("like", 0) or 0,
        "danmaku_count": v.get("video_review", 0) or 0,
        "publish_time": v.get("pubdate", 0),
    }
    author_bonus = 0.4 if _author_matches(actual_author, expected_author) else 0.0
    rel_score = score_video(normalized, subject, knowledge_point)
    return {
        "title": title,
        "url": v.get("arcurl", ""),
        "cover_url": v.get("pic", ""),
        "author": actual_author,
        "duration": _format_duration(v.get("duration", 0)),
        "play": v.get("play", 0),
        "_rel": round(rel_score, 3),
        "_author_bonus": author_bonus,
        "_score": round(min(rel_score + author_bonus, 1.0), 3),
    }


def _find_best_video(subject: str, title: str, knowledge_point: str, author: str) -> dict | None:
    tiers = [
        f"408 {subject} {title} {author}",
        f"{title} {author}",
        f"408 {subject} {title}",
        f"{subject} {title}",
    ]
    best = None
    for tier_num, keyword in enumerate(tiers, 1):
        raw = _search_bilibili(keyword, limit=10)
        if not raw:
            continue
        scored = [_score_candidate(v, subject, knowledge_point, author) for v in raw]
        scored.sort(key=lambda x: x["_score"], reverse=True)
        top = scored[0]

        if top["_score"] >= 0.3:
            if best is None or top["_score"] > best["_score"]:
                top["_tier"] = tier_num
                top["_keyword"] = keyword
                best = top

            if top["_author_bonus"] > 0 and top["_rel"] >= 0.3:
                return best

        time.sleep(0.5)
    return best


def _is_skip_url(url: str) -> bool:
    return "cheese" in url or "b23.tv" in url


def main():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    report = {
        "validated_ok": 0,
        "replaced": 0,
        "author_mismatch_replaced": 0,
        "platform_fixed": 0,
        "skipped_cheese": 0,
        "failed": 0,
    }

    for i, entry in enumerate(data):
        title_short = entry["title"][:30]
        author = entry.get("author", "")
        orig_url = entry.get("url", "")
        orig_platform = entry.get("platform", "")

        # --- Step 1: Auto-correct platform label ---
        if "bilibili.com" in orig_url and orig_platform != "Bilibili":
            entry["platform"] = "Bilibili"
            report["platform_fixed"] += 1
            print(f"  [{i+1}] PLATFORM: {orig_platform}->Bilibili | {title_short}")

        # --- Step 2: Skip cheese / b23.tv (can't resolve to video URL) ---
        if _is_skip_url(orig_url):
            report["skipped_cheese"] += 1
            print(f"  [{i+1}] SKIP (cheese/b23): {title_short}")
            continue

        has_video_url = "/video/av" in orig_url or "/video/BV" in orig_url

        # --- Step 3: Validate existing av/BV URLs ---
        if has_video_url:
            is_valid, detail = _validate_existing_url(orig_url, author)
            if is_valid:
                report["validated_ok"] += 1
                print(f"  [{i+1}] VALID: {title_short} (author={detail})")
                continue
            report["author_mismatch_replaced"] += 1
            print(f"  [{i+1}] MISMATCH: {title_short} | {detail}")
        else:
            print(f"  [{i+1}] SEARCH: {title_short} (url={orig_url[:50]})")

        # --- Step 4: Re-search for invalid / search URLs ---
        time.sleep(1)
        best = _find_best_video(entry["subject"], entry["title"], entry["knowledge_point"], author)
        if best is None or not best.get("url"):
            report["failed"] += 1
            print(f"  [{i+1}] FAILED (no result): {title_short}")
            continue

        entry["url"] = best["url"]
        entry["cover_url"] = best.get("cover_url", entry.get("cover_url", ""))
        entry["duration"] = best.get("duration", entry.get("duration", ""))
        entry["platform"] = "Bilibili"
        report["replaced"] += 1
        tier = best.get("_tier", "?")
        author_status = "MATCH" if best["_author_bonus"] > 0 else "DIFF"
        action = "REPLACED" if not has_video_url else "FIXED"
        print(f"  [{i+1}] {action} (tier={tier}, author={author_status}, rel={best['_rel']}): {title_short} -> {best['url'][:55]}")

        time.sleep(1)

    # --- Save ---
    SEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    real = sum(1 for x in data if "/video/av" in x.get("url", "") or "/video/BV" in x.get("url", ""))
    search = sum(1 for x in data if "search.bilibili" in x.get("url", ""))
    cheese = sum(1 for x in data if "cheese" in x.get("url", ""))
    b23 = sum(1 for x in data if "b23.tv" in x.get("url", ""))

    print(f"\n{'='*60}")
    print(f"Done: {json.dumps(report, ensure_ascii=False)}")
    print(f"{'='*60}")
    print(f"Final URL stats:")
    print(f"  /video/av or /video/BV : {real}")
    print(f"  search.bilibili        : {search}")
    print(f"  cheese                 : {cheese}")
    print(f"  b23.tv                 : {b23}")
    print(f"  total                  : {len(data)}")


if __name__ == "__main__":
    main()
