from services.llm_service import chat_completion


def ai_answer_for_post(title: str, content: str, subject: str, knowledge_point: str = "") -> dict:
    point = knowledge_point or subject
    fallback = (
        f"<p><b>问题定位：</b>{subject} · {point}。</p>"
        f"<p><b>建议：</b>先把帖子中的困惑拆成“概念定义、执行流程、边界条件”三块，再用一道同类题验证。</p>"
        f"<p><b>针对帖子：</b>{title} 的核心不是记结论，而是把每一步状态变化写出来。</p>"
    )
    llm = chat_completion(
        [
            {"role": "system", "content": "你是考研 408 学习论坛 AI 小助手，回答要友好、具体、可执行，可使用简单 HTML。"},
            {"role": "user", "content": f"帖子标题：{title}\n帖子内容：{content}\n科目：{subject}\n知识点：{point}\n请给出论坛回复。"},
        ],
        fallback,
    )
    return {
        "answer": llm.content.replace("\n", "<br>"),
        "agent_steps": ["内容清洗", "知识点标注", "检索 408 知识", "生成论坛回答"],
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
    }
