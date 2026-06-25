from __future__ import annotations

import json
import time

from agents.graph_utils import _make_step
from prompts.summary_prompt import SUMMARY_PROMPT
from services.llm_service import chat_json


def generate_conversation_summary(messages: list[dict]) -> dict:
    """生成会话摘要、标题和追问建议。

    Args:
        messages: 会话消息列表，每项含 role/content。

    Returns:
        dict: 包含 title, summary, followup_suggestions, agent_steps, llm_used, llm_error。
    """
    steps: list[dict] = []

    start = time.time()
    if not messages:
        steps.append(_make_step("validate_input", "0 messages", "empty input", "warning", start))
        return {
            "title": "空白会话",
            "summary": "",
            "followup_suggestions": ["开始 408 学习提问吧"],
            "llm_used": False,
            "llm_error": "",
            "agent_steps": steps,
            "duration_ms": 0,
        }

    steps.append(_make_step("validate_input", f"{len(messages)} messages", "input ok", "success", start))

    messages_json = json.dumps(messages[-8:], ensure_ascii=False)
    prompt = SUMMARY_PROMPT.format(messages=messages_json)

    fallback = {"title": "408 问答", "summary": "用户咨询了 408 相关问题", "followup_suggestions": ["深入讲解该知识点", "推荐相关练习题", "分析常见易错点"]}

    t2 = time.time()
    llm = chat_json(
        [{"role": "user", "content": prompt}],
        fallback,
    )

    data = llm.data if isinstance(llm.data, dict) else fallback
    step_status = "success" if llm.used_llm else "degraded"
    steps.append(_make_step("generate_summary", f"LLM={llm.used_llm}", f"title='{data.get('title','')[:20]}'", step_status, t2))

    return {
        "title": data.get("title", fallback["title"]),
        "summary": data.get("summary", fallback["summary"]),
        "followup_suggestions": data.get("followup_suggestions", fallback["followup_suggestions"]),
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": steps,
        "duration_ms": int((time.time() - start) * 1000),
    }
