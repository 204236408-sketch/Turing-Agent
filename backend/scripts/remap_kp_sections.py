"""
对 bad KP 做标题归一化 + 内容修复:
- LLM 偶尔会改 5 段的标题 (如 "高频简答计算题" -> 应映射到"常见考法")
- 或者合并 "例题" 到 "解题步骤"
- 规则: 把所有非标【】段的标题映射到最接近的标准 5 段之一
- 实在无法映射的(整段内容变成无结构), 重新调 LLM 重写

策略:
1. 读取现有 content
2. 用启发式把每个【xxx】标题映射到标准 5 段
3. 如果映射后缺段, 调 LLM 补齐 (或人工构造简单占位)
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from database import SessionLocal  # noqa: E402
from models import KnowledgePoint  # noqa: E402

SECTION_TITLES = ["核心概念", "常见考法", "解题步骤", "例题", "常见错误"]

# 自定义标题 -> 标准标题 映射
TITLE_ALIAS = {
    # 常见考法 类
    "常见考法": "常见考法",
    "高频简答计算题": "常见考法",
    "大题必考pv操作": "常见考法",
    "大题必考": "常见考法",
    "概念辨析": "常见考法",
    "判断/计算": "常见考法",
    "计算题": "常见考法",
    "碎片辨析": "常见考法",
    "高频考点": "常见考法",
    "408考点": "常见考法",
    "408考法": "常见考法",
    "408重点": "常见考法",
    "考点": "常见考法",
    "考法": "常见考法",
    "重点": "常见考法",
    # 例题 类
    "例题": "例题",
    "例题解析": "例题",
    "真题示例": "例题",
    "例题生产者消费者空缓冲初值": "例题",
    "例题银行家属于哪种策略": "例题",
    "例题三道作业": "例题",
}


def _normalize_title(t: str) -> str:
    t = t.strip()
    if t in SECTION_TITLES:
        return t
    # 直接查 alias
    if t in TITLE_ALIAS:
        return TITLE_ALIAS[t]
    # 包含关键字
    for k, v in TITLE_ALIAS.items():
        if k in t or t in k:
            return v
    return t  # 留原名, 后面再处理


def _parse_sections_raw(content: str) -> list[tuple[str, str]]:
    parts = re.split(r"【(.+?)】", content)
    out: list[tuple[str, str]] = []
    i = 1
    while i < len(parts) - 1:
        title = parts[i].strip()
        body = parts[i + 1].strip()
        out.append((title, body))
        i += 2
    return out


def _remap_sections(content: str) -> str | None:
    """把自定义标题映射到标准 5 段标题. 成功返回新 content, 失败返回 None."""
    secs = _parse_sections_raw(content)
    if not secs:
        return None
    # 按出现顺序映射, 标准 5 段只能出现 1 次
    buckets: dict[str, list[str]] = {t: [] for t in SECTION_TITLES}
    used_order: list[str] = []
    for title, body in secs:
        norm = _normalize_title(title)
        if norm in SECTION_TITLES:
            if not buckets[norm]:  # 首次出现
                used_order.append(norm)
            buckets[norm].append(body)
        else:
            # 实在无法映射 -> 把它合并到【常见考法】(兜底)
            if not buckets["常见考法"]:
                used_order.append("常见考法")
            buckets["常见考法"].append(body)

    # 拼回 content, 保持标准 5 段顺序
    if not any(buckets.values()):
        return None
    # 取第一行(关键词)
    first_line = content.split("\n", 1)[0]
    if not first_line.startswith("关键词"):
        first_line = f"关键词: {first_line}"

    parts_out: list[str] = [first_line]
    for t in SECTION_TITLES:
        bodies = buckets.get(t, [])
        if not bodies:
            # 缺段, 留空
            parts_out.append(f"【{t}】（暂无）")
            continue
        # 同段多块用换行合并, 去重
        merged = "\n".join(b.strip() for b in bodies if b.strip())
        parts_out.append(f"【{t}】{merged}")
    return "\n\n".join(parts_out)


def _has_all_5(content: str) -> bool:
    return all(f"【{t}】" in content for t in SECTION_TITLES)


def main() -> None:
    db = SessionLocal()
    try:
        all_kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        fixed = 0
        skipped = 0
        for kp in all_kps:
            c = kp.content or ""
            if not c.startswith("关键词"):
                continue
            if _has_all_5(c):
                continue
            new_c = _remap_sections(c)
            if new_c and _has_all_5(new_c):
                kp.content = new_c
                fixed += 1
            else:
                skipped += 1
                print(f"  无法修复: id={kp.id} name={kp.name!r}")
        db.commit()
        print(f"\n修复: {fixed} 跳过: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
