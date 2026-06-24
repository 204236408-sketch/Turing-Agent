from sqlalchemy.orm import Session
from services.rag_service import retrieve_knowledge, retrieve_user_memory
from services.llm_service import chat_completion


def answer_question(db: Session, user_id: int, question: str) -> dict:
    knowledge = retrieve_knowledge(db, question, limit=3)
    memories = retrieve_user_memory(db, user_id, question, limit=3)
    first = knowledge[0] if knowledge else {"subject": "408", "knowledge_point": "综合知识", "content": ""}
    memory_tip = memories[0]["content"] if memories else "暂无强相关长期记忆。"
    fallback = (
        f"<b>定位：</b>{first['subject']} · {first['knowledge_point']}。<br>"
        f"<b>解释：</b>{first['content'] or '先明确概念，再按题目条件逐步推导。'}<br>"
        f"<b>结合你的画像：</b>{memory_tip}<br>"
        "建议立刻做 1 道同知识点中等难度选择题，把理解转成可检验的结果。"
    )
    prompt = f"""
用户问题：{question}

检索到的 408 知识：
{knowledge}

用户长期记忆：
{memories}

请用中文回答。要求：
1. 先定位科目和知识点。
2. 给出适合考研 408 的结构化解释。
3. 结合用户长期记忆给个性化提醒。
4. 最后给出下一步训练建议。
5. 不要编造题目、页面访问序列、数值条件；用户没有给具体题目时，只解释概念区别。
6. 控制在 300 字以内。
7. 输出可以使用简单 HTML 标签，如 <b>、<br>、<ol>、<li>。
"""
    llm = chat_completion(
        [
            {"role": "system", "content": "你是考研 408 智能辅导 Agent，必须结合检索知识和用户长期记忆回答。不要编造用户没有提供的题目条件。"},
            {"role": "user", "content": prompt},
        ],
        fallback,
    )
    return {
        "answer": llm.content.replace("\n", "<br>"),
        "subject": first["subject"],
        "knowledge_point": first["knowledge_point"],
        "retrieved_knowledge": knowledge,
        "memories": memories,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "agent_steps": [
            {"name": "目标识别", "output": f"识别为 {first['subject']} 的 {first['knowledge_point']}"},
            {"name": "读取记忆", "output": memory_tip},
            {"name": "检索知识", "output": f"命中 {len(knowledge)} 条 408 知识"},
            {"name": "生成回答", "output": "已调用大模型生成回答" if llm.used_llm else "大模型不可用，已降级本地回答"},
        ],
        "related_actions": ["生成专项题", "加入复习计划"],
    }
