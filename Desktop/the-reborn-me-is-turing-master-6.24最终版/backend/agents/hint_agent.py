from __future__ import annotations

import time
from typing import Literal

from agents.graph_utils import _make_step
from services.llm_service import chat_completion


MASTERY_MODE: dict[str, dict] = {
    "薄弱点": {
        "mode": "detailed",
        "label": "详细引导",
        "instruction": "用户对该知识点掌握薄弱，请给出非常详细的分步引导提示，每步一个 <br> 换行，先提示关键公式或规则，再引导推导过程。",
    },
    "不熟": {
        "mode": "moderate",
        "label": "适中提示",
        "instruction": "用户对该知识点不够熟练，请给出中等详细度的提示，指出关键思路和易错点，避免直接给出答案。",
    },
    "不会": {
        "mode": "teaching",
        "label": "教学模式",
        "instruction": "用户对该知识点完全不会或未学，请以教学方式给出提示：先解释核心概念和原理，再分步骤引导解题思路。",
    },
    "未学": {
        "mode": "teaching",
        "label": "教学模式",
        "instruction": "用户对该知识点未学习，请以教学方式给出提示：先解释核心概念和原理，再分步骤引导解题思路。",
    },
    "掌握": {
        "mode": "verification",
        "label": "验证模式",
        "instruction": "用户对该知识点已掌握，请仅给出方向性验证提示（如「注意检查边界条件」），无需详细解释。",
    },
}

_DEFAULT_MODE = MASTERY_MODE["不熟"]


def generate_hints(
    mastery_status: str,
    subject: str,
    knowledge_point: str,
    question_text: str,
    standard_answer: str = "",
    explanation: str = "",
) -> dict:
    """根据掌握度生成渐进式答题提示。

    Args:
        mastery_status: 掌握状态（薄弱点/不熟/不会/未学/掌握）。
        subject: 科目。
        knowledge_point: 知识点。
        question_text: 题目文本。
        standard_answer: 标准答案。
        explanation: 解析文本。

    Returns:
        dict: 包含 mode, hints, agent_steps, llm_used, llm_error。
    """
    steps: list[dict] = []
    start = time.time()

    mode_config = MASTERY_MODE.get(mastery_status, _DEFAULT_MODE)
    mode_label = mode_config["label"]
    instruction = mode_config["instruction"]

    steps.append(_make_step("identify_mode", f"mastery={mastery_status}", f"mode={mode_label}", "success", start))

    fallback_hints: list[str] = []
    if mastery_status in ("薄弱点",):
        fallback_hints = [
            f"先回忆 {knowledge_point} 的核心定义和公式。",
            f"写出 {knowledge_point} 的关键步骤或规则。",
            "带入题目条件，逐条核对每一步。",
            "检查边界条件和特殊情况。",
            f"{explanation[:80] if explanation else '参考答案见解析。'}",
        ]
    elif mastery_status in ("不会", "未学"):
        fallback_hints = [
            f"{knowledge_point} 是 {subject} 中的重要知识点。",
            f"先理解 {knowledge_point} 的基本概念：{explanation[:100] if explanation else '请回顾教材对应章节。'}",
            "按照「定义 → 规则 → 示例」的顺序逐步理解。",
            f"题目涉及的知识点：{question_text[:80]}...",
            "建议先复习知识点再做本题。",
        ]
    elif mastery_status == "掌握":
        fallback_hints = [
            "验证你的推导过程。",
            "注意边界条件和特例。",
            f"确认答案符合 {knowledge_point} 的规则。",
        ]
    else:
        fallback_hints = [
            f"关于 {knowledge_point}，关键思路是什么？",
            "注意题目中的陷阱和易错点。",
            "带着思路再做一次推导验证。",
        ]

    t2 = time.time()
    llm = chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "你是考研 408 智能提示 Agent。根据学生掌握度返回恰当详细的提示。"
                    "不打分，不直接给答案，只给引导。使用简单 HTML 格式。"
                ),
            },
            {
                "role": "user",
                "content": f"""
掌握度：{mastery_status}（{mode_label}）
科目：{subject}
知识点：{knowledge_point}
题目：{question_text}
标准答案：{standard_answer or '暂缺'}
解析：{explanation or '暂缺'}

要求：{instruction}

请给出 3-5 条渐进式提示，用 <br> 分隔。
""",
            },
        ],
        "<br>".join(fallback_hints),
    )

    hint_text = llm.content.replace("\n", "<br>")
    hints = [h.strip() for h in hint_text.split("<br>") if h.strip()]
    if not hints:
        hints = fallback_hints

    t3 = time.time()
    step_status = "success" if llm.used_llm else "degraded"
    steps.append(_make_step("generate_hints", f"LLM={llm.used_llm}", f"{len(hints)} hints, mode={mode_label}", step_status, t2))

    return {
        "mode": mode_label,
        "hints": hints,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": steps,
        "duration_ms": int((time.time() - start) * 1000),
    }
