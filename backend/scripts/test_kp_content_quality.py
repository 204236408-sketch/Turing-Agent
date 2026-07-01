"""LLM 重写 KP 内容的回归测试"""
import re
import sys
from pathlib import Path
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
from database import SessionLocal
from models import KnowledgePoint

SECTION_TITLES = ["核心概念", "常见考法", "解题步骤", "例题", "常见错误"]
SECTION_LIMITS = {"核心概念": 600, "常见考法": 550, "解题步骤": 600, "例题": 500, "常见错误": 550}


def _parse_sections(content: str) -> dict[str, str]:
    parts = re.split(r"【(.+?)】", content)
    if len(parts) < 3:
        return {}
    out: dict[str, str] = {}
    i = 1
    while i < len(parts) - 1:
        title = parts[i].strip()
        body = parts[i + 1].strip()
        if title in SECTION_TITLES:
            out[title] = body
        i += 2
    return out


def test_all_kps_have_5_sections():
    db = SessionLocal()
    try:
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        bad = 0
        for kp in rows:
            c = kp.content or ""
            if not c.startswith("关键词"):
                bad += 1
                continue
            secs = _parse_sections(c)
            if set(secs.keys()) != set(SECTION_TITLES):
                print(f"  缺段: id={kp.id} name={kp.name!r} sections={list(secs.keys())}")
                bad += 1
        print(f"test 1: {len(rows)-bad}/{len(rows)} KP 有完整 5 段")
        assert bad == 0, f"{bad} 个 KP 结构不完整"
    finally:
        db.close()


def test_section_length_within_limit():
    db = SessionLocal()
    try:
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        bad = 0
        for kp in rows:
            secs = _parse_sections(kp.content or "")
            for t, body in secs.items():
                limit = SECTION_LIMITS[t] + 100  # 100 字冗余
                if len(body) > limit:
                    print(f"  超长: id={kp.id} 【{t}】={len(body)}字>{limit}")
                    bad += 1
        print(f"test 2: 超长 {bad} 处")
        assert bad == 0, f"{bad} 段超长"
    finally:
        db.close()


def test_no_exact_dup_within_section():
    """检查同一段内没有完全重复的句子。"""
    db = SessionLocal()
    try:
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        bad = 0
        for kp in rows:
            secs = _parse_sections(kp.content or "")
            for t, body in secs.items():
                sents = [s.strip() for s in re.split(r"[。！？；\n]", body) if len(s.strip()) >= 8]
                seen = set()
                for s in sents:
                    if s in seen:
                        print(f"  段内重复: id={kp.id} 【{t}】 句={s[:30]}")
                        bad += 1
                        break
                    seen.add(s)
        print(f"test 3: 段内重复 {bad} 处")
        assert bad == 0, f"{bad} 处段内重复"
    finally:
        db.close()


def test_keywords_in_first_line():
    """首行必须含关键词（KP 个性化的最弱保证）。"""
    db = SessionLocal()
    try:
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        bad = 0
        for kp in rows:
            c = kp.content or ""
            first = c.split("\n", 1)[0]
            if not first.startswith("关键词"):
                bad += 1
        print(f"test 4: 缺关键词首行 {bad} 个")
        assert bad == 0
    finally:
        db.close()


def test_no_markdown_noise():
    """不允许出现 markdown 噪声符号。"""
    db = SessionLocal()
    try:
        rows = db.query(KnowledgePoint).filter(KnowledgePoint.is_deleted == False).all()
        bad = 0
        for kp in rows:
            c = kp.content or ""
            if "```" in c or "**" in c or "##" in c:
                print(f"  含 markdown 噪声: id={kp.id}")
                bad += 1
        print(f"test 5: 含 markdown 噪声 {bad} 个")
        assert bad == 0
    finally:
        db.close()


if __name__ == "__main__":
    test_all_kps_have_5_sections()
    test_section_length_within_limit()
    test_no_exact_dup_within_section()
    test_keywords_in_first_line()
    test_no_markdown_noise()
    print("\n所有测试通过")
