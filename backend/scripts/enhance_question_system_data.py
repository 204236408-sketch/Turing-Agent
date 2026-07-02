from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
for path in (str(ROOT), str(BACKEND)):
    if path not in sys.path:
        sys.path.insert(0, path)

from database import SessionLocal, init_database
from models import KnowledgePoint, Question, Subject


DATA_DIR = BACKEND / "data"
KNOWLEDGE_PATH = DATA_DIR / "seed_knowledge_points.json"
QUESTION_PATH = DATA_DIR / "seed_questions.json"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _clean_text(text: str, limit: int = 90) -> str:
    text = " ".join((text or "").replace("\n", " ").split())
    if not text:
        return ""
    return text[:limit].rstrip("，；。") + ("。" if not text[:limit].endswith("。") else "")


def _first_fact(content: str, section: str) -> str:
    parts = [p.strip() for p in (content or "").replace("；", "。").split("。") if p.strip()]
    if not parts:
        return f"{section} 是 408 考纲中的基础知识点，需要掌握定义、适用条件和常见易错点。"
    return _clean_text(parts[0], 96)


def _mistake_option(common_mistakes: str, section: str) -> str:
    mistake = _clean_text(common_mistakes, 70)
    if not mistake:
        return f"只要记住 {section} 的名称即可，不需要区分条件和边界。"
    return mistake


def _keywords(keywords: str, section: str) -> list[str]:
    raw = [x.strip() for x in (keywords or "").replace("，", ",").split(",") if x.strip()]
    out: list[str] = []
    for item in [section, *raw]:
        if item and item not in out:
            out.append(item)
    return out[:5]


def build_questions_for_point(item: dict[str, Any]) -> list[dict[str, Any]]:
    subject = item.get("subject", "")
    chapter = item.get("name", "")
    section = item.get("section") or chapter
    content = item.get("content", "")
    common_mistakes = item.get("common_mistakes", "")
    fact = _first_fact(content, section)
    mistake = _mistake_option(common_mistakes, section)
    kws = _keywords(item.get("keywords", ""), section)
    first_keyword = kws[0] if kws else section

    base = {
        "subject": subject,
        "knowledge_point": chapter,
        "section": section,
        "source": "seed",
        "easy_mistakes": common_mistakes or f"容易只背结论，忽略 {section} 的条件、边界和适用场景。",
    }
    return [
        {
            **base,
            "difficulty": "简单",
            "question_type": "选择题",
            "variant_type": "choice",
            "question_text": f"关于{section}，下列说法正确的是？",
            "options": [
                f"A. {fact}",
                f"B. {mistake}",
                f"C. {section} 与 {subject} 的其他知识点没有任何联系",
                f"D. {section} 只会考固定记忆题，不会结合条件或流程辨析",
            ],
            "standard_answer": "A",
            "explanation": f"本题依据知识库：{fact} 常见误区是：{mistake}",
            "hints": [f"先回忆 {section} 的核心定义。", "再排除忽略条件、边界或联系的说法。"],
        },
        {
            **base,
            "difficulty": "中等",
            "question_type": "填空题",
            "variant_type": "fill",
            "question_text": f"{section} 的核心考查对象通常包括：____。",
            "standard_answer": "、".join(kws[:3]) if kws else first_keyword,
            "explanation": f"{section} 应围绕关键词 {', '.join(kws)} 展开，答题时需要结合定义和条件。",
            "hints": [f"先定位 {section} 的关键词。", "再写出最能代表该知识点的核心术语。"],
        },
        {
            **base,
            "difficulty": "中等",
            "question_type": "简答题",
            "variant_type": "essay",
            "question_text": f"简述{section}的核心内容，并指出一个常见易错点。",
            "standard_answer": f"1. 核心内容：{fact}\n2. 常见易错点：{mistake}",
            "explanation": f"简答题应先写核心结论，再补充适用条件或易混点。{section} 的易错点可从知识库 common_mistakes 字段提取。",
            "hints": [f"先写 {section} 的核心结论。", "再补一个条件、边界或常见误区。"],
        },
    ]


def unique_knowledge_items() -> list[dict[str, Any]]:
    raw = _load_json(KNOWLEDGE_PATH, [])
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for item in raw:
        subject = item.get("subject", "").strip()
        chapter = item.get("name", "").strip()
        section = (item.get("section") or chapter).strip()
        key = (subject, chapter, section)
        if not all(key) or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def enhance_seed_questions(write: bool) -> int:
    knowledge = unique_knowledge_items()
    existing = _load_json(QUESTION_PATH, [])
    if isinstance(existing, dict):
        existing = existing.get("questions", [])
    by_identity = {
        (
            q.get("subject", ""),
            q.get("knowledge_point", ""),
            q.get("section", ""),
            q.get("variant_type") or q.get("question_type", ""),
            q.get("question_text", ""),
        )
        for q in existing
    }
    additions: list[dict[str, Any]] = []
    for item in knowledge:
        for q in build_questions_for_point(item):
            key = (
                q.get("subject", ""),
                q.get("knowledge_point", ""),
                q.get("section", ""),
                q.get("variant_type") or q.get("question_type", ""),
                q.get("question_text", ""),
            )
            if key in by_identity:
                continue
            by_identity.add(key)
            additions.append(q)

    if write and additions:
        _dump_json(QUESTION_PATH, existing + additions)
    return len(additions)


def dedupe_knowledge_points(db) -> int:
    rows = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.is_deleted == False)
        .order_by(KnowledgePoint.subject.asc(), KnowledgePoint.name.asc(), KnowledgePoint.section.asc(), KnowledgePoint.id.asc())
        .all()
    )
    groups: dict[tuple[str, str, str, str], list[KnowledgePoint]] = {}
    for row in rows:
        content_key = " ".join((row.content or "").split())[:500]
        key = (row.subject or "", row.name or "", row.section or row.name or "", content_key)
        groups.setdefault(key, []).append(row)

    marked = 0
    for items in groups.values():
        if len(items) <= 1:
            continue
        keep = max(items, key=lambda r: (len(r.content or ""), bool(r.is_high_frequency), -r.id))
        for row in items:
            if row.id == keep.id:
                continue
            row.is_deleted = True
            marked += 1
    return marked


def sync_seed_questions_to_db(db) -> int:
    data = _load_json(QUESTION_PATH, [])
    questions = data.get("questions", []) if isinstance(data, dict) else data
    inserted = 0
    for item in questions:
        qtext = item.get("question_text") or ""
        subject = item.get("subject") or ""
        kp = item.get("section") or item.get("knowledge_point") or ""
        if not qtext or not subject or not kp:
            continue
        exists = (
            db.query(Question.id)
            .filter(
                Question.subject == subject,
                Question.knowledge_point == kp,
                Question.question_text == qtext,
                Question.is_deleted == False,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            Question(
                subject=subject,
                knowledge_point=kp,
                difficulty=item.get("difficulty") or "中等",
                question_type=item.get("question_type") or "选择题",
                variant_type=item.get("variant_type") or "choice",
                question_text=qtext,
                options_json=item.get("options") or [],
                sub_questions_json=item.get("sub_questions") or [],
                standard_answer=item.get("standard_answer") or "",
                explanation=item.get("explanation") or "解析暂缺。",
                hints_json=item.get("hints") or ["先定位知识点。", "再排除常见误区。"],
                easy_mistakes=item.get("easy_mistakes") or "",
                recommend_reason=f"种子题库：用于覆盖 {subject} / {kp} 的基础考法。",
                source="seed",
                is_verified=True,
                quality_score=100,
                quality_flag="normal",
            )
        )
        inserted += 1
    return inserted


def ensure_subjects(db) -> None:
    names = {item.get("subject") for item in unique_knowledge_items() if item.get("subject")}
    for order, name in enumerate(sorted(names), 1):
        if not db.query(Subject.id).filter(Subject.name == name).first():
            db.add(Subject(name=name, description=f"408 {name} 考纲知识体系", sort_order=order))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-seed-json", action="store_true", help="append generated seed questions to backend/data/seed_questions.json")
    parser.add_argument("--apply-db", action="store_true", help="dedupe knowledge points and sync seed questions to the local database")
    args = parser.parse_args()

    added_to_json = enhance_seed_questions(write=args.write_seed_json)
    print(f"seed question candidates: {added_to_json}")

    if args.apply_db:
        init_database()
        db = SessionLocal()
        try:
            ensure_subjects(db)
            deduped = dedupe_knowledge_points(db)
            inserted = sync_seed_questions_to_db(db)
            db.commit()
            print(f"knowledge duplicates marked deleted: {deduped}")
            print(f"seed questions inserted into db: {inserted}")
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


if __name__ == "__main__":
    main()
