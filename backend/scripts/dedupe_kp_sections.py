"""
对所有 KP 做段内去重 (合并重复句子) + 段内截断
- 段内: 相同/高度相似句子保留首个
- 段过长: 截到软上限
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from database import SessionLocal  # noqa: E402
from models import KnowledgePoint  # noqa: E402

SECTION_TITLES = ["核心概念", "常见考法", "解题步骤", "例题", "常见错误"]
# 软上限: 只在远超上限时截断, 平时不限制
SOFT_LIMITS = {
    "核心概念": 700,
    "常见考法": 650,
    "解题步骤": 700,
    "例题": 600,
    "常见错误": 650,
}


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    return len(inter) / len(union) if union else 0.0


def _dedupe_lines(body: str) -> str:
    """按行/句子去重。短行精确去重, 长行 Jaccard>=0.78 视为重复。"""
    # 按 \n 拆行, 行内按 。！？； 拆句
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    kept: list[str] = []
    used: list[str] = []
    for line in lines:
        # 拆句
        sents = [s.strip() for s in re.split(r"(?<=[。！？；])\s*", line) if s.strip()]
        for s in sents:
            if len(s) < 4:
                kept.append(s)
                continue
            # 短行精确去重
            if len(s) <= 25:
                if any(s == u or s in u for u in used):
                    continue
            # 长行 Jaccard
            dup = any(_jaccard(s, u) >= 0.78 for u in used)
            if dup:
                continue
            kept.append(s)
            used.append(s)
    return "".join(kept)


def _truncate(body: str, limit: int) -> str:
    if len(body) <= limit:
        return body
    cut = body[:limit]
    last = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"), cut.rfind("；"), cut.rfind("\n"))
    if last > limit * 0.5:
        cut = cut[:last + 1]
    return cut


def _process_content(content: str) -> tuple[str, int]:
    """处理一个 KP.content, 返回 (新内容, 修改标记)。"""
    if not content.startswith("关键词"):
        return content, 0
    # 拆 section
    parts = re.split(r"【(.+?)】", content)
    if len(parts) < 3:
        return content, 0
    first_line = parts[0].strip()
    out: list[str] = [first_line]
    changed = 0
    i = 1
    while i < len(parts) - 1:
        title = parts[i].strip()
        body = parts[i + 1].strip()
        if title in SECTION_TITLES:
            new_body = _dedupe_lines(body)
            new_body = _truncate(new_body, SOFT_LIMITS[title])
            if new_body != body:
                changed += 1
            out.append(f"【{title}】{new_body}")
        else:
            out.append(f"【{title}】{body}")
        i += 2
    return "\n\n".join(out), changed


def main() -> None:
    db = SessionLocal()
    try:
        all_kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        total_changed = 0
        for kp in all_kps:
            c = kp.content or ""
            new_c, changed = _process_content(c)
            if changed > 0:
                kp.content = new_c
                total_changed += 1
        db.commit()
        print(f"处理: {total_changed} 个 KP 内容有变动")
    finally:
        db.close()


if __name__ == "__main__":
    main()
