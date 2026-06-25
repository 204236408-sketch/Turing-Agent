import time
from pathlib import Path

from config import BASE_DIR
from services.chroma_service import chroma_status, get_or_create_collection, delete_collection, upsert_document
from services.vector_embedding_service import embedding_status


def rebuild_collection(collection_name: str) -> dict:
    status = chroma_status()
    if not status["enabled"]:
        return {"success": False, "error": "ChromaDB 未启用，无法重建", "collection": collection_name}

    try:
        existing = get_or_create_collection(collection_name)
        if existing.get("created"):
            return {"success": True, "collection": collection_name, "action": "created"}

        delete_collection(collection_name)
        get_or_create_collection(collection_name)
        return {"success": True, "collection": collection_name, "action": "rebuilt"}
    except Exception as e:
        return {"success": False, "error": str(e), "collection": collection_name}


def import_knowledge_from_docs() -> dict:
    from services.chroma_service import upsert_document

    docs_dir = BASE_DIR.parent / "knowledge_docs"
    if not docs_dir.exists():
        return {"success": False, "error": f"知识库目录不存在: {docs_dir}", "imported": 0}

    imported = 0
    failed = 0
    for fp in sorted(docs_dir.glob("**/*.md")):
        try:
            text = fp.read_text(encoding="utf-8")
            lines = text.splitlines()
            metadata = {"subject": "", "name": "", "knowledge_point": ""}
            for line in lines:
                if line.startswith("# ") and not metadata["name"]:
                    metadata["name"] = line[2:].strip()
                elif line.startswith("- **科目**"):
                    metadata["subject"] = line.split("**")[2].strip() if "**" in line else ""
                elif line.startswith("- **知识点**"):
                    metadata["knowledge_point"] = line.split("**")[2].strip() if "**" in line else ""
            if not metadata["subject"]:
                for p in fp.relative_to(BASE_DIR).parts:
                    if p in ("数据结构", "计算机组成原理", "操作系统", "计算机网络"):
                        metadata["subject"] = p
                        break
            result = upsert_document("knowledge_base_408", f"md_{fp.stem}", text, {k: v for k, v in metadata.items() if v})
            if result.get("stored"):
                imported += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1

    return {"success": True, "imported": imported, "failed": failed}


def import_knowledge_from_db() -> dict:
    from database import SessionLocal, init_database
    from models import KnowledgePoint

    init_database()
    imported = 0
    failed = 0
    with SessionLocal() as db:
        for item in db.query(KnowledgePoint).all():
            text = f"{item.subject} {item.name} {item.content}"
            meta = {"subject": item.subject, "knowledge_point": item.name, "section": item.section or ""}
            result = upsert_document("knowledge_base_408", str(item.id), text, meta)
            if result.get("stored"):
                imported += 1
            else:
                failed += 1
    return {"imported": imported, "failed": failed}


if __name__ == "__main__":
    print("=" * 50)
    print("ChromaDB 重建工具")
    print("=" * 50)

    status = chroma_status()
    print(f"\nChromaDB 状态: {'已启用' if status['enabled'] else '未启用'}")
    if not status["enabled"]:
        print(f"原因: {status.get('error', 'chromadb 未安装')}")
        print("退出。")
        exit(1)

    emb_status = embedding_status()
    print(f"Embedding 状态: {'可用' if emb_status['available'] else '不可用'}")

    collections = ["knowledge_base_408", "user_memory_vector", "mistake_summary"]
    for col in collections:
        start = time.time()
        result = rebuild_collection(col)
        elapsed = int((time.time() - start) * 1000)
        if result["success"]:
            print(f"  [{elapsed}ms] {col}: {result['action']}")
        else:
            print(f"  [{elapsed}ms] {col}: 失败 - {result.get('error')}")

    print("\n重新导入知识库...")
    docs_dir = BASE_DIR.parent / "knowledge_docs"
    if docs_dir.exists():
        r = import_knowledge_from_docs()
        print(f"  Markdown 文档: 成功 {r['imported']}, 失败 {r['failed']}")
    else:
        print(f"  知识库文档目录不存在: {docs_dir}")
        r = import_knowledge_from_db()
        print(f"  数据库导入: 成功 {r['imported']}, 失败 {r['failed']}")

    print("\n重建完成。")
