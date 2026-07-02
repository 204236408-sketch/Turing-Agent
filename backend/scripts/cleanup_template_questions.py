"""清理已入库的元话术模板题。

匹配规则复用 backend/agents/question_graph.py:_is_template_question：
- 题面/解析/答案/易错点/提示出现下列模板特征 → 视为坏题，软删除
  - "的复习应优先围绕"
  - "的核心内容及一个常见易错点"
  - "完成下列小问"
  - "易只写概念名称，缺少条件、流程或对比说明"
  - "易把综合题答成单句定义，缺少分层说明"
  - "易只背"
  - "请注意概念成立的前提与边界"
  - "易把 .* 的概念理解片面化"

不会动 LLM 出的题（这些题不会含上面特征）。
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal  # noqa: E402
from models import Question  # noqa: E402

BAD_PATTERNS = (
    "的复习应优先围绕",
    "的核心内容及一个常见易错点",
    "完成下列小问",
    "易只写概念名称，缺少条件、流程或对比说明",
    "易把综合题答成单句定义，缺少分层说明",
    "易只背",
    "请注意概念成立的前提与边界",
    "易把 .* 的概念理解片面化",
    # 增量：seed 题库里的填空题元话术
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


def is_template(question: Question) -> bool:
    hints = question.hints_json or []
    if not isinstance(hints, list):
        hints = []
    blob = "\n".join(
        [
            str(question.question_text or ""),
            str(question.standard_answer or ""),
            str(question.explanation or ""),
            str(question.easy_mistakes or ""),
            "\n".join(str(h) for h in hints),
        ]
    )
    return any(pat in blob for pat in BAD_PATTERNS)


def main():
    dry = "--apply" not in sys.argv
    db = SessionLocal()
    try:
        rows = db.query(Question).filter(Question.is_deleted == False).all()  # noqa: E712
        bad = [q for q in rows if is_template(q)]
        print(f"[scan] total={len(rows)} template_questions={len(bad)}")
        if not bad:
            print("no template questions to clean")
            return
        for q in bad:
            print(f"  - id={q.id} kp={q.knowledge_point!r} stem={str(q.question_text)[:80]!r}")
        if dry:
            print("dry run, add --apply to soft-delete these rows")
            return
        for q in bad:
            q.is_deleted = True
        db.commit()
        print(f"[apply] soft-deleted {len(bad)} template questions")
    finally:
        db.close()


if __name__ == "__main__":
    main()
