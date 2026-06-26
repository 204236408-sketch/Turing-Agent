from __future__ import annotations

from pathlib import Path
from typing import Any


<<<<<<< HEAD
COLLECTIONS = ["knowledge_base_408", "user_memory_vector", "mistake_summary"]
=======
COLLECTIONS = ["knowledge_base_408", "user_memory_vector", "mistake_summary", "seed_questions_vector"]
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)


from chromadb import EmbeddingFunction, Embeddings

class _ChromaEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        from services.vector_embedding_service import get_embedding_service
        self._svc = get_embedding_service()

    def __call__(self, input: list[str]) -> Embeddings:
        result = self._svc.embed_texts(input)
        if result["success"]:
            return result["embeddings"]
        raise RuntimeError(f"embedding failed: {result.get('error')}")

    @staticmethod
    def name() -> str:
        return "siliconflow_bge_zh"

    @staticmethod
    def build_from_config(config: dict) -> "_ChromaEmbeddingFunction":
        return _ChromaEmbeddingFunction()

    def get_config(self) -> dict:
        return {"backend": "siliconflow", "model": "BAAI/bge-large-zh-v1.5"}


class ChromaService:
    def __init__(self, persist_path: str) -> None:
        self._path = Path(persist_path)
        self._client: Any = None
        self._enabled = False
        self._import_error = ""
        self._init()

    def _init(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings

            self._path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self._path),
                settings=Settings(anonymized_telemetry=False),
            )
            self._enabled = True
            self._import_error = ""
        except ImportError as e:
            self._import_error = str(e)
            self._enabled = False
            self._client = None
        except Exception as e:
            self._import_error = str(e)
            self._enabled = False
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def client(self) -> Any | None:
        return self._client

    def status(self) -> dict:
        return {
            "enabled": self._enabled,
            "mode": "chromadb" if self._enabled else "disabled",
            "path": str(self._path),
            "error": self._import_error if not self._enabled else "",
            "collections": self._list_collections(),
        }

    def _list_collections(self) -> list[str]:
        if not self._enabled or self._client is None:
            return []
        try:
            return [c.name for c in self._client.list_collections()]
        except Exception:
            return []

    def get_or_create_collection(self, name: str) -> Any | None:
        if not self._enabled or self._client is None:
            return None
        try:
<<<<<<< HEAD
            if name == "knowledge_base_408":
=======
            if name in ("knowledge_base_408", "seed_questions_vector"):
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
                ef = _ChromaEmbeddingFunction()
                return self._client.get_or_create_collection(name, embedding_function=ef)
            return self._client.get_or_create_collection(name)
        except Exception:
            return None

    def upsert(
        self, collection: str, document_id: str, text: str, metadata: dict | None = None
    ) -> dict:
        if not self._enabled or self._client is None:
            return {
                "collection": collection,
                "document_id": document_id,
                "stored": False,
                "error": "chromadb not enabled",
                "preview": text[:120],
            }
        try:
            coll = self.get_or_create_collection(collection)
            if coll is None:
                return {
                    "collection": collection,
                    "document_id": document_id,
                    "stored": False,
                    "error": "failed to get collection",
                    "preview": text[:120],
                }
            coll.upsert(
                ids=[document_id],
                documents=[text],
                metadatas=[metadata or {}],
            )
            return {
                "collection": collection,
                "document_id": document_id,
                "stored": True,
                "error": "",
                "preview": text[:120],
            }
        except Exception as e:
            return {
                "collection": collection,
                "document_id": document_id,
                "stored": False,
                "error": str(e),
                "preview": text[:120],
            }

    def query(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        where: dict | None = None,
    ) -> dict:
        if not self._enabled or self._client is None:
            return {
                "collection": collection,
                "items": [],
                "fallback": True,
                "error": "chromadb not enabled",
            }
        try:
            coll = self.get_or_create_collection(collection)
            if coll is None:
                return {
                    "collection": collection,
                    "items": [],
                    "fallback": True,
                    "error": "failed to get collection",
                }
            kwargs: dict[str, Any] = {"n_results": limit}
            if where:
                kwargs["where"] = where
            result = coll.query(query_texts=[query], **kwargs)
            items = []
            if result["ids"] and result["ids"][0]:
                for i, doc_id in enumerate(result["ids"][0]):
                    doc = result["documents"][0][i] if result["documents"] else ""
                    meta = result["metadatas"][0][i] if result["metadatas"] else {}
                    distance = result["distances"][0][i] if result["distances"] else 0.0
                    items.append({
                        "id": doc_id,
                        "text": doc,
                        "metadata": meta,
                        "score": 1.0 - distance,
                    })
            return {
                "collection": collection,
                "items": items,
                "fallback": False,
                "error": "",
            }
        except Exception as e:
            return {
                "collection": collection,
                "items": [],
                "fallback": True,
                "error": str(e),
            }

    def delete_collection(self, name: str) -> dict:
        if not self._enabled or self._client is None:
            return {
                "collection": name,
                "deleted": False,
                "error": "chromadb not enabled",
            }
        try:
            self._client.delete_collection(name)
            return {"collection": name, "deleted": True, "error": ""}
        except Exception as e:
            return {"collection": name, "deleted": False, "error": str(e)}


# ---- Module-level singleton (for backward compat & scripts) ----
from config import settings

_service: ChromaService | None = None


def _get_service() -> ChromaService:
    global _service
    if _service is None:
        _service = ChromaService(settings.chroma_path)
    return _service


def chroma_status() -> dict:
    return _get_service().status()


def get_client():
    return _get_service().client


def get_or_create_collection(name: str):
    return _get_service().get_or_create_collection(name)


def upsert_document(
    collection: str, document_id: str, text: str, metadata: dict | None = None
) -> dict:
    return _get_service().upsert(collection, document_id, text, metadata)


def query_documents(
    collection: str,
    query: str,
    limit: int = 5,
    where: dict | None = None,
) -> dict:
    return _get_service().query(collection, query, limit, where)


def delete_collection(name: str) -> dict:
    return _get_service().delete_collection(name)
