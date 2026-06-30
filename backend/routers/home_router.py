"""
首页大盘接口（半成品需要深化）

功能：
- GET /api/home/overview — 获取首页大屏数据，包含：
  · today_plan：今日学习计划（优先攻克知识点）
  · countdown：考研倒计时
  · recommendations：智能推荐列表
  · stats：本周答题数、正确率、薄弱点统计
  · knowledge_graph：四科知识图谱（含掌握状态着色）
  · memories：长期记忆摘要
  · initial_state：新用户初始引导状态

状态：半成品需要深化。业务逻辑较完整，但存在大量硬编码回退值（操作系统/页面置换算法），
      乱码清理表不全面，知识点状态计算逻辑需要验证。
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import AnswerRecord, KnowledgeMastery, KnowledgePoint, Mistake, User, UserMemory, UserProfile
from services.mastery_service import (
    normalize_status,
    status_label,
    synchronize_user_mastery,
)
from services.knowledge_graph_service import build_knowledge_overview, status_style
from services.recommendation_service import build_smart_recommendations, choose_today_plan as choose_recommended_plan
from utils.response import success


router = APIRouter(prefix="/api/home", tags=["home"])


SUBJECTS = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
DEFAULT_TARGET_DATE = "2026-12-19"

# 状态判定阈值（与 mastery_service._score_to_status 严格一致）
SCORE_THRESHOLDS = {"mastered": 80, "unfamiliar": 50, "unknown": 20, "weak": 1}

# 兼容旧字段 final_status 存中文标签：保留一份中文状态档位表
STATUS_LABELS = ["未学", "薄弱点", "不会", "不熟", "掌握"]

KNOWLEDGE_FALLBACK = {
    "数据结构": ["线性表", "栈和队列", "树与二叉树", "图", "查找与排序"],
    "计算机组成原理": ["数据表示与运算", "存储系统", "指令系统", "中央处理器", "总线与 I/O"],
    "操作系统": ["进程与线程", "同步与互斥", "死锁", "内存管理", "文件系统"],
    "计算机网络": ["体系结构", "数据链路层", "网络层", "传输层", "应用层"],
}
GRAPH_ALIASES = {
    ("数据结构", "绪论"): ["绪论"],
    ("数据结构", "线性表"): ["线性表"],
    ("数据结构", "栈、队列和数组"): ["栈、队列和数组", "栈和队列", "栈", "队列", "数组"],
    ("数据结构", "串"): ["串", "字符串"],
    ("数据结构", "树与二叉树"): ["树与二叉树", "树", "二叉树", "树、森林"],
    ("数据结构", "图"): ["图"],
    ("数据结构", "查找"): ["查找", "查找与排序"],
    ("数据结构", "排序"): ["排序", "查找与排序"],
    ("计算机组成原理", "计算机系统概述"): ["计算机系统概述", "概述"],
    ("计算机组成原理", "数据的表示和运算"): ["数据的表示和运算", "数据表示与运算", "数据表示", "运算"],
    ("计算机组成原理", "存储系统"): ["存储系统"],
    ("计算机组成原理", "指令系统"): ["指令系统"],
    ("计算机组成原理", "中央处理器"): ["中央处理器", "CPU"],
    ("计算机组成原理", "总线"): ["总线", "总线与 I/O", "总线与IO"],
    ("计算机组成原理", "输入输出系统"): ["输入输出系统", "I/O", "输入输出", "IO系统"],
    ("操作系统", "计算机系统概述"): ["计算机系统概述", "OS概述"],
    ("操作系统", "进程与线程"): ["进程与线程", "进程", "线程", "同步与互斥", "进程同步", "同步互斥", "死锁"],
    ("操作系统", "内存管理"): ["内存管理", "分页管理", "虚拟内存", "页面置换算法", "页面置换", "LRU", "FIFO"],
    ("操作系统", "文件管理"): ["文件管理", "文件系统"],
    ("操作系统", "输入输出管理"): ["输入输出管理", "I/O管理", "IO管理"],
    ("计算机网络", "计算机网络体系结构"): ["计算机网络体系结构", "体系结构", "网络体系结构"],
    ("计算机网络", "物理层"): ["物理层"],
    ("计算机网络", "数据链路层"): ["数据链路层"],
    ("计算机网络", "网络层"): ["网络层"],
    ("计算机网络", "传输层"): ["传输层", "TCP", "UDP"],
    ("计算机网络", "应用层"): ["应用层"],
}
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")

MOJIBAKE_MAP = {
    "���ݽṹ": "数据结构",
    "��������ԭ��": "计算机组成原理",
    "����ϵͳ": "操作系统",
    "���������": "计算机网络",
    "���Ա�": "线性表",
    "ջ�Ͷ���": "栈和队列",
    "���������": "树与二叉树",
    "ͼ": "图",
    "����": "查找",
    "���ݱ�ʾ������": "数据表示与运算",
    "�洢ϵͳ": "存储系统",
    "ҳ���û��㷨": "页面置换算法",
    "????": "操作系统",
    "??????": "页面置换算法",
    "δѧ": "未学",
    "����": "掌握",
    "���": "掌握",
    "������": "薄弱点",
    "钖勫急鐐?": "薄弱点",
    "涓嶇啛": "不熟",
    "涓嶄細": "不会",
    "鏈": "未学",
    "鎺屾彙": "掌握",
}


def clean_text(value: str | None, fallback: str = "") -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    if text in MOJIBAKE_MAP:
        return MOJIBAKE_MAP[text]
    if "?" in text or "�" in text:
        return fallback or "待识别知识点"
    return text


def _safe_status(row: KnowledgeMastery | None) -> str:
    if row is None:
        return "未学"
    return row.final_status or "未学"


def target_datetime(profile: UserProfile | None) -> datetime:
    raw = (profile.target_date if profile else "") or DEFAULT_TARGET_DATE
    try:
        return datetime.combine(date.fromisoformat(raw[:10]), time.min, tzinfo=SHANGHAI_TZ)
    except ValueError:
        return datetime.combine(date.fromisoformat(DEFAULT_TARGET_DATE), time.min, tzinfo=SHANGHAI_TZ)


def countdown_payload(profile: UserProfile | None) -> dict:
    target = target_datetime(profile)
    now = datetime.now(SHANGHAI_TZ)
    diff = max(target - now, timedelta())
    days = diff.days
    seconds = diff.seconds
    return {
        "target_date": target.date().isoformat(),
        "target_label": f"{target.year} 年 {target.month} 月 {target.day} 日",
        "days": days,
        "hours": seconds // 3600,
        "minutes": (seconds % 3600) // 60,
        "seconds": seconds % 60,
        "expired": target <= now,
    }


def current_week_range() -> tuple[datetime, datetime]:
    today = datetime.now()
    start = datetime.combine((today - timedelta(days=today.weekday())).date(), time.min)
    return start, start + timedelta(days=7)


def mastery_map(rows: list[KnowledgeMastery]) -> dict[tuple[str, str], KnowledgeMastery]:
    """对同一 (subject, kp) 多行进行去重，选择 mastery_score 最高的行（与 knowledge_graph_service 一致）"""
    result: dict[tuple[str, str], KnowledgeMastery] = {}
    for row in rows:
        key = (clean_text(row.subject), clean_text(row.knowledge_point))
        existing = result.get(key)
        if not existing:
            result[key] = row
            continue
        if (row.mastery_score or 0) > (existing.mastery_score or 0):
            result[key] = row
    return result


def compute_point_status(subject: str, point: str, rows: dict[tuple[str, str], KnowledgeMastery]) -> tuple[str, KnowledgeMastery | None]:
    row = rows.get((subject, point))
    return _safe_status(row), row


def sorted_mastery_candidates(rows: list[KnowledgeMastery]) -> list[KnowledgeMastery]:
    """按掌握度从低到高（最薄弱在前）排序，weak_score 高的优先"""
    return sorted(
        rows,
        key=lambda r: (
            -(r.mastery_score or 0),  # 综合分低的优先
            -(r.weak_score or 0),
            -(r.wrong_count or 0),
            -((r.qa_count or 0) + (r.forum_count or 0)),
        ),
    )


def build_recommendations(rows: list[KnowledgeMastery], mistakes: list[Mistake], memories: list[UserMemory], points: list[KnowledgePoint]) -> list[dict]:
    items: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(mode: str, subject: str, point: str, reason: str, difficulty: str = "中等"):
        key = (mode, subject, point)
        if key in seen or len(items) >= 5:
            return
        seen.add(key)
        items.append(
            {
                "mode": mode,
                "subject": subject,
                "knowledge_point": point,
                "reason": reason,
                "difficulty": difficulty,
                "question_type": "选择题",
                "count": 3,
            }
        )

    for row in sorted_mastery_candidates(rows):
        status = _safe_status(row)
        if status in {"薄弱点", "不会", "不熟"}:
            add(
                "薄弱点强化",
                clean_text(row.subject, "操作系统"),
                clean_text(row.knowledge_point, "页面置换算法"),
                f"{status} · 错 {row.wrong_count} 次 · 薄弱权重 {row.weak_score:g}",
            )
    for mistake in mistakes[:3]:
        add(
            "最近错题复练",
            clean_text(mistake.subject, "操作系统"),
            clean_text(mistake.knowledge_point, "页面置换算法"),
            "来自最近错题记录，建议做同知识点变式题。",
        )
    for memory in memories[:3]:
        add(
            "长期记忆复习",
            clean_text(memory.subject, "操作系统"),
            clean_text(memory.knowledge_point, "页面置换算法"),
            "来自 active 长期记忆，适合转化为训练题。",
        )
    for point in points:
        if point.is_high_frequency:
            add("高频考点诊断", clean_text(point.subject, "操作系统"), clean_text(point.name, "页面置换算法"), "高频知识点，适合作为今日补齐训练。")
    if not items:
        add("新手基线诊断", "操作系统", "页面置换算法", "暂无学习行为，先用高频基础题建立初始画像。")
        add("新手基线诊断", "数据结构", "树与二叉树", "暂无错题记录，先覆盖 408 高频考点。")
        add("新手基线诊断", "计算机网络", "传输层", "暂无问答记录，先检查概念理解。")
    return items[:3]


def build_stats(rows: list[KnowledgeMastery], memories: list[UserMemory], all_answers: list[AnswerRecord], weekly_answers: list[AnswerRecord], last_week_answers: list[AnswerRecord] = None) -> dict:
    total_answers = len(weekly_answers)
    weekly_correct = sum(1 for item in weekly_answers if item.is_correct)
    all_total = len(all_answers)
    all_correct = sum(1 for item in all_answers if item.is_correct)
    accuracy = round((all_correct / all_total) * 100) if all_total else 0
    unique_rows = list(mastery_map(rows).values())
    weak_count = sum(1 for r in unique_rows if _safe_status(r) in {"薄弱点", "不会", "不熟"})
    mastered_count = sum(1 for r in unique_rows if _safe_status(r) == "掌握")
    last_week_total = len(last_week_answers) if last_week_answers else 0
    last_week_correct = sum(1 for item in last_week_answers if item.is_correct) if last_week_answers else 0
    weekly_trend = f"+{round((total_answers - last_week_total) / last_week_total * 100)}%" if last_week_total > 0 and total_answers > last_week_total else (f"-{round((last_week_total - total_answers) / last_week_total * 100)}%" if last_week_total > total_answers else "")
    accuracy_trend = ""
    if all_total >= 10:
        recent_count = min(all_total, 20)
        recent_correct = sum(1 for item in all_answers[-recent_count:] if item.is_correct)
        recent_accuracy = round((recent_correct / recent_count) * 100)
        accuracy_trend = f"+{(recent_accuracy - accuracy)}%" if recent_accuracy > accuracy else (f"-{(accuracy - recent_accuracy)}%" if recent_accuracy < accuracy else "")
    weak_trend = ""
    if unique_rows:
        prev_weak = sum(1 for r in unique_rows if r.final_status in {"薄弱点", "不会", "不熟"} and r.weak_score and r.weak_score > 5)
        weak_trend = f"-{(prev_weak - weak_count)}" if prev_weak > weak_count else (f"+{(weak_count - prev_weak)}" if weak_count > prev_weak else "")
    memory_trend = ""
    if len(memories) > 0:
        now_naive = datetime.now()
        def _days_since(dt):
            if dt is None:
                return 999
            dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
            return (now_naive - dt_naive).days
        memory_trend = "新增" if any(_days_since(m.update_time) <= 1 for m in memories) else ""
    return {
        "weekly_answers": total_answers,
        "weekly_correct": weekly_correct,
        "accuracy": accuracy,
        "weak_points": weak_count,
        "mastered_points": mastered_count,
        "memory_entries": len(memories),
        "cards": [
            {"label": "本周答题", "value": total_answers, "delta": f"{weekly_correct} 道正确" if total_answers else "开始答题后自动统计", "trend": weekly_trend},
            {"label": "综合正确率", "value": f"{accuracy}%" if all_total else "待生成", "delta": f"累计 {all_total} 次答题" if all_total else "暂无答题记录", "trend": accuracy_trend},
            {"label": "长期薄弱点", "value": weak_count, "delta": "按 weak_score 与错题同步", "trend": weak_trend},
            {"label": "记忆条目", "value": len(memories), "delta": "问答、错题和反馈会写入这里", "trend": memory_trend},
        ],
    }


def build_memory_list(memories: list[UserMemory], rows: list[KnowledgeMastery]) -> list[dict]:
    items = [
        {
            "title": clean_text(m.knowledge_point, "待复习知识点"),
            "content": clean_text(m.content, "系统已记录一个需要复习的长期记忆条目。"),
            "subject": clean_text(m.subject, "408"),
        }
        for m in memories[:4]
    ]
    if items:
        return items
    touched = [r for r in sorted_mastery_candidates(rows) if _safe_status(r) != "未学"]
    if touched:
        return [
            {
                "title": clean_text(row.knowledge_point, "已学习知识点"),
                "content": f"当前状态：{_safe_status(row)}；答题 {row.total_answer_count} 次，错 {row.wrong_count} 次。",
                "subject": clean_text(row.subject, "408"),
            }
            for row in touched[:3]
        ]
    return [
        {
            "title": "还没有长期学习记忆",
            "content": "完成一次出题训练、问答或错题确认后，系统会把薄弱点、错因和复习偏好写入这里。",
            "subject": "初始化",
        }
    ]


def _worst_status(statuses: list[str]) -> str:
    """取状态列表中最差的一个（按 STATUS_LABELS 顺序：未学 < 薄弱点 < 不会 < 不熟 < 掌握）"""
    if not statuses:
        return "未学"
    return min(statuses, key=lambda s: STATUS_LABELS.index(s) if s in STATUS_LABELS else 99)


def _kp_key(point: KnowledgePoint) -> tuple[str, str]:
    """与 knowledge_graph_service.point_name_of 保持一致：section → name。"""
    return (point.subject, clean_text(point.section) or clean_text(point.name))


def _kp_name(point: KnowledgePoint) -> str:
    return clean_text(point.section) or clean_text(point.name)


def build_graph(db: Session, user_id: int, points: list[KnowledgePoint]) -> dict:
    """首页图谱：直接复用 knowledge_graph_service.build_knowledge_overview，保证两页面同源。

    返回结构适配首页前端：
      - subjects: { 科目: [chapter_item, ...] }，每个 chapter_item 含 status / mastery_percent / style
      - summary: { 状态key: 计数 } 供前端分布条
      - status_style: { 状态key: { color, label, class_name } }
    """
    overview = build_knowledge_overview(db, user_id)
    # overview["subjects"] 是 list 形态，首页期望 dict 形态，转换之
    grouped: dict[str, list[dict]] = {s: [] for s in SUBJECTS}
    summary: dict[str, int] = {key: 0 for key in ("mastered", "unfamiliar", "unknown", "weak", "unlearned")}

    for subject in overview.get("subjects", []):
        sname = subject["subject_name"]
        for chapter in subject.get("chapters", []):
            grouped.setdefault(sname, []).append({
                "id": f"{sname}-{chapter['chapter_name']}",
                "subject": sname,
                "name": chapter["chapter_name"],
                "section": chapter["chapter_name"],
                "parent_name": sname,
                "level": 2,
                "is_high_frequency": False,
                "status": chapter["status"],
                "status_label": chapter["status_label"],
                "mastery_percent": chapter["mastery_percent"],
                "knowledge_count": chapter["knowledge_count"],
                "learned_count": chapter.get("learned_count", 0),
                "style": chapter["style"],
            })
            summary[chapter["status"]] = summary.get(chapter["status"], 0) + 1

    for s in SUBJECTS:
        grouped.setdefault(s, [])

    return {
        "subjects": grouped,
        "summary": summary,
        "status_style": {key: status_style(key) for key in ("mastered", "unfamiliar", "unknown", "weak", "unlearned")},
    }


@router.get("/overview")
def home_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    points = db.query(KnowledgePoint).order_by(KnowledgePoint.subject, KnowledgePoint.id).all()
    synchronize_user_mastery(db, user.id, [(point.subject, point.name) for point in points])
    db.flush()
    mastery_rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user.id).all()
    memories = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user.id, UserMemory.status == "active")
        .order_by(desc(UserMemory.update_time))
        .all()
    )
    mistakes = (
        db.query(Mistake)
        .filter(Mistake.user_id == user.id, Mistake.status == "active")
        .order_by(desc(Mistake.create_time))
        .all()
    )
    week_start, week_end = current_week_range()
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start
    weekly_answers = (
        db.query(AnswerRecord)
        .filter(AnswerRecord.user_id == user.id, AnswerRecord.create_time >= week_start, AnswerRecord.create_time < week_end)
        .all()
    )
    last_week_answers = (
        db.query(AnswerRecord)
        .filter(AnswerRecord.user_id == user.id, AnswerRecord.create_time >= last_week_start, AnswerRecord.create_time < last_week_end)
        .all()
    )
    all_answers = db.query(AnswerRecord).filter(AnswerRecord.user_id == user.id).all()
    answer_count = len(all_answers)
    today_plan = choose_recommended_plan(db, user.id)
    raw_recommendations = build_smart_recommendations(db, user.id)
    recommendations = sorted(raw_recommendations, key=lambda item: (not item["available"], raw_recommendations.index(item)))
    stats = build_stats(mastery_rows, memories, all_answers, weekly_answers, last_week_answers)
    # 关键修复：与导航页同源；synchronize_user_mastery 用 (subject, section) 作为 KP key
    synchronize_user_mastery(db, user.id, [_kp_key(p) for p in points])
    db.flush()
    graph = build_graph(db, user.id, points)
    db.commit()
    return success(
        {
            "today_plan": today_plan,
            "countdown": countdown_payload(profile),
            "recommendations": recommendations,
            "stats": stats,
            "knowledge_graph": graph,
            "memories": build_memory_list(memories, mastery_rows),
            "initial_state": {
                "has_answers": answer_count > 0,
                "has_mistakes": bool(mistakes),
                "has_memories": bool(memories),
                "message": "当前还没有足够学习记录，先完成一次基线诊断，系统会自动建立你的 408 学习画像。",
            },
        }
    )
