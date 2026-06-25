import time
from pathlib import Path

from config import BASE_DIR
from services.chroma_service import upsert_document, chroma_status
from services.vector_embedding_service import embedding_status


def _parse_md_file(filepath: Path) -> dict | None:
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    lines = text.splitlines()
    metadata = {
        "subject": "",
        "name": "",
        "section": "",
        "knowledge_point": "",
    }
    content_lines = []

    # 行内元数据模式: "key: value"（在 # 标题之前出现）
    frontmatter_keys = {"subject", "knowledge_point", "section", "chapter", "keywords"}
    frontmatter: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            break
        key, _, val = stripped.partition(":")
        key = key.strip().lower()
        if key in frontmatter_keys:
            frontmatter[key] = val.strip()
            continue
        break

    metadata["subject"] = frontmatter.get("subject", "")
    metadata["knowledge_point"] = frontmatter.get("knowledge_point", "")
    metadata["section"] = frontmatter.get("section", frontmatter.get("chapter", ""))

    for line in lines:
        if line.startswith("# "):
            if not metadata["name"]:
                metadata["name"] = line[2:].strip()
        elif line.startswith("## "):
            if not metadata["section"]:
                metadata["section"] = line[3:].strip()
        elif line.startswith("- **科目**"):
            if not metadata["subject"]:
                metadata["subject"] = line.split("**")[2].strip() if "**" in line else ""
        elif line.startswith("- **知识点**"):
            if not metadata["knowledge_point"]:
                metadata["knowledge_point"] = line.split("**")[2].strip() if "**" in line else ""
        content_lines.append(line)

    if not metadata["subject"]:
        parts = filepath.relative_to(BASE_DIR).parts
        for p in parts:
            if p in ("数据结构", "计算机组成原理", "操作系统", "计算机网络"):
                metadata["subject"] = p
                break

    content = "\n".join(content_lines).strip()
    if not content:
        return None

    return {
        "document_id": f"md_{filepath.stem}",
        "text": content,
        "metadata": {k: v for k, v in metadata.items() if v},
    }


def import_markdown_docs(docs_dir: Path) -> dict:
    if not docs_dir.exists():
        return {"success": False, "error": f"directory not found: {docs_dir}", "imported": 0, "failed": 0}

    md_files = sorted(docs_dir.glob("**/*.md"))
    if not md_files:
        return {"success": True, "error": "no md files found", "imported": 0, "failed": 0}

    imported = 0
    failed = 0
    errors = []

    for fp in md_files:
        parsed = _parse_md_file(fp)
        if parsed is None:
            failed += 1
            errors.append(f"{fp.name}: parse failed")
            continue

        result = upsert_document(
            "knowledge_base_408",
            parsed["document_id"],
            parsed["text"],
            parsed["metadata"],
        )
        if result.get("stored"):
            imported += 1
        else:
            failed += 1
            errors.append(f"{fp.name}: {result.get('error', 'unknown error')}")

    return {
        "success": True,
        "imported": imported,
        "failed": failed,
        "errors": errors[:10],
    }


def import_from_database(db_session) -> dict:
    from models import KnowledgePoint

    imported = 0
    failed = 0
    for item in db_session.query(KnowledgePoint).all():
        text = f"{item.subject} {item.name} {item.content}"
        meta = {
            "subject": item.subject,
            "knowledge_point": item.name,
            "section": item.section or "",
        }
        result = upsert_document("knowledge_base_408", str(item.id), text, meta)
        if result.get("stored"):
            imported += 1
        else:
            failed += 1

    return {"imported": imported, "failed": failed}


if __name__ == "__main__":
    print("=" * 50)
    print("ChromaDB 知识库导入工具")
    print("=" * 50)

    status = chroma_status()
    print(f"\nChromaDB 状态: {'已启用' if status['enabled'] else '未启用'}")
    if not status["enabled"]:
        print(f"原因: {status.get('error', 'chromadb 未安装')}")
        print("将以 fallback 模式运行（标记 stored=false）")

    emb_status = embedding_status()
    print(f"Embedding 状态: {'可用' if emb_status['available'] else '不可用'}")

    docs_dir = BASE_DIR.parent / "knowledge_docs"
    if docs_dir.exists():
        print(f"\n从 {docs_dir} 导入 Markdown 文档...")
        md_result = import_markdown_docs(docs_dir)
        print(f"  Markdown: 成功 {md_result['imported']}, 失败 {md_result['failed']}")
        if md_result["errors"]:
            for e in md_result["errors"]:
                print(f"    - {e}")
    else:
        print(f"\n知识库文档目录不存在: {docs_dir}")
        print("从数据库 KnowledgePoint 导入...")
        from database import SessionLocal, init_database

        init_database()
        with SessionLocal() as db:
            db_result = import_from_database(db)
            print(f"  数据库: 成功 {db_result['imported']}, 失败 {db_result['failed']}")

    print("\n完成。")
