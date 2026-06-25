from __future__ import annotations

import time

from agents.graph_utils import _make_step
from services.llm_service import chat_completion


def ai_answer_for_post(
    title: str,
    content: str,
    subject: str,
    knowledge_point: str = "",
    author_profile: dict | None = None,
) -> dict:
    """为论坛帖子生成 AI 个性化回答。

    Args:
        title: 帖子标题。
        content: 帖子内容。
        subject: 科目。
        knowledge_point: 知识点。
        author_profile: 发帖人学习画像（掌握度、近期记忆、常见错因）。

    Returns:
        dict: 包含 answer, agent_steps, llm_used, llm_error。
    """
    steps: list[dict] = []
    start = time.time()

    point = knowledge_point or subject
    steps.append(_make_step("parse_post", f"subject={subject}, kp={point}", f"title='{title[:30]}'", "success", start))

    profile_section = ""
    if author_profile:
        mastery = author_profile.get("mastery_status", "")
        memories = author_profile.get("recent_memories", [])
        common_errors = author_profile.get("common_errors", [])
        memory_text = "；".join([m.get("content", "")[:40] for m in memories[:3]])
        error_text = "、".join(common_errors[:3])
        if mastery or memory_text or error_text:
            profile_section = f"""
发帖人学习画像：
- 掌握度：{mastery or '未知'}
- 近期记忆：{memory_text or '无'}
- 常见错因：{error_text or '无'}

请结合发帖人的学习情况，给出个性化回答。若发帖人掌握度低，请更详细解释。"""

    fallback = (
        f"<p><b>问题定位：</b>{subject} · {point}。</p>"
        f'<p><b>建议：</b>先把帖子中的困惑拆成「概念定义、执行流程、边界条件」三块，再用一道同类题验证。</p>'
        f"<p><b>针对帖子：</b>{title} 的核心不是记结论，而是把每一步状态变化写出来。</p>"
    )

    t2 = time.time()
    llm = chat_completion(
        [
            {"role": "system", "content": "你是考研 408 学习论坛 AI 小助手，回答要友好、具体、可执行，可使用简单 HTML。"},
            {
                "role": "user",
                "content": f"帖子标题：{title}\n帖子内容：{content}\n科目：{subject}\n知识点：{point}\n{profile_section}\n请给出论坛回复。",
            },
        ],
        fallback,
    )

    step_status = "success" if llm.used_llm else "degraded"
    steps.append(_make_step("generate_answer", f"LLM={llm.used_llm}", f"answer_len={len(llm.content)}", step_status, t2))

    return {
        "answer": llm.content.replace("\n", "<br>"),
        "agent_steps": steps,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
    }
