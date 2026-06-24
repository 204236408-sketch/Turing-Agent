import json
from sqlalchemy.orm import Session
from models import Question, QuestionGenerationSession
from services.llm_service import chat_json
from services.serialization import question_to_dict


CHOICE_FALLBACK = [
    {
        "question_text": "某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？",
        "options": ["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"],
        "standard_answer": "C",
        "explanation": "命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。",
        "hints": ["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"],
    },
]


def _to_variant_type(question_type: str) -> str:
    mapping = {
        "选择题": "choice", "填空题": "fill", "简答题": "essay", "综合题": "comprehensive",
        "choice": "choice", "fill": "fill", "essay": "essay", "comprehensive": "comprehensive",
    }
    return mapping.get(question_type, "choice")


def _prompt_schema_for(vt: str) -> str:
    if vt == "fill":
        return """{
  "questions": [
    {
      "question_text": "题干",
      "standard_answer": "标准答案文本",
      "explanation": "解析",
      "hints": ["提示1", "提示2"]
    }
  ]
}"""
    if vt == "essay":
        return """{
  "questions": [
    {
      "question_text": "题干",
      "standard_answer": "标准答案要点",
      "explanation": "解析",
      "hints": ["提示1", "提示2"]
    }
  ]
}"""
    if vt == "comprehensive":
        return """{
  "questions": [
    {
      "question_text": "综合题干",
      "sub_questions": [
        {"title": "第 1 问", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "standard_answer": "A"},
        {"title": "第 2 问", "standard_answer": "答案文本"}
      ],
      "explanation": "解析",
      "hints": ["提示1", "提示2"]
    }
  ]
}"""
    return """{
  "questions": [
    {
      "question_text": "题干",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "standard_answer": "A",
      "explanation": "解析",
      "hints": ["提示1", "提示2"]
    }
  ]
}"""


def _build_fallback(vt: str, subject: str, knowledge_point: str, count: int) -> list[dict]:
    base = CHOICE_FALLBACK.copy()
    if vt == "fill":
        return [
            {
                "question_text": f"【{subject} · {knowledge_point}】请填空：{knowledge_point} 的核心定义是什么？",
                "standard_answer": f"{knowledge_point} 的标准定义（根据教材）",
                "explanation": f"本题考查 {knowledge_point} 的概念理解，需完整表述。",
                "hints": ["先回忆教材定义。", "注意关键词不能遗漏。"],
            } for _ in range(count)
        ]
    if vt == "essay":
        return [
            {
                "question_text": f"【{subject} · {knowledge_point}】请简要分析 {knowledge_point} 在 408 中的考查方式。",
                "standard_answer": f"{knowledge_point} 通常考查：概念理解、过程推导、边界条件辨析。",
                "explanation": f"408 对 {knowledge_point} 的考查兼顾定义理解和应用能力。",
                "hints": ["从概念、过程和边界三个维度回答。", "结合一道典型题目说明。"],
            } for _ in range(count)
        ]
    if vt == "comprehensive":
        return [
            {
                "question_text": f"【{subject} · {knowledge_point}】综合题",
                "sub_questions": [
                    {"title": f"简述 {knowledge_point} 的基本概念。", "standard_answer": f"{knowledge_point} 是 {subject} 中的重要知识点。"},
                    {"title": f"在实际题目中，{knowledge_point} 的常见考法有哪些？", "options": ["A. 概念辨析", "B. 过程计算", "C. 边界条件", "D. 以上都是"], "standard_answer": "D"},
                ],
                "explanation": f"综合题考查 {knowledge_point} 的多角度理解。",
                "hints": ["先回答概念部分。", "再分析具体应用。"],
            } for _ in range(count)
        ]
    stem = f"关于「{knowledge_point}」的下列说法，哪一项最符合 408 考纲要求？"
    return [
        {
            "question_text": stem,
            "options": [
                f"A. 只需记忆 {knowledge_point} 的结论，不必理解过程",
                f"B. 应结合定义、关键步骤和边界条件理解 {knowledge_point}",
                f"C. {knowledge_point} 不属于 {subject} 的考试范围",
                "D. 所有题目都可以忽略初始状态",
            ],
            "standard_answer": "B",
            "explanation": f"{knowledge_point} 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。",
            "hints": [f"先回忆 {knowledge_point} 的核心定义。", "再检查选项是否忽略过程或边界条件。"],
        } for _ in range(count)
    ]


def generate_questions(
    db: Session,
    user_id: int,
    mode: str,
    subject: str,
    knowledge_point: str,
    difficulty: str,
    question_type: str,
    count: int,
    recommendation_reason: str = "",
) -> dict:
    vt = _to_variant_type(question_type)
    fallback = {"questions": _build_fallback(vt, subject, knowledge_point, count)}
    llm = chat_json(
        [
            {
                "role": "system",
                "content": "你是考研 408 智能出题 Agent。只输出合法 JSON，不要 Markdown，不要解释。",
            },
            {
                "role": "user",
                "content": f"""
请生成 {count} 道考研 408 {question_type}。
科目：{subject}
知识点：{knowledge_point}
难度：{difficulty}
生成模式：{mode}

JSON 格式必须严格如下：
{_prompt_schema_for(vt)}
""",
            },
        ],
        fallback,
    )
    raw_questions = (llm.data or fallback).get("questions") or fallback["questions"]
    raw_questions = raw_questions[:count]
    if llm.used_llm and not _questions_match_target(raw_questions, subject, knowledge_point):
        llm.used_llm = False
        llm.error = "AI 题目与指定科目/知识点不匹配，已自动降级为本地保底题。"
        raw_questions = fallback["questions"][:count]
    if vt in ("fill", "essay"):
        for item in raw_questions:
            item.pop("options", None)
            ans = item.get("standard_answer", "").strip()
            if len(ans) == 1 and 'A' <= ans <= 'Z':
                item["standard_answer"] = item.get("explanation", ans)
    elif vt == "comprehensive":
        for item in raw_questions:
            item.pop("options", None)
    is_smart = mode != "自由选择"
    session = QuestionGenerationSession(
        user_id=user_id,
        generation_mode="smart" if is_smart else "manual",
        recommend_mode=mode if is_smart else "",
        subject=subject,
        knowledge_point=knowledge_point,
        difficulty=difficulty,
        question_type=question_type,
        question_count=count,
        reason=recommendation_reason or f"{mode}：围绕 {subject} / {knowledge_point} 生成 {count} 道 {difficulty} {question_type}。",
    )
    db.add(session)
    db.flush()
    questions = []
    for idx, item in enumerate(raw_questions):
        sub_qs = json.dumps(item.get("sub_questions") or [], ensure_ascii=False) if vt == "comprehensive" else "[]"
        question = Question(
            session_id=session.id,
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            question_type=question_type,
            variant_type=vt,
            question_text=_with_target_prefix(
                item.get("question_text") or fallback["questions"][idx % len(fallback["questions"])]["question_text"],
                subject,
                knowledge_point,
            ),
            options_json=json.dumps(item.get("options") or [], ensure_ascii=False),
            sub_questions_json=sub_qs,
            standard_answer=(item.get("standard_answer") or "").strip(),
            explanation=item.get("explanation") or "解析暂缺。",
            hints_json=json.dumps(item.get("hints") or ["先定位知识点。", "再按步骤推导。"], ensure_ascii=False),
            recommend_reason=session.reason,
            source="llm" if llm.used_llm else "agent_fallback",
        )
        db.add(question)
        db.flush()
        questions.append(question_to_dict(question))
    return {
        "session_id": session.id,
        "config": session.reason,
        "questions": questions,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
    }


def _with_target_prefix(text: str, subject: str, knowledge_point: str) -> str:
    prefix = f"【{subject} · {knowledge_point}】"
    return text if text.startswith(prefix) else f"{prefix}{text}"


def _questions_match_target(items: list[dict], subject: str, knowledge_point: str) -> bool:
    if not items:
        return False
    target_keywords = {subject, knowledge_point}
    if knowledge_point == "页面置换算法":
        target_keywords.update({"页面", "置换", "缺页", "LRU", "FIFO", "OPT", "Clock"})
    if knowledge_point == "传输层":
        target_keywords.update({"TCP", "UDP", "传输层", "握手", "挥手"})
    if knowledge_point == "树与二叉树":
        target_keywords.update({"树", "二叉树", "遍历", "前序", "中序", "后序"})
    text = "\n".join(str(item.get("question_text", "")) for item in items)
    return any(keyword and keyword in text for keyword in target_keywords)
