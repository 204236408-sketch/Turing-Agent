"""
重跑所有不满足 "5 段固定标题" 的 KP。
- 先扫库识别
- 调 LLM 重写, 严格 5 段校验
- 失败 2 次以上则人工留 todo
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from database import SessionLocal  # noqa: E402
from models import KnowledgePoint  # noqa: E402
from scripts.llm_rewrite_kp_content import (  # noqa: E402
    SECTION_TITLES, _generate_one, _get_chapter_name,
)


def main() -> None:
    db = SessionLocal()
    try:
        all_kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        # 识别 bad: 不含全部 5 段或总长 < 900
        bad_kps: list[KnowledgePoint] = []
        for kp in all_kps:
            c = kp.content or ""
            if not c.startswith("关键词"):
                bad_kps.append(kp)
                continue
            ok = all(f"【{t}】" in c for t in SECTION_TITLES) and len(c) >= 900
            if not ok:
                bad_kps.append(kp)
        print(f"bad KP: {len(bad_kps)}/{len(all_kps)}")

        # 预扫描章节名
        chapter_names: dict[str, set[str]] = {}
        name_count: dict[tuple[str, str], int] = {}
        for kp in all_kps:
            name_count[(kp.subject, kp.name)] = name_count.get((kp.subject, kp.name), 0) + 1
        for (s, n), c in name_count.items():
            if c >= 2:
                chapter_names.setdefault(s, set()).add(n)

        if "--apply" not in sys.argv:
            for kp in bad_kps[:5]:
                chapter = _get_chapter_name(kp, chapter_names)
                print(f"\n--- BAD: id={kp.id} name={kp.name!r} kws={(kp.keywords or '')[:40]}")
                print(f"  现有 content_len: {len(kp.content or '')}")
            print("\n[dry-run] 加 --apply 才真写库")
            return

        # 真跑
        ok = fail = 0
        t0 = time.time()
        for i, kp in enumerate(bad_kps, 1):
            chapter = _get_chapter_name(kp, chapter_names)
            new_content = _generate_one(kp, chapter, max_retry=3)
            if new_content and len(new_content) >= 900:
                kp.content = new_content
                ok += 1
            else:
                fail += 1
                print(f"  [SKIP] id={kp.id} 仍不达标 (len={len(new_content or '')})")
            if i % 3 == 0:
                db.commit()
                elapsed = time.time() - t0
                eta = elapsed / i * (len(bad_kps) - i)
                print(f"  [{i}/{len(bad_kps)}] ok={ok} fail={fail} elapsed={elapsed:.0f}s eta={eta:.0f}s")
            time.sleep(1)
        db.commit()
        print(f"\n完成: ok={ok} fail={fail} 用时 {time.time()-t0:.0f}s")
    finally:
        db.close()


if __name__ == "__main__":
    main()
