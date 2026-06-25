from __future__ import annotations

import json
import time

from agents.graph_utils import _make_step
from prompts.plan_prompt import PLAN_PROMPT
from services.llm_service import chat_json


def generate_daily_plan(
    recent_answers: list[dict],
    recent_mistakes: list[dict],
    recent_memories: list[dict],
    weak_points: list[dict] | None = None,
) -> dict:
    """生成个性化每日学习计划。

    Args:
        recent_answers: 近期答题记录。
        recent_mistakes: 近期错题记录。
        recent_memories: 近期长期记忆。
        weak_points: 薄弱知识点列表。

    Returns:
        dict: 包含 plan, agent_steps, llm_used, llm_error。
    """
    steps: list[dict] = []
    start = time.time()

    weak_points = weak_points or []
    weak_text = "；".join([f"{w.get('subject','')}/{w.get('knowledge_point','')}(weak={w.get('weak_score',0)})" for w in weak_points[:3]])
    answer_text = "；".join([f"{a.get('subject','')}/{a.get('knowledge_point','')}({'对' if a.get('is_correct') else '错'})" for a in recent_answers[:5]])
    mistake_text = "；".join([f"{m.get('subject','')}/{m.get('knowledge_point','')}({m.get('error_type','')})" for m in recent_mistakes[:3]])
    memory_text = "；".join([m.get("content", "")[:30] for m in recent_memories[:3]])

    steps.append(_make_step("collect_data",
        f"answers={len(recent_answers)}, mistakes={len(recent_mistakes)}, memories={len(recent_memories)}",
        "data collected", "success", start))

    prompt = PLAN_PROMPT.format(
        recent_answers=answer_text or "暂无答题记录",
        recent_mistakes=mistake_text or "暂无错题记录",
        long_term_memories=memory_text or "暂无长期记忆",
        weak_points=weak_text or "暂无薄弱点数据",
    )

    fallback = {
        "plan": [
            {
                "step": 1, "subject": "操作系统", "knowledge_point": "页面置换算法",
                "action": "专项练习", "count": 3, "difficulty": "中等",
                "estimated_minutes": 25, "reason": "根据你的学习情况推荐",
            },
            {
                "step": 2, "subject": "计算机网络", "knowledge_point": "传输层",
                "action": "知识点复习", "count": 5, "difficulty": "简单",
                "estimated_minutes": 20, "reason": "巩固基础概念",
            },
        ],
    }

    t2 = time.time()
    llm = chat_json(
        [{"role": "user", "content": prompt}],
        fallback,
    )

    data = llm.data if isinstance(llm.data, dict) else fallback
    plan = data.get("plan", fallback["plan"])
    step_status = "success" if llm.used_llm else "degraded"
    steps.append(_make_step("generate_plan", f"LLM={llm.used_llm}", f"{len(plan)} steps generated", step_status, t2))

    return {
        "plan": plan,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": steps,
        "duration_ms": int((time.time() - start) * 1000),
    }
