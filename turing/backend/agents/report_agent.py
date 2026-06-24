from sqlalchemy.orm import Session
from models import AnswerRecord, KnowledgeMastery, Mistake, Report, UserMemory
import json
from services.llm_service import chat_json


SUBJECTS = {"数据结构", "计算机组成原理", "操作系统", "计算机网络"}
PLACEHOLDER_VALUES = {"阶段总结", "主要错误类型", "高频提问知识点", "论坛高频讨论知识点", "推荐视频方向", "任务1", "任务2", "任务3"}


def _valid_learning_point(subject: str, knowledge_point: str) -> bool:
    value = (knowledge_point or "").strip()
    return subject in SUBJECTS and bool(value) and value != "待生成" and "?" not in value


def _clean_text(value, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or text in PLACEHOLDER_VALUES:
        return fallback
    return text


def _clean_plan(value, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    items = [str(item).strip() for item in value if str(item or "").strip()]
    items = [item for item in items if item not in PLACEHOLDER_VALUES]
    return items[:5] or fallback


def generate_report(db: Session, user_id: int) -> dict:
    total = db.query(AnswerRecord).filter(AnswerRecord.user_id == user_id).count()
    correct = db.query(AnswerRecord).filter(AnswerRecord.user_id == user_id, AnswerRecord.is_correct == True).count()
    weak = (
        db.query(KnowledgeMastery)
        .filter(KnowledgeMastery.user_id == user_id, KnowledgeMastery.final_status.in_(["薄弱点", "不会", "不熟"]))
        .all()
    )
    weak = [item for item in weak if _valid_learning_point(item.subject, item.knowledge_point)]
    mistakes = db.query(Mistake).filter(Mistake.user_id == user_id).order_by(Mistake.create_time.desc()).limit(12).all()
    mistakes = [item for item in mistakes if _valid_learning_point(item.subject, item.knowledge_point)][:5]
    memories = db.query(UserMemory).filter(UserMemory.user_id == user_id, UserMemory.status == "active").limit(20).all()
    memories = [item for item in memories if _valid_learning_point(item.subject, item.knowledge_point)][:5]
    weak_points = "、".join([item.knowledge_point for item in weak]) or "暂无明显薄弱点"
    fallback = {
        "summary": f"累计答题 {total} 道，正确 {correct} 道，当前重点是 {weak_points}。",
        "main_error_type": "、".join([m.error_type for m in mistakes if m.error_type]) or "规则混淆",
        "qa_focus": "页面置换算法、TCP 连接释放",
        "forum_focus": "操作系统与计算机网络高频讨论",
        "video_suggestion": "优先观看页面置换算法和 TCP 四次挥手专题",
        "plan": ["完成页面置换算法 3 道中等题", "复述 TCP TIME_WAIT 两个作用", "整理 1 条错因进入长期记忆"],
    }
    llm = chat_json(
        [
            {"role": "system", "content": "你是考研 408 学习报告 Agent。只输出合法 JSON，不要输出字段说明、占位词或模板词。"},
            {
                "role": "user",
                "content": f"""
累计答题：{total}
正确题数：{correct}
薄弱知识点：{weak_points}
最近错题：{[m.error_type + ':' + m.knowledge_point for m in mistakes]}
长期记忆：{[m.content for m in memories]}

请输出：
{{
  "summary": "基于真实数据写一段阶段总结",
  "main_error_type": "概括最近错题中最突出的错误类型",
  "qa_focus": "从长期记忆和错题推断后续问答应关注的知识点",
  "forum_focus": "推断适合在论坛关注或讨论的主题",
  "video_suggestion": "给出适合观看的视频方向",
  "plan": ["具体训练任务1", "具体训练任务2", "具体训练任务3"]
}}
""",
            },
        ],
        fallback,
    )
    data = llm.data or fallback
    plan = _clean_plan(data.get("plan"), fallback["plan"])
    report = Report(
        user_id=user_id,
        title="Turing 408 阶段学习报告",
        summary=_clean_text(data.get("summary"), fallback["summary"]),
        weak_points=weak_points,
        main_error_type=_clean_text(data.get("main_error_type"), fallback["main_error_type"]),
        qa_focus=_clean_text(data.get("qa_focus"), fallback["qa_focus"]),
        forum_focus=_clean_text(data.get("forum_focus"), fallback["forum_focus"]),
        video_suggestion=_clean_text(data.get("video_suggestion"), fallback["video_suggestion"]),
        plan_json=json.dumps(plan, ensure_ascii=False),
    )
    db.add(report)
    db.flush()
    payload = report_to_dict(report, memories)
    payload["llm_used"] = llm.used_llm
    payload["llm_error"] = llm.error
    return payload


def report_to_dict(report: Report, memories=None) -> dict:
    visible_memories = [
        item for item in (memories or [])
        if _valid_learning_point(item.subject, item.knowledge_point)
    ]
    return {
        "id": report.id,
        "title": report.title,
        "summary": report.summary,
        "weak_points": report.weak_points,
        "main_error_type": report.main_error_type,
        "qa_focus": report.qa_focus,
        "forum_focus": report.forum_focus,
        "video_suggestion": report.video_suggestion,
        "plan": json.loads(report.plan_json or "[]"),
        "memories": [
            {"knowledge_point": item.knowledge_point, "content": item.content}
            for item in visible_memories
        ],
        "create_time": report.create_time.isoformat(),
    }
