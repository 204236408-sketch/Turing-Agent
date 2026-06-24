from pathlib import Path
from config import settings


def chroma_status() -> dict:
    path = Path(settings.chroma_path)
    path.mkdir(parents=True, exist_ok=True)
    return {
        "enabled": False,
        "mode": "local-placeholder",
        "path": str(path),
        "message": "开发版使用轻量本地检索；安装 chromadb 后可替换为真实向量库。",
    }


def upsert_document(collection: str, document_id: str, text: str, metadata: dict | None = None) -> dict:
    return {
        "collection": collection,
        "document_id": document_id,
        "stored": False,
        "metadata": metadata or {},
        "preview": text[:120],
    }
