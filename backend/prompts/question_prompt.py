"""408 智能出题 prompt 模板

设计原则（针对 LLM 幻觉的工程化约束）：
1. **知识库绑定**：所有事实必须从 {kb_context} 抽取，禁止外推
2. **溯源必填**：explanation 必须含知识库片段编号（kb_ref），让下游能验证
3. **结构化输出**：字段少而精，1:1 对应 Question 表实际存储
4. **题型模板化**：不同题型给不同 JSON 模板，避免 LLM 自由发挥
5. **难度量化**：用具体指标（计算步数/跨章节数）描述难度，避免主观
6. **拒绝出题信号**：当 kb_context 为空时，模型应返回 refusal 字段
"""

# 难度量化指标，让 LLM 自我约束
DIFFICULTY_RUBRIC = {
    "简单": {
        "concept_count": 1,        # 涉及的独立概念数 ≤1
        "calc_steps_max": 2,        # 最大计算步骤数 ≤2
        "cross_section": False,     # 不允许跨小节
    },
    "中等": {
        "concept_count": 2,
        "calc_steps_max": 4,
        "cross_section": True,
    },
    "较难": {
        "concept_count": 3,
        "calc_steps_max": 6,
        "cross_section": True,
    },
    "困难": {
        "concept_count": 4,
        "calc_steps_max": 8,
        "cross_section": True,
    },
}


QUESTION_PROMPT_TEMPLATE = """
# 身份
你是一名 408 考研命题教师。所有题目必须严格对标 408 统考真题，且只能基于下方【知识库参考资料】编写。**未在知识库出现的考点、公式、协议号、器件参数，一律不得出题**。

# 输入参数
科目：{subject}
知识点：{kp_name}
难度：{difficulty}
题型：{q_type}
题目数量：{q_count}
用户本知识点掌握状态：{kp_status}
用户最近错题摘要：{mistake_summary}
智能推荐模式：{recommend_mode}

# 【参考题目】（OCR 错题场景下携带：用户上传照片识别出的原题 + Agent 推断的标准答案）
{reference_block}

# 【知识库参考资料】（这是你出题的唯一事实来源）
{kb_context}

# 强制约束（违反任一条都视为不合格）

## 约束 1：知识库溯源
- 题干/选项/答案/解析中出现的每一个事实（定义、公式、协议号、时序、流程），必须能在【知识库参考资料】中找到对应原文
- 解析（explanation）开头必须写 `kb_ref: [1,2]` 引用 1 个或多个知识库片段编号，未引用视为不合格
- 知识库无相关资料时，**该题在 question_text 写 `__REFUSAL__` 并把 options/standard_answer 留空**，让系统改用备选题

## 约束 2：不得编造
- 不得发明任何协议号（如自造 TCP 选项号）、寄存器名、时序参数、教材未列的公式
- 不得使用"通常""一般认为"等模糊表述作为事实依据
- 跨小节综合题只能引用本知识库已包含的相邻小节概念

## 约束 3：难度量化（基于 {difficulty}）
{difficulty_rubric}
- 若题目的概念数 / 计算步数 / 跨小节数超出上表，视为难度不匹配，必须重写或放弃

## 约束 4：题型结构
{qtype_schema}

## 约束 4.1：选择题选项质量
- options 必须全部是该知识点内部的概念、步骤、公式、条件、编码方式或算法差异，不能出现与知识点无关的元话术
- 禁止使用这些选项模式："仅考查定义背诵"、"只考计算过程"、"只考综合应用"、"仅以选择题形式出现"、"仅以大题形式出现"、"不属于 408 考纲范围"
- 干扰项应来自真实易混点，例如浮点数题应围绕阶码/尾数/移码/规格化/舍入/IEEE754 位段设计，而不是围绕考试题型设计
- OCR 参考题存在时，3 道题必须是同考点变式：至少分别覆盖"概念辨析"、"步骤/流程"、"典型字段或边界条件"三个角度，题干和选项不得三题同构

## 约束 5：错题针对性
- 用户的最近错题摘要（mistake_summary）非空时，至少 1 道题的 easy_mistakes 字段必须直接对应其中一类错因
- 干扰选项必须复刻该错因的"看似合理但实际错误"的逻辑

## 约束 6：去重
- 与【题库参考】中已有题目的考点或解法不要完全重复，可以同考点换问法，但题干关键词重合度应低于 30%

## 约束 7：输出字段严格
仅输出以下字段，**任何额外字段都会被系统丢弃且扣分**：
{qtype_fields}

## 约束 8：JSON 强约束
1. 仅输出纯净 JSON 文本，禁止 ```json / 注释 / 标题 / 解释
2. 顶层固定 key 为 questions，值为题目数组
3. 字段值禁止空字符串、空数组、占位符（如 "TODO"）
4. 标准答案（standard_answer）必须能在题干/选项中直接定位

# 输出模板
{output_template}
"""


# 不同题型的 JSON 字段定义（与 Question 表 / serialization 对齐）
QTYPE_FIELD_SCHEMA = {
    "choice": {
        "fields": ["question_text", "options", "standard_answer", "explanation", "easy_mistakes", "hints"],
        "schema": """- question_text: 完整选择题干
- options: 固定 4 项，["A. ...", "B. ...", "C. ...", "D. ..."]，唯一正确
- standard_answer: 单个字母 "A" | "B" | "C" | "D"
- explanation: 解析，开头写 kb_ref: [片段编号]；不写采分点；说明对错与概念差异
- easy_mistakes: 1-2 句描述本类题考生最常踩的坑（来自 mistake_summary 优先）
- hints: 固定 2 项数组["一级考点定位","二级关键步骤"]，不强制 3 项""",
        "template": """{
  "questions": [
    {
      "question_text": "题干...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "standard_answer": "A",
      "explanation": "kb_ref: [1] ...",
      "easy_mistakes": "易把 X 当成 Y，原因是混淆了 Z 概念。",
      "hints": ["先定位 X 的定义", "再按 Y 步骤推导"]
    }
  ]
}""",
    },
    "fill": {
        "fields": ["question_text", "standard_answer", "explanation", "easy_mistakes", "hints"],
        "schema": """- question_text: 含 1-3 个空（用 ____ 表示）的填空题干
- standard_answer: 填空的标准答案，逗号分隔（"X,Y"）
- explanation: 解析，开头写 kb_ref: [...]；不写采分点
- easy_mistakes: 本类填空易错点
- hints: 2 项数组""",
        "template": """{
  "questions": [
    {
      "question_text": "____ 是 X，____ 是 Y。",
      "standard_answer": "X,Y",
      "explanation": "kb_ref: [1] ...",
      "easy_mistakes": "易写成 Z，原因是没区分 A 与 B。",
      "hints": ["先回忆 X 的定义", "再核对 Y 的条件"]
    }
  ]
}""",
    },
    "essay": {
        "fields": ["question_text", "standard_answer", "explanation", "easy_mistakes", "hints"],
        "schema": """- question_text: 简答题题干
- standard_answer: 分点作答（1. ... \\n2. ...）
- explanation: 解析，开头写 kb_ref: [...]；简答题必须列采分点
- easy_mistakes: 简答漏点
- hints: 2 项数组""",
        "template": """{
  "questions": [
    {
      "question_text": "简述 X 的工作机制。",
      "standard_answer": "1. ...\\n2. ...",
      "explanation": "kb_ref: [1,2] 采分点：第1点2分，第2点3分。",
      "easy_mistakes": "常漏第 2 点，原因是没理解 A 流程。",
      "hints": ["先从概念定义入手", "再按流程/分层回答"]
    }
  ]
}""",
    },
    "comprehensive": {
        "fields": ["question_text", "sub_questions", "explanation", "easy_mistakes", "hints"],
        "schema": """- question_text: 综合题题干（情境描述）
- sub_questions: 子题数组，每项 {title, options?, standard_answer}
- explanation: 解析，开头 kb_ref: [...]；列每问采分点
- easy_mistakes: 综合题易漏的关联点
- hints: 2 项数组""",
        "template": """{
  "questions": [
    {
      "question_text": "情境描述...",
      "sub_questions": [
        {"title": "第1问：...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "standard_answer": "A"},
        {"title": "第2问：...", "standard_answer": "答案文本"}
      ],
      "explanation": "kb_ref: [1] 第1问采分点... 第2问采分点...",
      "easy_mistakes": "第1问易错在混淆 X 与 Y。",
      "hints": ["先把情境抽象为状态变化", "再按子问顺序作答"]
    }
  ]
}""",
    },
}


def render_question_prompt(
    *,
    subject: str,
    knowledge_point: str,
    difficulty: str,
    question_type: str,
    count: int,
    kp_status: str = "暂无掌握度数据",
    mistake_summary: str = "无历史错题",
    recommend_mode: str = "自由选择",
    kb_context: str = "",
    reference_text: str = "",
    reference_answer: str = "",
) -> str:
    """组装出题 prompt（注入知识库片段 + OCR 参考题）。"""
    vt_map = {"选择题": "choice", "填空题": "fill", "简答题": "essay", "综合题": "comprehensive"}
    vt = vt_map.get(question_type, "choice")
    schema_def = QTYPE_FIELD_SCHEMA[vt]

    rubric = DIFFICULTY_RUBRIC.get(difficulty, DIFFICULTY_RUBRIC["中等"])
    difficulty_rubric = (
        f"- 涉及独立概念数 ≤ {rubric['concept_count']}\n"
        f"- 最大计算/推理步数 ≤ {rubric['calc_steps_max']}\n"
        f"- 跨小节综合：{'允许' if rubric['cross_section'] else '不允许'}"
    )

    fields_list = "\n".join(f"- {f}" for f in schema_def["fields"])

    # 拼接参考题目段（仅在 OCR 场景注入；为空则写"无"避免 LLM 误以为有）
    if reference_text or reference_answer:
        ref_lines = []
        if reference_text:
            # 截断到 800 字避免 prompt 过长
            ref_text_trim = reference_text.strip()[:800]
            ref_lines.append(f"原题（OCR 识别）:\n{ref_text_trim}")
        if reference_answer:
            ref_lines.append(f"Agent 推断标准答案（仅作参考，事实以知识库为准）:\n{reference_answer.strip()[:400]}")
        reference_block = "\n\n".join(ref_lines)
    else:
        reference_block = "（无 OCR 参考题）"

    return QUESTION_PROMPT_TEMPLATE.format(
        subject=subject,
        kp_name=knowledge_point,
        difficulty=difficulty,
        q_type=question_type,
        q_count=count,
        kp_status=kp_status,
        mistake_summary=mistake_summary,
        recommend_mode=recommend_mode,
        kb_context=kb_context or "（知识库暂无该知识点内容，请在 question_text 写 __REFUSAL__）",
        difficulty_rubric=difficulty_rubric,
        qtype_schema=schema_def["schema"],
        qtype_fields=fields_list,
        output_template=schema_def["template"],
        reference_block=reference_block,
    )
