import json
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request
from config import settings


@dataclass
class LLMResult:
    content: str
    used_llm: bool
    error: str = ""
    data: Any = None


def chat_completion(messages: list[dict], fallback: str, temperature: float = 0.3, model: str | None = None, max_tokens: int = 1600) -> LLMResult:
    if not settings.llm_enabled:
        return LLMResult(content=fallback, used_llm=False, error="SILICONFLOW_API_KEY 未配置")
    try:
        selected_model = model or settings.siliconflow_model
        body = json.dumps(
            {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        req = request.Request(
            f"{settings.siliconflow_base_url.rstrip('/')}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=settings.llm_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = (payload["choices"][0]["message"].get("content") or "").strip()
        if not content:
            return LLMResult(content=fallback, used_llm=False, error="AI 返回空内容，已使用保底回答", data=payload)
        return LLMResult(content=content, used_llm=True, data={"raw": payload, "model": selected_model})
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return LLMResult(content=fallback, used_llm=False, error=f"HTTP {exc.code}: {detail}")
    except Exception as exc:
        return LLMResult(content=fallback, used_llm=False, error=str(exc))


def chat_json(messages: list[dict], fallback: dict, temperature: float = 0.2, model: str | None = None, max_tokens: int = 1600) -> LLMResult:
    result = chat_completion(messages, json.dumps(fallback, ensure_ascii=False), temperature, model=model, max_tokens=max_tokens)
    if not result.used_llm:
        result.data = fallback
        return result
    try:
        model_name = result.data.get("model", "") if isinstance(result.data, dict) else ""
        parsed = extract_json(result.content)
        if isinstance(parsed, dict) and model_name:
            parsed["_llm_model"] = model_name
        result.data = parsed
        return result
    except Exception as exc:
        result.used_llm = False
        result.error = f"AI 返回内容不是合法 JSON：{exc}"
        result.data = fallback
        result.content = json.dumps(fallback, ensure_ascii=False)
        return result


def chat_json_with_fallback_models(
    messages: list[dict],
    fallback: dict,
    models: list[str],
    temperature: float = 0.2,
    max_tokens: int = 1600,
) -> LLMResult:
    errors: list[str] = []
    for model in models:
        result = chat_json(messages, fallback, temperature=temperature, model=model, max_tokens=max_tokens)
        if result.used_llm:
            return result
        errors.append(f"{model}: {result.error}")
    result = LLMResult(
        content=json.dumps(fallback, ensure_ascii=False),
        used_llm=False,
        error="; ".join(errors),
        data=fallback,
    )
    return result


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.S)
    if fence:
        cleaned = fence.group(1).strip()
    if not cleaned.startswith(("{", "[")):
        start_candidates = [pos for pos in [cleaned.find("{"), cleaned.find("[")] if pos >= 0]
        if not start_candidates:
            raise ValueError("未找到 JSON 起始位置")
        cleaned = cleaned[min(start_candidates):]
    return json.loads(cleaned)
