from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from config import settings


class EmbeddingBackend:
    name: str = ""
    available: bool = False
    error: str = ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class SiliconFlowEmbedding(EmbeddingBackend):
    name = "siliconflow"

    def __init__(self):
        self.available = bool(settings.siliconflow_api_key.strip())
        self.error = "" if self.available else "SILICONFLOW_API_KEY not configured"
        self.model = "BAAI/bge-large-zh-v1.5"
        self.base_url = settings.siliconflow_base_url.rstrip("/")

    def embed(self, texts: list[str]) -> list[list[float]]:
        texts = [self._truncate(t) for t in texts]
        body = json.dumps({
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/embeddings",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        result = payload.get("data", [])
        result.sort(key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in result]

    @staticmethod
    def _truncate(text: str, max_chars: int = 600) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n...(truncated)"


class ChromaDefaultEmbedding(EmbeddingBackend):
    name = "chroma_default"

    def __init__(self):
        try:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self._fn = DefaultEmbeddingFunction()
            self.available = True
            self.error = ""
        except Exception as e:
            self._fn = None
            self.available = False
            self.error = str(e)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._fn is None:
            raise RuntimeError("chroma default embedding not available")
        return self._fn(texts)


class EmbeddingService:
    def __init__(self):
        self._backends: list[EmbeddingBackend] = [
            SiliconFlowEmbedding(),
            ChromaDefaultEmbedding(),
        ]
        self._active: EmbeddingBackend | None = None
        self._init()

    def _init(self):
        for backend in self._backends:
            if backend.available:
                self._active = backend
                return
        self._active = None

    @property
    def active(self) -> EmbeddingBackend | None:
        return self._active

    def embed_texts(self, texts: list[str]) -> dict:
        if self._active is None:
            return {"success": False, "embeddings": [], "fallback": True, "error": "no embedding backend available"}
        try:
            embeddings = self._active.embed(texts)
            return {"success": True, "embeddings": embeddings, "fallback": False, "error": "", "backend": self._active.name}
        except Exception as e:
            return {"success": False, "embeddings": [], "fallback": True, "error": str(e)}

    def status(self) -> dict:
        backends = [{"name": b.name, "available": b.available, "error": b.error} for b in self._backends]
        return {
            "available": self._active is not None,
            "active_backend": self._active.name if self._active else "",
            "backends": backends,
        }

    @property
    def dimension(self) -> int:
        if isinstance(self._active, SiliconFlowEmbedding):
            return 1024
        return 384


_service = EmbeddingService()


def embed_texts(texts: list[str]) -> dict:
    return _service.embed_texts(texts)


def embedding_status() -> dict:
    return _service.status()


def get_embedding_service() -> EmbeddingService:
    return _service
