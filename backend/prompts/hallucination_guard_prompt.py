"""LLM 自检 prompt：对生成的题目做事实正确性审查

策略：用 LLM 自身当 judge，但严格约束：
1. 只能基于【知识库参考资料】判断
2. 强制结构化输出（pass / fail + 原因 + kb_ref）
3. 不可决断的标 uncertain，让系统降级
"""

SELF_CHECK_PROMPT = """
# 任务
你是 408 考研题目质检员。下面是一道刚被 LLM 生成的选择题/填空题/简答题/综合题，以及对应的【知识库参考资料】。你的唯一工作是**对照知识库原文**，判断题目中的事实性陈述（定义、公式、协议号、时序、流程）是否都能在知识库中找到依据。

# 题目
{question_json}

# 【知识库参考资料】（事实判断的唯一来源）
{kb_context}

# 评估维度（每一项必须独立判断）
1. **题干事实**：题干涉及的每个概念/数据/参数是否都能在知识库找到原文或合理推论？
2. **答案正确性**：standard_answer 是不是唯一正确选项？其他选项是否真为错误（而不是也正确）？
3. **解析溯源**：explanation 开头是否声明了 kb_ref？所述推理过程是否在知识库覆盖的范围内？
4. **难度匹配**：题目难度是否符合用户指定的等级？（简单：单概念；中等：2 概念 4 步内；较难：3 概念 6 步内；困难：综合）
5. **题型结构**：是否符合指定题型的格式要求（选择题是否 4 选项、填空题是否有空、简答是否分点等）？

# 输出格式（严格 JSON，禁止任何额外文字）
{{
  "verdict": "pass" | "fail" | "uncertain",
  "issues": [
    {{
      "dimension": "题干事实" | "答案正确性" | "解析溯源" | "难度匹配" | "题型结构",
      "severity": "blocker" | "minor",
      "description": "具体问题描述（不超过 50 字）"
    }}
  ],
  "suggestion": "如果 fail，给出最小修改建议（不超过 80 字）；pass/uncertain 时为空字符串"
}}
"""


def render_self_check_prompt(question_json: str, kb_context: str) -> str:
    """组装自检 prompt。"""
    return SELF_CHECK_PROMPT.format(
        question_json=question_json,
        kb_context=kb_context or "（无知识库片段，无法判断，标 uncertain）",
    )
