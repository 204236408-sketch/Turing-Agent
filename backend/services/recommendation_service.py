from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import (
    AnswerRecord,
    KnowledgeMastery,
    KnowledgePoint,
    Mistake,
    Question,
    QuestionGenerationSession,
    UserMemory,
)

# 统一时区锚点：上海。涉及"今日"语义（种子、4 小时窗口）都按上海时间算，避免 UTC 与上海相差 8 小时
# 导致跨夜时科目/题型轮换错位，或晚 8 点前用户看不到早上推荐的题目
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")

STATUS_PRIORITY = {"薄弱点": 0, "不会": 1, "不熟": 2, "掌握": 3, "未学": 4}
SMART_MODES = {"薄弱点强化", "最近错题复练", "高频提问专项", "已改善知识点复测", "四科随机综合"}

_ALL_SUBJECTS = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
_ALL_QUESTION_TYPES = ["选择题", "填空题", "简答题", "综合题"]

# today_plan 降级链：错题（最高信号）→ 提问 → 薄弱；「四科随机综合」不进入此链，
# 因为它是基线诊断兜底，只有"非综合项全不可用"时才单独处理。
TODAY_PLAN_FALLBACK_CHAIN = ["最近错题复练", "高频提问专项", "薄弱点强化"]


def _now_shanghai() -> datetime:
    """统一返回带上海时区的当前时间，避免与 UTC 混用。"""
    return datetime.now(SHANGHAI_TZ)


def _normalize_kp(name: str | None) -> str:
    """KP 名称归一化：去首尾空格、去掉 `(xxx)` 括号后缀。

    设计动机：OCR 错题回流时可能写作「指令集体系结构(ISA)」「进程与线程(同步)」等带括号别名，
    而 seed 库的标准名是「指令系统」「进程与线程」。如果不归一化，错误 KP 名下的 mastery 与错题
    会和真实 KP 失配，导致「最近错题复练」命中不到 mastery 行，主推逻辑看起来"没数据"。
    这是项目硬约束里登记的统一入口，所有 KP 名称比较都应先走这里。
    """
    if not name:
        return ""
    text = str(name).strip()
    # 去掉第一个左括号之后的内容（ISA、同步、扩展等补充说明）
    for sep in ("（", "("):
        idx = text.find(sep)
        if idx > 0:
            text = text[:idx].strip()
            break
    return text


def _kp_key(subject: str | None, kp: str | None) -> tuple[str, str]:
    """生成 (subject, kp) 归一化 key，供 used/比较使用。"""
    return ((subject or "").strip(), _normalize_kp(kp))


def _to_difficulty(mastery: KnowledgeMastery | None, base: str = "中等") -> str:
    """weak_score 越高越薄弱，出题就该越简单（降低挫败感）。"""
    if mastery is None:
        return base
    ws = mastery.weak_score or 0
    if ws > 6:
        return "简单"
    if ws >= 3:
        return "中等"
    if mastery.total_answer_count and mastery.total_answer_count >= 5:
        return "较难"
    return base


def _to_question_type(mastery: KnowledgeMastery | None, mode: str) -> str:
    """根据薄弱特征选择题型：连续错→填空、频繁提问→简答、弱分高→综合，其余选择题。"""
    if mode == "已改善知识点复测":
        return "选择题"
    if mastery is None:
        return "选择题"
    cw = mastery.continuous_wrong_count or 0
    qa = mastery.qa_count or 0
    ws = mastery.weak_score or 0
    if cw >= 2:
        return "填空题"
    if qa >= 3:
        return "简答题"
    if ws >= 8:
        return "综合题"
    return "选择题"


def _to_count(mastery: KnowledgeMastery | None, mode: str) -> int:
    """weak_score 越高（越薄弱），题目越多强化练习。"""
    if mode == "已改善知识点复测":
        return 2
    if mode == "四科随机综合":
        return 3
    if mastery is None:
        return 3
    ws = mastery.weak_score or 0
    if ws > 6:
        return 5
    if ws >= 3:
        return 3
    return 2


def _point_payload(
    mode: str,
    subject: str,
    knowledge_point: str,
    reason: str,
    difficulty: str,
    question_type: str,
    count: int,
    *,
    available: bool = True,
    initial: bool = False,
    mistake_tip: str = "",
) -> dict:
    """组装推荐项；可附 mistake_tip 一句个性化提示（基于用户错题摘要，无需 LLM 调用）。"""
    enriched_reason = reason
    if mistake_tip:
        enriched_reason = f"{reason}\n{_personalize_hint(mistake_tip)}"
    return {
        "mode": mode,
        "subject": subject,
        "knowledge_point": knowledge_point,
        "reason": enriched_reason,
        "difficulty": difficulty,
        "question_type": question_type,
        "count": count,
        "available": available,
        "initial": initial,
    }


def _personalize_hint(mistake_tip: str) -> str:
    """把错题摘要转成单句建议（不调 LLM，避免引入新的幻觉）。"""
    if not mistake_tip:
        return ""
    tip = mistake_tip[:60] + ('...' if len(mistake_tip) > 60 else '')
    return f"建议关注你最近的错因：{tip}"


def _format_mistake_tip(mistakes: list) -> str:
    """从错题列表里抽取最高频的 error_type + 错因，组成一句 tip。"""
    if not mistakes:
        return ""
    type_counter: dict[str, int] = {}
    sample_reason = ""
    for m in mistakes[:10]:
        et = m.error_type or "未分类"
        type_counter[et] = type_counter.get(et, 0) + 1
        if not sample_reason and m.error_reason:
            sample_reason = m.error_reason
    top_type = max(type_counter, key=type_counter.get) if type_counter else ""
    if sample_reason and top_type:
        return f"{top_type}：{sample_reason}"
    if sample_reason:
        return sample_reason
    if top_type:
        return top_type
    return ""


def _kp_name(point: KnowledgePoint) -> str:
    """与 knowledge_graph_service.point_name_of 保持一致：section → name。"""
    return (point.section or point.name or "").strip()


def _baseline_points(db: Session) -> list[KnowledgePoint]:
    """取高频考点作为基线，无高频标记时退化为全量知识点。"""
    points = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.is_high_frequency == True)
        .order_by(KnowledgePoint.subject.asc(), KnowledgePoint.id.asc())
        .all()
    )
    if points:
        return points
    return db.query(KnowledgePoint).order_by(KnowledgePoint.subject.asc(), KnowledgePoint.id.asc()).all()


def _urgency_score(mastery: KnowledgeMastery) -> float:
    """综合弱分+连续错数+提问数+最近练习时间来评估紧迫程度。"""
    ws = mastery.weak_score or 0
    cw = mastery.continuous_wrong_count or 0
    qa = mastery.qa_count or 0
    recency = 0
    if mastery.last_answer_time:
        # last_answer_time 在数据库里通常以 UTC 存储（naive），与 SHANGNAI_TZ 当前时间比较时统一转到上海
        last = mastery.last_answer_time
        if last.tzinfo is None:
            last = last.replace(tzinfo=ZoneInfo("UTC"))
        days = (_now_shanghai() - last.astimezone(SHANGHAI_TZ)).days
        recency = max(0, 5 - days)
    return ws * 0.4 + cw * 2.5 + qa * 0.5 + recency * 0.5


def _recently_recommended(db: Session, user_id: int, hours: int = 4) -> set[tuple[str, str]]:
    """最近 hours 小时内已"真正答过题"的知识点集合（用于去重）。

    与旧实现的区别：旧实现从 QuestionGenerationSession 查"出过题"，但用户可能只点开按钮没答完，
    会导致 4 个非综合项全被去重过滤、今天优先攻克降级到空状态。改为从 AnswerRecord 查"已提交答案"，
    才是"已经练过"的真实信号。
    """
    cutoff = _now_shanghai() - timedelta(hours=hours)
    rows = (
        db.query(AnswerRecord.subject, AnswerRecord.knowledge_point)
        .filter(
            AnswerRecord.user_id == user_id,
            AnswerRecord.create_time >= cutoff,
            AnswerRecord.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    result: set[tuple[str, str]] = set()
    for r in rows:
        # 兼容 (subject, knowledge_point) 单行或 Row 对象两种形态
        subject = getattr(r, "subject", None) or (r[0] if len(r) > 0 else None)
        kp = getattr(r, "knowledge_point", None) or (r[1] if len(r) > 1 else None)
        result.add(_kp_key(subject, kp))
    # 去掉空 key（脏数据兜底）
    return {k for k in result if k[0] and k[1]}


def _recently_answered_per_mode(
    db: Session,
    user_id: int,
    hours: int = 4,
) -> dict[str, set[tuple[str, str]]]:
    """按 mode 分别聚合最近 hours 小时内已答过的 KP 集合。

    关系链：AnswerRecord.question_id -> Question.id -> Question.session_id -> QuestionGenerationSession.id。
    任意一环 join 失败都不能阻塞整个推荐接口,所以用 try/except 软降级：失败时返回空 dict,
    让 5 个推荐项走"无去重"路径,功能正常但允许 4h 内重复。
    """
    try:
        cutoff = _now_shanghai() - timedelta(hours=hours)
        rows = (
            db.query(
                QuestionGenerationSession.recommend_mode,
                AnswerRecord.subject,
                AnswerRecord.knowledge_point,
            )
            .join(Question, Question.id == AnswerRecord.question_id)
            .join(QuestionGenerationSession, QuestionGenerationSession.id == Question.session_id)
            .filter(
                QuestionGenerationSession.user_id == user_id,
                AnswerRecord.user_id == user_id,
                AnswerRecord.create_time >= cutoff,
                AnswerRecord.is_deleted == False,  # noqa: E712
                QuestionGenerationSession.is_deleted == False,  # noqa: E712
            )
            .all()
        )
    except Exception as e:  # noqa: BLE001
        # 软降级：join 失败返回空 dict,不阻塞主流程
        logging.getLogger(__name__).warning("per-mode recent join failed: %s", e)
        return {}

    result: dict[str, set[tuple[str, str]]] = {}
    for mode, subject, kp in rows:
        if not mode or not subject or not kp:
            continue
        result.setdefault(mode, set()).add(_kp_key(subject, kp))
    return result


def _recently_recommended_fingerprints(db: Session, user_id: int, hours: int = 24, limit: int = 30) -> list[str]:
    """最近 24 小时内生成的题面指纹列表（题干前 32 字 + 中文实词）。

    推荐环节用：让 5 个推荐项尽量不在"最近已经出过类似题"的知识点上重复。
    """
    try:
        from agents.question_graph import _text_signature  # 复用去重节点的指纹函数
    except Exception:
        return []
    try:
        cutoff = _now_shanghai() - timedelta(hours=hours)
        rows = (
            db.query(Question.question_text)
            .join(QuestionGenerationSession, Question.session_id == QuestionGenerationSession.id)
            .filter(
                QuestionGenerationSession.user_id == user_id,
                QuestionGenerationSession.create_time >= cutoff,
                Question.is_deleted == False,  # noqa: E712
            )
            .order_by(QuestionGenerationSession.create_time.desc())
            .limit(limit)
            .all()
        )
        return [_text_signature(r[0]) for r in rows if r and r[0]]
    except Exception:  # noqa: BLE001
        return []


def _masteries_with_scores(db: Session, user_id: int) -> list[tuple[KnowledgeMastery, float]]:
    rows = db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user_id).all()
    scored = [(r, _urgency_score(r)) for r in rows]
    scored.sort(key=lambda x: -x[1])
    return scored


def _pop_used(
    candidates: list[tuple[KnowledgeMastery, float]],
    used: set[tuple[str, str]],
) -> tuple[KnowledgeMastery, float] | None:
    """从 candidates 中取第一个未在 used 中的项，使用归一化 KP key 比较。"""
    for m, s in candidates:
        if _kp_key(m.subject, m.knowledge_point) not in used:
            return m, s
    return None


def build_smart_recommendations(db: Session, user_id: int) -> list[dict]:
    """生成 5 种推荐模式的列表。

    关键设计点（与旧实现的差异）：
    1. 跨模式 used 集合使用归一化 KP key（_kp_key），避免 OCR 错题回流的"(ISA)"等后缀让 mastery 命中失败。
    2. 4 小时去重只对「同 mode」生效：用户答过"薄弱点强化"的 KP 不会让"高频提问专项"也跳过。
    3. 5 个模式之间仍共享 used 集合，作为"5 个推荐项尽量不指向同一 KP"的软约束，
       但每个模式在过滤前先去掉自己 mode 4 小时内已用过的 KP（避免同 mode 4h 内重复）。

    软降级：整个函数任何位置抛异常,都返回 5 个 available=False 的占位项（指向 baseline fallback）,
    保证 /api/home/overview 不返回 500,前端只看到「暂无数据」而不是「接口暂不可用」。
    """
    try:
        return _build_smart_recommendations_impl(db, user_id)
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).exception("build_smart_recommendations failed: %s", e)
        try:
            baseline = _baseline_points(db)
            fallback = baseline[0] if baseline else None
            fallback_subject = fallback.subject if fallback else "数据结构"
            fallback_point = _kp_name(fallback) if fallback else "线性表"
        except Exception:  # noqa: BLE001
            fallback_subject, fallback_point = "数据结构", "线性表"
        # 5 个占位项,available=False 走兜底
        placeholders = [
            ("薄弱点强化", "中等", "选择题", 3),
            ("最近错题复练", "简单", "选择题", 2),
            ("高频提问专项", "中等", "填空题", 2),
            ("已改善知识点复测", "较难", "选择题", 2),
            ("四科随机综合", "中等", "综合题", 3),
        ]
        return [
            {
                "mode": mode,
                "subject": fallback_subject,
                "knowledge_point": fallback_point,
                "reason": f"推荐生成暂不可用：{type(e).__name__}",
                "difficulty": diff,
                "question_type": qt,
                "count": cnt,
                "available": False,
                "initial": True,
            }
            for mode, diff, qt, cnt in placeholders
        ]


def _build_smart_recommendations_impl(db: Session, user_id: int) -> list[dict]:
    """build_smart_recommendations 的实际实现,异常时由外层 try 软降级。"""
    mastery_rows = (
        db.query(KnowledgeMastery)
        .filter(KnowledgeMastery.user_id == user_id)
        .all()
    )
    mistakes = (
        db.query(Mistake)
        .filter(Mistake.user_id == user_id, Mistake.status == "active")
        .order_by(desc(Mistake.create_time), desc(Mistake.id))
        .all()
    )
    memories = (
        db.query(UserMemory)
        .filter(
            UserMemory.user_id == user_id,
            UserMemory.memory_type == "weak_point",
            UserMemory.status == "active",
        )
        .order_by(desc(UserMemory.update_time), desc(UserMemory.id))
        .all()
    )
    baseline = _baseline_points(db)
    fallback = baseline[0] if baseline else None
    fallback_subject = fallback.subject if fallback else "数据结构"
    fallback_point = _kp_name(fallback) if fallback else "线性表"

    # 4 小时内按 mode 分别聚合的"答过"集合（与旧实现最大差异点）
    per_mode_recent = _recently_answered_per_mode(db, user_id)

    scored = _masteries_with_scores(db, user_id)

    # 归一化 KP key 的 mastery 反查表
    weak_map: dict[tuple[str, str], KnowledgeMastery] = {}
    for m in mastery_rows:
        weak_map[_kp_key(m.subject, m.knowledge_point)] = m

    # 跨模式 used：保证 5 项尽量不指向同一 KP（软约束，不强求）
    used: set[tuple[str, str]] = set()

    # P2-9: 准备用户错题 tip（无 LLM 调用的个性化），用于"薄弱点强化"和"最近错题复练"两项
    user_mistake_tip = _format_mistake_tip(mistakes) if mistakes else ""

    def _filter_by_mode_used(
        candidates: list,
        mode: str,
    ) -> list:
        """先按 mode 自身 4h 内已用 KP 过滤；剩余再交给 _pop_used 走跨模式 used 软约束。

        接受两种 candidates 形态：
        - list[(KnowledgeMastery, float)]（带 urgency 分数）
        - list[KnowledgeMastery]（不带分数，例如已改善复测/高频提问专项场景）
        通过 isinstance 自动适配,避免 c[0] 在非元组类型上抛 TypeError。
        """
        mode_used = per_mode_recent.get(mode, set())
        result = []
        for c in candidates:
            m = c[0] if isinstance(c, tuple) else c
            if _kp_key(m.subject, m.knowledge_point) not in mode_used:
                result.append(c)
        return result

    # ── 1. 薄弱点强化 ──
    scored_weak_all = [
        (m, s) for m, s in scored
        if m.final_status in {"薄弱点", "不会", "不熟"}
    ]
    scored_weak = _filter_by_mode_used(scored_weak_all, "薄弱点强化")
    if scored_weak:
        picked = _pop_used(scored_weak, used)
        if picked:
            m, _ = picked
            used.add(_kp_key(m.subject, m.knowledge_point))
            weak_item = _point_payload(
                "薄弱点强化", m.subject, m.knowledge_point,
                f"{m.final_status}·连续答错 {m.continuous_wrong_count} 次，"
                f"建议优先做 {_to_question_type(m, '薄弱点强化')} 专项训练。",
                _to_difficulty(m),
                _to_question_type(m, "薄弱点强化"),
                _to_count(m, "薄弱点强化"),
                mistake_tip=user_mistake_tip,
            )
        else:
            m, _ = scored_weak[0]
            weak_item = _point_payload(
                "薄弱点强化", m.subject, m.knowledge_point,
                f"{m.final_status}·连续答错 {m.continuous_wrong_count} 次",
                _to_difficulty(m),
                _to_question_type(m, "薄弱点强化"),
                _to_count(m, "薄弱点强化"),
                mistake_tip=user_mistake_tip,
            )
    elif memories:
        mem = memories[0]
        m = weak_map.get((mem.subject, mem.knowledge_point))
        weak_item = _point_payload(
            "薄弱点强化", mem.subject, mem.knowledge_point,
            "长期记忆仍标记为薄弱点，优先通过专项题验证。",
            _to_difficulty(m),
            _to_question_type(m, "薄弱点强化"),
            _to_count(m, "薄弱点强化"),
        )
    else:
        weak_item = _point_payload(
            "薄弱点强化", fallback_subject, fallback_point,
            "尚未形成薄弱点。先完成基线诊断，答题后系统会自动定位需要强化的知识点。",
            "简单", "选择题", 3,
            available=False, initial=True,
        )

    # ── 2. 最近错题复练 ──
    if mistakes:
        lm = mistakes[0]
        m = weak_map.get(_kp_key(lm.subject, lm.knowledge_point))
        mode_used = per_mode_recent.get("最近错题复练", set())
        if _kp_key(lm.subject, lm.knowledge_point) in mode_used:
            for alt in mistakes[1:]:
                if _kp_key(alt.subject, alt.knowledge_point) not in mode_used:
                    lm = alt
                    m = weak_map.get(_kp_key(lm.subject, lm.knowledge_point))
                    break
        if _kp_key(lm.subject, lm.knowledge_point) in used:
            for alt in mistakes[1:]:
                if (
                    _kp_key(alt.subject, alt.knowledge_point) not in used
                    and _kp_key(alt.subject, alt.knowledge_point) not in mode_used
                ):
                    lm = alt
                    m = weak_map.get(_kp_key(lm.subject, lm.knowledge_point))
                    break
        used.add(_kp_key(lm.subject, lm.knowledge_point))
        mistake_item = _point_payload(
            "最近错题复练", lm.subject, lm.knowledge_point,
            f"最近错题来自「{lm.knowledge_point}」（{lm.error_type or '未分类'}），"
            f"生成 {_to_count(m, '最近错题复练')} 道同类变式题检查是否真正理解错因。",
            _to_difficulty(m, "中等"),
            _to_question_type(m, "最近错题复练"),
            _to_count(m, "最近错题复练"),
        )
    else:
        mistake_item = _point_payload(
            "最近错题复练", fallback_subject, fallback_point,
            "暂无错题记录。完成一次答题并确认错因后，这里会自动生成错题复练。",
            "简单", "选择题", 2,
            available=False, initial=True,
        )

    # ── 3. 高频提问专项 ──
    qa_candidates_all = sorted(
        [m for m in mastery_rows if (m.qa_count or 0) > 0],
        key=lambda r: r.qa_count or 0,
        reverse=True,
    )
    qa_candidates = _filter_by_mode_used(qa_candidates_all, "高频提问专项")
    if qa_candidates:
        qa_m = qa_candidates[0]
        for alt in qa_candidates:
            if _kp_key(alt.subject, alt.knowledge_point) not in used:
                qa_m = alt
                break
        used.add(_kp_key(qa_m.subject, qa_m.knowledge_point))
        qa_item = _point_payload(
            "高频提问专项", qa_m.subject, qa_m.knowledge_point,
            f"你已围绕该知识点提问 {qa_m.qa_count} 次，"
            f"适合把「问懂了」转化为「会做题」。",
            _to_difficulty(qa_m, "中等"),
            _to_question_type(qa_m, "高频提问专项"),
            _to_count(qa_m, "高频提问专项"),
        )
    else:
        qa_item = _point_payload(
            "高频提问专项", fallback_subject, fallback_point,
            "暂无可归类的高频提问。完成知识问答后，系统会按提问知识点生成专项题。",
            "中等", "填空题", 2,
            available=False, initial=True,
        )

    # ── 4. 已改善知识点复测 ──
    improved_candidates_all = [m for m in mastery_rows if m.final_status == "掌握"]
    improved_candidates = _filter_by_mode_used(improved_candidates_all, "已改善知识点复测")
    improved_candidates = [
        m for m in improved_candidates
        if _kp_key(m.subject, m.knowledge_point) not in used
    ]
    if improved_candidates:
        imp = improved_candidates[0]
        used.add(_kp_key(imp.subject, imp.knowledge_point))
        improved_item = _point_payload(
            "已改善知识点复测", imp.subject, imp.knowledge_point,
            f"当前状态已掌握（答对 {imp.correct_count}/{imp.total_answer_count}），"
            f"提高难度复测掌握是否稳定。",
            "较难", "选择题", 2,
        )
    else:
        improved_item = _point_payload(
            "已改善知识点复测", fallback_subject, fallback_point,
            "暂无达到「掌握」的知识点。累计至少 3 次答题且正确率达到 80% 后开放复测。",
            "较难", "选择题", 2,
            available=False, initial=True,
        )

    # ── 5. 四科随机综合 ──
    # 时区修复：用上海时区生成种子，与前端"今日"语义对齐
    today = _now_shanghai()
    seed = today.timetuple().tm_yday
    subject_index = (seed // 7) % 4
    qtype_index = (seed // 3) % 4

    primary_subject = _ALL_SUBJECTS[subject_index]
    primary_qtype = _ALL_QUESTION_TYPES[qtype_index]

    by_subject: dict[str, list[KnowledgePoint]] = {}
    for p in baseline:
        by_subject.setdefault(p.subject, []).append(p)
    pts = by_subject.get(primary_subject) or [fallback]
    primary_point = pts[seed % max(len(pts), 1)]

    comprehensive_item = _point_payload(
        "四科随机综合",
        primary_subject,
        primary_point.name if primary_point else fallback_point,
        f"本周主推 {primary_subject}，题型轮换至 {primary_qtype}。"
        f"按 408 高频考点轮换抽取，用于建立或校准当前学习画像。",
        "中等",
        primary_qtype,
        3,
        initial=not any(r.total_answer_count for r in mastery_rows),
    )

    return [weak_item, mistake_item, qa_item, improved_item, comprehensive_item]


def resolve_smart_recommendation(db: Session, user_id: int, mode: str) -> dict:
    """按 mode 名取推荐项，如果不可用则回退到四科随机综合。"""
    normalized_mode = mode if mode in SMART_MODES else "薄弱点强化"
    items = build_smart_recommendations(db, user_id)
    chosen = next(item for item in items if item["mode"] == normalized_mode)
    if chosen["available"]:
        return chosen
    return next(item for item in items if item["mode"] == "四科随机综合")


def choose_today_plan(db: Session, user_id: int) -> dict:
    """为用户选择"今日计划"。

    降级链：错题（最高信号）→ 提问 → 薄弱 → 综合（兜底）。
    与旧实现的差异：旧实现只在"非综合项"里挑第一个 available，常常让用户看到四科综合的基线诊断卡片。
    新实现按"信号强度"递降选择：错题/提问都算强信号，只要其中之一 available，就直接拿来当今日计划，
    给用户一个有内容的卡片；只有当所有强信号都不可用时，才退到"薄弱→综合"作为兜底。
    同时用 initial_state 区分「新手指引」与「真实空状态异常」。

    软降级：任何异常都返回"先完成一次 408 基线诊断"占位卡片（initial_state=True）,
    保证 /api/home/overview 不返回 500。
    """
    try:
        items = build_smart_recommendations(db, user_id)
        by_mode: dict[str, dict] = {it["mode"]: it for it in items}

        # 1. 按 TODAY_PLAN_FALLBACK_CHAIN 顺序挑选第一个 available
        for mode in TODAY_PLAN_FALLBACK_CHAIN:
            cand = by_mode.get(mode)
            if cand and cand.get("available"):
                return {
                    **cand,
                    "title": f"今天优先攻克\n{cand['knowledge_point']}",
                    "empty_state": False,
                }

        # 2. 全部不可用：回落"基线诊断"卡片，initial_state=True 标识这是首次引导
        baseline = by_mode.get("四科随机综合") or items[-1]
        return {
            **baseline,
            "title": "先完成一次\n408 基线诊断",
            "reason": "你当前还没有稳定的答题或错题记录。系统会先从高频考点生成诊断题，完成后自动形成薄弱点和长期学习记忆。",
            "empty_state": True,
            "initial_state": True,
        }
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).exception("choose_today_plan failed: %s", e)
        return {
            "mode": "四科随机综合",
            "subject": "数据结构",
            "knowledge_point": "线性表",
            "difficulty": "中等",
            "question_type": "选择题",
            "count": 3,
            "available": False,
            "initial": True,
            "title": "先完成一次\n408 基线诊断",
            "reason": "推荐服务暂不可用，请稍后刷新重试。",
            "empty_state": True,
            "initial_state": True,
        }


def normalize_existing_kp_rows(db: Session) -> int:
    """对全库 KP 名称做一次归一化扫描，幂等可重复执行。

    覆盖：KnowledgeMastery / Mistake / QuestionGenerationSession / AnswerRecord 的 subject 和 knowledge_point。
    部署本修复后调用一次，把历史脏数据（如「指令集体系结构(ISA)」）改成「指令集体系结构」，
    让 _kp_key 后续能稳定匹配。返回被改写的行数。
    """
    updated = 0
    for model in (KnowledgeMastery, Mistake, QuestionGenerationSession, AnswerRecord):
        try:
            rows = db.query(model).all()
        except Exception:
            continue
        for row in rows:
            old_sub = getattr(row, "subject", None)
            old_kp = getattr(row, "knowledge_point", None)
            new_sub = (old_sub or "").strip() if old_sub else old_sub
            new_kp = _normalize_kp(old_kp)
            changed = False
            if new_sub and new_sub != old_sub:
                row.subject = new_sub
                changed = True
            if new_kp and new_kp != old_kp:
                row.knowledge_point = new_kp
                changed = True
            if changed:
                updated += 1
    try:
        db.commit()
    except Exception:
        db.rollback()
    return updated
