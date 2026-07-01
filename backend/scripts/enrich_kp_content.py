"""
扩充 KnowledgePoint.content 字段
策略：扫描 backend/data/knowledge_docs/ 下的所有 .md 文件，
把同 (subject, name, keywords) 的所有小节内容合并到 KP.content。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_DIR = HERE.parent
DOCS_DIR = BACKEND_DIR / "data" / "knowledge_docs"
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal  # noqa: E402
from models import KnowledgePoint  # noqa: E402

# md 文件按 "----------------------------------------" 分块
# 每块结构：
# # 标题
# subject: xxx
# knowledge_point: xxx
# keywords: k1,k2,k3
# <空行>
# ## 核心概念
# ...
# ## 408 高频...
# ## 解题步骤
# ...
# ## 例题
# ...
# ## 常见错误
# ...


SECTION_HEADER = re.compile(r"^##\s+(.+?)\s*$", re.M)


def _parse_blocks(md_text: str) -> list[dict]:
    """把 md 文本切成块，每块含元信息和所有 ## 小节。"""
    blocks: list[dict] = []
    raw_blocks = re.split(r"-{5,}", md_text)
    for raw in raw_blocks:
        raw = raw.strip("\n")
        if not raw.strip():
            continue
        # 提取头部 4 行: # title / subject: / knowledge_point: / keywords:
        lines = raw.split("\n")
        title = ""
        meta = {"subject": "", "knowledge_point": "", "keywords": ""}
        i = 0
        # 标题
        for j, ln in enumerate(lines):
            if ln.startswith("# ") and not ln.startswith("## "):
                title = ln[2:].strip()
                i = j + 1
                break
        # 解析 key: value
        for j in range(i, min(i + 8, len(lines))):
            ln = lines[j].strip()
            for k in ("subject", "knowledge_point", "keywords"):
                if ln.startswith(f"{k}:"):
                    meta[k] = ln[len(k) + 1:].strip()
                    break
        if not meta["subject"] or not meta["knowledge_point"]:
            continue

        # 解析 ## 小节
        sections: list[tuple[str, str]] = []
        current_title = None
        current_buf: list[str] = []
        for ln in lines[i + 4:]:
            m = SECTION_HEADER.match(ln)
            if m:
                if current_title is not None:
                    sections.append((current_title, "\n".join(current_buf).strip()))
                current_title = m.group(1).strip()
                current_buf = []
            else:
                if current_title is not None:
                    current_buf.append(ln)
        if current_title is not None:
            sections.append((current_title, "\n".join(current_buf).strip()))

        blocks.append({
            "subject": meta["subject"],
            "knowledge_point": meta["knowledge_point"],
            "keywords": meta["keywords"],
            "sections": sections,
        })
    return blocks


def _split_sentences(text: str) -> list[str]:
    """按中英文句末标点切句,保留分隔符。"""
    if not text:
        return []
    # 中文标点: 。！？ 英文标点: . ! ?  顿号/分号按短句保留
    parts = re.split(r"(?<=[。！？!?])\s*", text)
    return [p.strip() for p in parts if p and p.strip()]


def _sentence_jaccard(a: str, b: str) -> float:
    """两个句子的字符级 Jaccard 相似度。"""
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    return len(inter) / len(union) if union else 0.0


# 内容型 section 允许的最大字符数,避免一个 section 堆出几千字
# 排版上: 核心概念 / 易错点 / 408 重点 这种"重点突出"型 section 收紧
# 解题步骤 / 例题 这种"过程型" section 适当放宽
_SECTION_CHAR_LIMIT = {
    "核心概念": 600,
    "基本概念": 600,
    "概念": 600,
    "定义": 600,
    "概述": 600,
    "易错点": 400,
    "常见错误": 400,
    "误区": 400,
    "408 重点": 400,
    "408高频考点": 400,
    "常见考法": 400,
    "408 常见考法": 400,
    "考法": 400,
    "考点": 400,
    "408 重点与考点": 400,
    "解题步骤": 800,
    "例题": 800,
    "总结": 400,
    "重点": 400,
}
_SECTION_CHAR_LIMIT_DEFAULT = 600
_DEDUPE_THRESHOLD = 0.72  # 句子级 jaccard 超过该阈值视为重复


def _dedupe_and_trim(body: str, max_chars: int) -> str:
    """对 section body 做句级去重 + 字符数截断。

    去重策略：
    - 按句末标点切句
    - 与已保留句的 jaccard > 阈值时跳过(视为同一内容重复)
    - 累计字符数超过 max_chars 时截断尾部

    这样可让一个 section 内"同义/复述"只保留第一次出现,
    后续 block 的同 title 内容若不补充新信息就不会再被追加。
    """
    if not body:
        return ""
    sentences = _split_sentences(body)
    kept: list[str] = []
    used: list[str] = []  # 已保留句的字符集合缓存(避免重复计算 jaccard)
    total = 0
    for s in sentences:
        # 句级去重
        dup = False
        for u in used:
            if _sentence_jaccard(s, u) >= _DEDUPE_THRESHOLD:
                dup = True
                break
        if dup:
            continue
        # 字符数限制
        if total + len(s) > max_chars and kept:
            break
        kept.append(s)
        used.append(s)
        total += len(s)
    return "".join(kept)


def _flatten_sections(sections: list[tuple[str, str]]) -> str:
    """把 [('核心概念', '...'), ('例题', '...')] 拼成一段大文本。

    每个 section body 在拼接前先做句级去重 + 字符数截断,防止多个 md 块同 title
    拼接时出现"同一句话重复 2-7 遍"的乱排版。
    """
    out: list[str] = []
    for title, body in sections:
        if not body:
            continue
        # 简化标题: '408 出栈序列合法性判断' -> '高频考点'
        norm = re.sub(r"^408\s*", "", title).strip()
        limit = _SECTION_CHAR_LIMIT.get(norm, _SECTION_CHAR_LIMIT_DEFAULT)
        trimmed = _dedupe_and_trim(body, limit)
        if not trimmed:
            continue
        out.append(f"【{norm}】{trimmed}")
    return "\n\n".join(out)


def _keywords_set(kw: str) -> set[str]:
    return {w.strip() for w in re.split(r"[,，;；\s]+", kw) if w.strip()}


def main() -> None:
    db = SessionLocal()
    try:
        # 1. 解析所有 md 文件 -> 所有块
        all_blocks: list[dict] = []
        for md in DOCS_DIR.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            all_blocks.extend(_parse_blocks(text))
        print(f"解析到 {len(all_blocks)} 个知识块")

        # 2. 按 (subject, knowledge_point) 分组
        groups: dict[tuple[str, str], list[dict]] = {}
        for b in all_blocks:
            key = (b["subject"], b["knowledge_point"])
            groups.setdefault(key, []).append(b)

        # 3. 对每个 KP 在 DB 中查找，匹配最相关的块
        kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        updated = 0
        skipped = 0
        for kp in kps:
            grp = groups.get((kp.subject, kp.name))
            if not grp:
                skipped += 1
                continue
            kp_kws = _keywords_set(kp.keywords or "")
            # 找最匹配的块：keywords 集合 Jaccard 最高
            best = None
            best_j = 0.0
            for blk in grp:
                blk_kws = _keywords_set(blk["keywords"])
                if not kp_kws or not blk_kws:
                    continue
                inter = kp_kws & blk_kws
                union = kp_kws | blk_kws
                j = len(inter) / len(union) if union else 0
                if j > best_j:
                    best_j = j
                    best = blk
            if not best or best_j < 0.1:
                # 没匹配上 -> 用第一个块
                best = grp[0]

            # 拼接：把所有相关 section 全部拼起来
            section_texts: list[str] = []
            seen_section_titles: set[str] = set()
            for blk in grp:
                for title, body in blk["sections"]:
                    if title in seen_section_titles:
                        # 合并同标题的多块内容
                        idx = next(i for i, (t, _) in enumerate(section_texts) if t == title)
                        section_texts[idx] = (title, section_texts[idx][1] + "\n" + body)
                    else:
                        section_texts.append((title, body))
                        seen_section_titles.add(title)
            enriched = _flatten_sections(section_texts)

            # 加上关键词
            full_content = f"关键词：{best['keywords']}\n\n{enriched}"
            # 不再以"更长"为更新条件——本轮 enrich 加了去重/截断后内容可能更短
            # 改为：含至少 1 个 section 头（【xxx】）就覆盖,保证历史脏数据被刷新
            has_section = "【" in enriched and "】" in enriched
            if has_section:
                kp.content = full_content
                # 同步 common_mistakes（从 ## 常见错误 section 提取）
                for title, body in section_texts:
                    if "常见错误" in title or "易错" in title:
                        # common_mistakes 也走一次去重截断,避免存几千字
                        mistakes_limit = _SECTION_CHAR_LIMIT.get("易错点", 400)
                        kp.common_mistakes = _dedupe_and_trim(body, mistakes_limit)
                        break
                updated += 1
        db.commit()
        print(f"已更新 {updated} 个 KP，{skipped} 个无匹配（跳过）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
