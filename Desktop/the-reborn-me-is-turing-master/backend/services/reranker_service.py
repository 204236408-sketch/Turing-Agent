from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from config import settings


class RerankerService:
    def __init__(self):
        self.available = bool(settings.siliconflow_api_key.strip())
        self.error = "" if self.available else "SILICONFLOW_API_KEY not configured"
        self.model = "BAAI/bge-reranker-v2-m3"
        self.base_url = settings.siliconflow_base_url.rstrip("/")

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        if not self.available or not documents:
            return documents

        texts = [d.get("content", d.get("text", "")) for d in documents]
        docs_with_idx = list(enumerate(documents))

        try:
            scored = self._call_rerank_api(query, texts)
            for rank_item, (orig_idx, _) in zip(scored, docs_with_idx):
                documents[orig_idx]["rerank_score"] = rank_item.get("relevance_score", 0.0)
                documents[orig_idx]["rerank_index"] = rank_item.get("index", 0)
        except Exception as e:
            for d in documents:
                d["rerank_score"] = d.get("score", 0.0)
            return documents

        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        if score_threshold is not None:
            documents = [d for d in documents if d.get("rerank_score", 0) >= score_threshold]

        if top_k is not None:
            documents = documents[:top_k]

        return documents

    def _call_rerank_api(self, query: str, documents: list[str]) -> list[dict]:
        body = json.dumps({
            "model": self.model,
            "query": query,
            "documents": documents,
        }).encode("utf-8")

        req = request.Request(
            f"{self.base_url}/rerank",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code}: {body_text}")

        results = payload.get("results", [])
        results.sort(key=lambda x: x.get("index", 0))
        return results

    def status(self) -> dict:
        return {
            "available": self.available,
            "error": self.error,
            "model": self.model,
        }


_service = RerankerService()


def rerank(
    query: str,
    documents: list[dict],
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[dict]:
    return _service.rerank(query, documents, top_k, score_threshold)


def reranker_status() -> dict:
    return _service.status()
