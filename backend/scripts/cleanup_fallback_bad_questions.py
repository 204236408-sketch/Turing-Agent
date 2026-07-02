"""清理 LLM 出题失败时产生的兜底模板坏题。

这些题的共同特征是：题干/选项不是真实知识点考查，而是元话术或固定模板。
脚本采用软删除（is_deleted=1），避免破坏 answer_record/favorite/mistake 等外键关联。
"""

import json
import re
from sqlalchemy import or_
from database import SessionLocal
from models import Question


_BAD_QUESTION_TEXT_PATTERNS = [
    r"核心概念，说法最准确的一项是",
    r"请填空：.*的核心定义是什么",
    r"请简要分析.*在\s*408\s*中的考查方式",
    r"综合题[^\n]*$",
]

_BAD_OPTION_PHRASES = [
    "仅考查定义背诵",
    "只考计算过程",
    "只考综合应用",
    "仅以选择题形式出现",
    "仅以大题形式出现",
    "不属于 408 考纲范围",
    "不属于408考纲范围",
    "只有 1 个固定步骤",
    "步骤之间无任何关联",
    "步骤顺序不可调整",
]


def _has_bad_option_text(options: list | str | None) -> bool:
    if not options:
        return False
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            return False
    joined = "\n".join(str(opt) for opt in options or [])
    return any(phrase in joined for phrase in _BAD_OPTION_PHRASES)


def _has_bad_question_text(text: str | None) -> bool:
    if not text:
        return False
    return any(re.search(p, text) for p in _BAD_QUESTION_TEXT_PATTERNS)


def main() -> None:
    db = SessionLocal()
    try:
        # 1) 按 quality_flag 和题干/选项元话术批量匹配
        query = db.query(Question).filter(
            Question.is_deleted == False,
            or_(
                Question.quality_flag == "deprecated",
                Question.question_text.like("%核心概念，说法最准确的一项是%"),
                Question.question_text.like("%请填空：%的核心定义是什么？%"),
                Question.question_text.like("%请简要分析%在 408 中的考查方式%"),
                Question.question_text.like("%综合题%"),
            ),
        )

        candidates = query.all()
        bad_ids = []
        for q in candidates:
            text = q.question_text or ""
            if (
                q.quality_flag == "deprecated"
                or _has_bad_question_text(text)
                or _has_bad_option_text(q.options_json)
            ):
                bad_ids.append(q.id)

        if not bad_ids:
            print("未找到兜底模板坏题，无需清理。")
            return

        # 2) 软删除
        db.query(Question).filter(Question.id.in_(bad_ids)).update(
            {"is_deleted": True}, synchronize_session=False
        )
        db.commit()
        print(f"已软删除 {len(bad_ids)} 道兜底模板坏题。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
