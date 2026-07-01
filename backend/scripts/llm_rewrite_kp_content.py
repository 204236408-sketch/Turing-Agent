"""
用 LLM 为每个 KnowledgePoint 重新生成 5 段正文
- 输入: KP 的 (subject, chapter, name, keywords)
- 输出: 【核心概念】/【常见考法】/【解题步骤】/【例题】/【常见错误】 5 段
- 特点: KP 个性化（不与同章其他 KP 内容重复）、句句独立、关键点突出
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_DIR = HERE.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal  # noqa: E402
from models import KnowledgePoint  # noqa: E402
from services.llm_service import chat_completion  # noqa: E402

# 5 段标题
SECTION_TITLES = ["核心概念", "常见考法", "解题步骤", "例题", "常见错误"]

# 每段字符下限/上限, 避免 LLM 偷懒写超长或太精简
# 软下限 (达不到就重生成) / 软上限 (超了截断)
SECTION_LIMITS = {
    "核心概念": (200, 400),   # 至少 200 字, 最多 400
    "常见考法": (170, 380),
    "解题步骤": (180, 400),
    "例题": (150, 320),
    "常见错误": (170, 380),
}

# KP 关键字约束
SYSTEM_PROMPT = """你是计算机 408 考研备考助教。任务: 针对给定的"知识点"生成 5 段精炼但内容丰富的笔记。

严格要求:
1) 输出必须严格使用 5 段【】标题, 顺序固定: 【核心概念】→【常见考法】→【解题步骤】→【例题】→【常见错误】
2) 段长要求 (硬性):
   - 【核心概念】 220-380 字: 定义 + 2-3 个关键点 + 与邻近概念的区别 + 应用场景
   - 【常见考法】 200-350 字: 3-4 个 408 真实题型, 标注题型(选择题/简答/计算/应用题) + 考点侧重
   - 【解题步骤】 220-380 字: 4-5 步可操作流程, 用 ①②③④ 编号, 关键判断点必须提到
   - 【例题】 180-300 字: 1 个完整 408 风格小例, 含已知条件 + 求解过程 + 一句话答案
   - 【常见错误】 200-350 字: 3-4 个典型易错点, 每条说明"错误观点→正确观点"
3) 总字数 1000-1400 字 (5 段合计)
4) 禁止输出 markdown 符号 (##/**/```) 、emoji、空【】段落、占位符(如"暂无""略")
5) 内容必须紧扣"知识点名"展开, 不要扯到同章其他无关 KP
6) 例题必须真实可解, 步骤必须逻辑闭环
7) 避免"接下来""综上所述""由此可见"等水词, 句句干货
8) 专业术语首次出现可附英文/缩写"""


def _build_user_prompt(kp: KnowledgePoint, chapter_name: str) -> str:
    kws = kp.keywords or ""
    return (
        f"科目: {kp.subject}\n"
        f"章节: {chapter_name}\n"
        f"知识点: {kp.name}\n"
        f"关键词: {kws}\n\n"
        f"请按上述要求, 为该知识点生成 5 段笔记。"
    )


def _parse_sections(content: str) -> dict[str, str] | None:
    """把 LLM 输出切成 {标题: 正文}。返回 None 表示结构不合法。"""
    parts = re.split(r"【(.+?)】", content)
    if len(parts) < 3:
        return None
    out: dict[str, str] = {}
    i = 1
    while i < len(parts) - 1:
        title = parts[i].strip()
        body = parts[i + 1].strip()
        if title in SECTION_TITLES:
            out[title] = body
        i += 2
    # 必须 5 段齐全
    if set(out.keys()) != set(SECTION_TITLES):
        return None
    return out


def _strip_noise(text: str) -> str:
    """去掉 markdown 噪声符号。"""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    return text.strip()


def _validate(sections: dict[str, str]) -> str | None:
    """返回 None 通过, 否则返回错误描述。"""
    total = 0
    for title, body in sections.items():
        if not body:
            return f"【{title}】空"
        lo, hi = SECTION_LIMITS[title]
        # 允许 30% 短, 100 字上溢
        min_ok = max(lo - int(lo * 0.3), 100)
        if len(body) < min_ok:
            return f"【{title}】太短({len(body)}字<{min_ok})"
        if len(body) > hi + 100:
            return f"【{title}】超长({len(body)}字>{hi + 100})"
        if "【" in body or "】" in body:
            return f"【{title}】嵌套【】"
        # 占位符检测 (仅检查明确占位)
        if any(tok in body for tok in ["暂无", "（暂无）", "(暂无)", "TBD"]):
            return f"【{title}】含占位符"
        total += len(body)
    if total < 800:
        return f"总长过短({total}字<800)"
    return None


def _enforce_limits(sections: dict[str, str]) -> dict[str, str]:
    """超长段截到上限。"""
    out: dict[str, str] = {}
    for title, body in sections.items():
        _, hi = SECTION_LIMITS[title]
        limit = hi + 60  # 软上限
        if len(body) > limit:
            cut = body[:limit]
            last = max(cut.rfind("。"), cut.rfind("！"), cut.rfind("？"), cut.rfind("；"), cut.rfind("\n"))
            if last > limit * 0.5:
                cut = cut[:last + 1]
            body = cut
        out[title] = body.strip()
    return out


def _compose_content(keywords: str, sections: dict[str, str]) -> str:
    """拼成 KP.content 字符串。"""
    parts = [f"关键词: {keywords}\n"]
    for title in SECTION_TITLES:
        parts.append(f"【{title}】{sections[title]}")
    return "\n\n".join(parts)


def _generate_one(kp: KnowledgePoint, chapter_name: str, max_retry: int = 2) -> str | None:
    """调用 LLM, 返 KP.content 字符串或 None (失败)。"""
    for attempt in range(max_retry):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(kp, chapter_name)},
        ]
        result = chat_completion(
            messages, fallback="", temperature=0.5, max_tokens=2000
        )
        if not result.used_llm or not result.content:
            print(f"  [LLM FAIL] id={kp.id} err={result.error[:120]}")
            return None
        content = _strip_noise(result.content)
        sections = _parse_sections(content)
        if not sections:
            if attempt < max_retry - 1:
                print(f"  [RETRY] id={kp.id} 结构不合规, 重试")
                time.sleep(1)
                continue
            print(f"  [FAIL] id={kp.id} 多次结构不合规")
            return None
        sections = _enforce_limits(sections)
        err = _validate(sections)
        if err:
            if attempt < max_retry - 1:
                print(f"  [RETRY] id={kp.id} {err}")
                time.sleep(1)
                continue
            print(f"  [FAIL] id={kp.id} {err}")
            return None
        return _compose_content(kp.keywords or "", sections)
    return None


def _get_chapter_name(kp: KnowledgePoint, chapter_lookup: dict) -> str:
    """从文件命名或预查 DB 得章节名。"""
    # 先看 KP.name 本身是不是章节名 (DB 中 KP.name 经常是章节名)
    if kp.name and kp.name in chapter_lookup.get(kp.subject, set()):
        return kp.name
    return kp.name  # 默认


def main() -> None:
    db = SessionLocal()
    try:
        # 预扫描: 收集 (subject, name) → 是不是章节名
        all_kps = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        chapter_names: dict[str, set[str]] = {}
        # 章节名 = 同一 subject 下 name 重复 ≥ 2 次的视为章节
        name_count: dict[tuple[str, str], int] = {}
        for kp in all_kps:
            key = (kp.subject, kp.name)
            name_count[key] = name_count.get(key, 0) + 1
        for (subj, nm), cnt in name_count.items():
            if cnt >= 2:
                chapter_names.setdefault(subj, set()).add(nm)

        # 支持命令行指定只跑某个科目 / id 区间, 便于分批
        only_subject = None
        only_ids: set[int] = set()
        for arg in sys.argv[1:]:
            if arg == "--apply":
                continue
            if arg.startswith("--subject="):
                only_subject = arg.split("=", 1)[1]
            elif arg.startswith("--ids="):
                for x in arg.split("=", 1)[1].split(","):
                    if x.strip().isdigit():
                        only_ids.add(int(x))

        targets: list[KnowledgePoint] = []
        for kp in all_kps:
            if only_subject and kp.subject != only_subject:
                continue
            if only_ids and kp.id not in only_ids:
                continue
            targets.append(kp)
        print(f"待重写 KP: {len(targets)} (subject={only_subject or 'all'} ids={len(only_ids) or 'all'})")

        if "--apply" not in sys.argv:
            # dry-run: 跑前 3 个看效果
            for kp in targets[:3]:
                chapter = _get_chapter_name(kp, chapter_names)
                print(f"\n--- 样例: id={kp.id} subj={kp.subject} chapter={chapter} name={kp.name!r} kws={(kp.keywords or '')[:40]}")
                new_content = _generate_one(kp, chapter)
                if new_content:
                    print(f"new_content (前 600 字):\n{new_content[:600]}")
                time.sleep(1)
            print("\n[dry-run] 加 --apply 才真写库")
            return

        # 真跑全量
        ok = fail = 0
        t0 = time.time()
        for i, kp in enumerate(targets, 1):
            chapter = _get_chapter_name(kp, chapter_names)
            new_content = _generate_one(kp, chapter, max_retry=1)  # 不重试, 失败就跳
            if new_content:
                kp.content = new_content
                ok += 1
            else:
                fail += 1
            if i % 5 == 0:
                db.commit()
                elapsed = time.time() - t0
                eta = elapsed / i * (len(targets) - i)
                print(f"  [{i}/{len(targets)}] ok={ok} fail={fail} elapsed={elapsed:.0f}s eta={eta:.0f}s")
            time.sleep(0.2)  # 限速
        db.commit()
        print(f"\n完成: ok={ok} fail={fail} 用时 {time.time()-t0:.0f}s")
    finally:
        db.close()


if __name__ == "__main__":
    main()
