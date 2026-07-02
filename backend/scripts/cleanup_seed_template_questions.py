"""清理 seed_questions.json 中的元话术模板题。

题目文本/答案/解析/易错点/提示命中下列任意模板特征 → 视为坏题，从 JSON 中移除。
仅修改磁盘文件；不动 Question 表（那个由 cleanup_template_questions.py 处理）。
"""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_PATH = BACKEND_DIR / "data" / "seed_questions.json"

BAD_PATTERNS = (
    "的复习应优先围绕",
    "的核心内容及一个常见易错点",
    "完成下列小问",
    "易只写概念名称，缺少条件、流程或对比说明",
    "易把综合题答成单句定义，缺少分层说明",
    "易只背",
    "请注意概念成立的前提与边界",
    "易把 .* 的概念理解片面化",
    "的核心考查对象通常包括",
    "的考点通常包括",
    "的高频考点为",
    "的常见考法包括",
    "的常见考点包括",
    "应围绕关键词",
    "应重点关注",
    "应掌握的核心是",
    "出题角度通常为",
    "的常见出题形式",
)


def is_template(item: dict) -> bool:
    hints = item.get("hints") or []
    if not isinstance(hints, list):
        hints = []
    blob = "\n".join(
        [
            str(item.get("question_text", "")),
            str(item.get("standard_answer", "")),
            str(item.get("explanation", "")),
            str(item.get("easy_mistakes", "")),
            "\n".join(str(h) for h in hints),
        ]
    )
    return any(pat in blob for pat in BAD_PATTERNS)


def main():
    dry = "--apply" not in sys.argv
    if not SEED_PATH.exists():
        print(f"[error] seed file not found: {SEED_PATH}")
        return
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    keep = [q for q in data if not is_template(q)]
    bad = [q for q in data if is_template(q)]
    print(f"[scan] total={len(data)} template={len(bad)} keep={len(keep)}")
    for q in bad[:10]:
        print(f"  - {str(q.get('question_text'))[:80]!r}")
    if len(bad) > 10:
        print(f"  ... and {len(bad) - 10} more")
    if dry:
        print("dry run, add --apply to write back to seed_questions.json")
        return
    SEED_PATH.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[apply] removed {len(bad)} template questions, kept {len(keep)}")


if __name__ == "__main__":
    main()
