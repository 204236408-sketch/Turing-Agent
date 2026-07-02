from __future__ import annotations

import contextvars
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, Literal

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from agents.graph_state import QuestionState
from agents.graph_utils import _make_step, _safe_node, _with_timeout
from config import settings
from models import KnowledgePoint, Question, QuestionGenerationSession, KnowledgeMastery
from services.llm_service import LLMResult, chat_json, chat_completion
from services.serialization import question_to_dict
from prompts.hallucination_guard_prompt import render_self_check_prompt

logger = logging.getLogger("question_graph")

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)
_SELF_CHECK_TIMEOUT = 8  # 单题自检超时（秒），超时按 uncertain 处理（速度优化：从 15 缩到 8）

# 内存 LLM 出题缓存：相同 (subject, kp, difficulty, type, count) 组合在 5 分钟内复用结果。
# 速度优化：用户在"智能出题"页面点"再来一组"或短时间内多入口同 KP 出题时避免重复打 LLM。
_LLM_CACHE_TTL = 300  # 秒
_LLM_CACHE: dict[tuple, tuple[float, dict]] = {}


def _llm_cache_get(key: tuple) -> dict | None:
    import time as _t
    hit = _LLM_CACHE.get(key)
    if not hit:
        return None
    ts, data = hit
    if _t.time() - ts > _LLM_CACHE_TTL:
        _LLM_CACHE.pop(key, None)
        return None
    return data


def _llm_cache_set(key: tuple, data: dict) -> None:
    import time as _t
    # 上限 200 条，避免长会话内存爆
    if len(_LLM_CACHE) > 200:
        # 简单清空最早的 50 条
        for k in list(_LLM_CACHE.keys())[:50]:
            _LLM_CACHE.pop(k, None)
    _LLM_CACHE[key] = (_t.time(), data)

_db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)
_GRAPH: StateGraph | None = None

CHOICE_FALLBACK = []  # 已废弃：fallback 改为从 seed_questions.json 按 (subject, kp, vt) 抽题


# 种子题库懒加载缓存：仅在第一次需要时读盘，避免每次 fallback 都做 JSON 解析
_SEED_QUESTIONS_CACHE: list[dict] | None = None


def _load_seed_questions() -> list[dict]:
    """从 data/seed_questions.json 加载全部种子题（仅加载一次）。"""
    global _SEED_QUESTIONS_CACHE
    if _SEED_QUESTIONS_CACHE is not None:
        return _SEED_QUESTIONS_CACHE
    try:
        path = Path(__file__).resolve().parent.parent / "data" / "seed_questions.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            raw = data
        elif isinstance(data, dict):
            # 兼容 {"questions": [...]} 格式
            raw = data.get("questions", [])
        else:
            raw = []
        # 加载时直接过滤元话术模板题，避免历史脏数据进入出题池
        _SEED_QUESTIONS_CACHE = [it for it in raw if not _is_template_question(it)]
        removed = len(raw) - len(_SEED_QUESTIONS_CACHE)
        if removed:
            logger.info("seed_questions.json 加载时过滤元话术模板题 %s 条", removed)
    except Exception as exc:
        logger.warning("加载 seed_questions.json 失败：%s", exc)
        _SEED_QUESTIONS_CACHE = []
    return _SEED_QUESTIONS_CACHE


def _pick_seed_questions(subject: str, knowledge_point: str, vt: str, count: int) -> list[dict]:
    """从种子题库按 (subject, knowledge_point, vt) 抽题。

    五层匹配（按优先级）：
    1) 精确匹配 (subject, kp, vt) — 首选
    2) 模糊匹配 (subject, kp) 不限 vt
    3) section 匹配 (subject, section == kp) — 前端常按小节名出题，seed 中 kp 存的是章节名
    4) 语义匹配 (subject) + 题干含 KP 关键词 — KP 命名在 seed 库中粒度不同（如"内存管理"含"页面置换"题）时兜底
    5) 仍抽不到 → 返回空（让上层走通用模板兜底）

    KP 在匹配前会去除括号后缀（(ISA)/(X86) 等），避免 OCR 推断出的 KP 与 seed 库不一致。
    """
    if count <= 0:
        return []
    pool = _load_seed_questions()
    if not pool:
        return []

    # 归一化 KP: 去除括号后缀
    kp_normalized = _normalize_kp(knowledge_point)
    subject_match = subject or ""

    def _matches_kp_vt(item: dict, *, require_vt: bool) -> bool:
        if item.get("subject") != subject_match:
            return False
        item_kp = _normalize_kp(item.get("knowledge_point", ""))
        if item_kp != kp_normalized:
            return False
        if not require_vt:
            return True
        return item.get("variant_type") == vt or item.get("question_type") == _vt_to_zh(vt)

    # 第 1 步：精确 (subject, kp, vt)
    strict = [dict(it) for it in pool if _matches_kp_vt(it, require_vt=True)]
    if strict:
        return _shuffle_round_robin(strict, count)

    # 第 2 步：模糊 (subject, kp) 不限 vt
    fuzzy = [dict(it) for it in pool if _matches_kp_vt(it, require_vt=False)]
    if fuzzy:
        return _shuffle_round_robin(fuzzy, count)

    # 第 3 步：按 section 字段匹配（解决 seed 中 kp=章节名、section=小节名 的场景）
    section_match = [
        dict(it) for it in pool
        if it.get("subject") == subject_match
        and _normalize_kp(it.get("section", "")) == kp_normalized
    ]
    if section_match:
        # 如果要求具体 vt，优先取同 vt；否则不限 vt
        if vt:
            same_vt = [it for it in section_match if it.get("variant_type") == vt or it.get("question_type") == _vt_to_zh(vt)]
            if same_vt:
                return _shuffle_round_robin(same_vt, count)
        return _shuffle_round_robin(section_match, count)

    # 第 4 步：语义匹配（仅同 subject） + 题干含 KP 的关键概念词
    keywords = _kp_semantic_keywords(kp_normalized)
    if keywords:
        sem = [
            dict(it) for it in pool
            if it.get("subject") == subject_match
            and any(kw in (it.get("question_text") or "") for kw in keywords)
        ]
        if sem:
            same_vt = [it for it in sem if it.get("variant_type") == vt or it.get("question_type") == _vt_to_zh(vt)]
            return _shuffle_round_robin(same_vt or sem, count)

    return []


def _normalize_kp(knowledge_point: str) -> str:
    """KP 名称归一化:去除括号后缀（(ISA)/(X86) 等），方便 seed 库模糊匹配。"""
    if not knowledge_point:
        return ""
    import re
    normalized = re.sub(r"[\(（][^)）]*[\)）]", "", knowledge_point).strip()
    return normalized.replace("的", "")


def _choice_templates_for_kp(subject: str, kp_label: str) -> list[dict]:
    """选择题硬编码模板已废弃，保留空函数避免调用崩溃。
    所有兜底路径都走 refusal 标记，由下游过滤 + 前端提示重试。"""
    return []


# KP → 关键概念词。覆盖 seed 库里 KP 命名与题库实际 KP 不完全一致的情况
# 例如用户指定 KP="页面置换算法"，seed 库 KP="内存管理" 但题干含 LRU/缺页/置换 关键词
_KP_KEYWORDS: dict[str, list[str]] = {
    "页面置换算法": ["LRU", "FIFO", "OPT", "Clock", "缺页", "页框", "置换", "Belady"],
    "进程管理": ["进程", "PCB", "调度", "优先级", "就绪", "阻塞"],
    "内存管理": ["分页", "分段", "虚拟内存", "缺页", "页面"],
    "指令系统": ["指令", "寻址", "操作码", "指令字", "立即寻址"],
    "指令集体系结构": ["指令", "ISA", "指令字", "寻址", "操作码", "RISC", "CISC", "微程序", "定长", "变长", "指令格式", "指令系统"],
    "计算机组成原理": ["CPU", "指令", "存储器", "总线", "微程序", "数据通路", "控制器", "运算器", "寄存器", "Cache", "流水线"],
    "传输层": ["TCP", "UDP", "握手", "挥手", "TIME_WAIT", "端口"],
    "树与二叉树": ["二叉树", "遍历", "前序", "中序", "后序", "线索", "完全二叉树"],
    "线性表": ["顺序表", "链表", "单链表", "双链表", "顺序存储"],
    "栈、队列和数组": ["栈", "队列", "循环队列", "出栈", "入栈", "FIFO", "LIFO"],
    "绪论": ["数据结构", "算法", "时间复杂度", "空间复杂度"],
    "数据链路层": ["CSMA", "帧", "差错控制", "滑动窗口", "MAC", "PPP"],
    "网络层": ["IP", "路由", "子网", "CIDR", "OSPF", "BGP", "ICMP"],
    "中央处理器": ["CPU", "指令周期", "微程序", "流水线", "控制器", "数据通路"],
    "存储系统": ["Cache", "缓存", "主存", "辅存", "虚拟存储", "TLB", "命中率"],
}


def _kp_semantic_keywords(knowledge_point: str) -> list[str]:
    """返回 KP 的关键概念词列表，用于第三层语义匹配。"""
    if not knowledge_point:
        return []
    if knowledge_point in _KP_KEYWORDS:
        return _KP_KEYWORDS[knowledge_point]
    # 兜底：把 KP 名字本身当作关键词
    return [knowledge_point]


def _build_kp_keywords(knowledge_point: str) -> str:
    """为 LLM prompt 构造 KP 关键词清单（逗号分隔）。
    把 KP 名、归一化后的 KP 名、_KP_KEYWORDS 中的扩展关键词合并去重，
    让 LLM 显式知道"必须围绕哪些词出题"，减少 KP 跑题率。"""
    if not knowledge_point:
        return ""
    seen: list[str] = []
    for kw in [knowledge_point, _normalize_kp(knowledge_point), *_kp_semantic_keywords(knowledge_point)]:
        if not kw:
            continue
        kw_clean = str(kw).strip()
        if not kw_clean or kw_clean in seen:
            continue
        seen.append(kw_clean)
    return "、".join(seen[:12])


def _vt_to_zh(vt: str) -> str:
    return {"choice": "选择题", "fill": "填空题", "essay": "简答题", "comprehensive": "综合题"}.get(vt, "选择题")


def _shuffle_round_robin(items: list[dict], count: int) -> list[dict]:
    """轮转抽取：保证每道种子题尽量均匀出现，避免连续多道相同题。"""
    if not items:
        return []
    n = len(items)
    # 起点用确定性偏移（基于调用次数的 hash），避免每次随机洗牌造成用户刷新看到不同题
    start = (int(time.time()) // 30) % n  # 每 30 秒切换一次起点
    picked = [items[(start + i) % n] for i in range(min(count, n))]
    return picked


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()

def _to_variant_type(question_type: str) -> str:
    mapping = {
        "选择题": "choice", "填空题": "fill", "简答题": "essay", "综合题": "comprehensive", "混合": "mixed",
        "choice": "choice", "fill": "fill", "essay": "essay", "comprehensive": "comprehensive",
    }
    return mapping.get(question_type, "choice")


def _all_questions_refused(questions: list[dict]) -> bool:
    if not questions:
        return True
    return all("__REFUSAL__" in str(it.get("question_text", "")) for it in questions)


def _call_llm_for_questions(
    *,
    subject: str,
    knowledge_point: str,
    difficulty: str,
    question_type: str,
    count: int,
    kp_status: str,
    mistake_summary: str,
    misconception_profile: dict,
    mode: str,
    kb_context: str,
    reference_text: str,
    reference_answer: str,
    strict_kb: bool,
    fallback_data: dict,
    kp_keywords: str = "",
):
    """统一封装 LLM 出题调用，使用 ThreadPoolExecutor 限制超时。"""
    from prompts.question_prompt import render_question_prompt

    if not kp_keywords:
        kp_keywords = _build_kp_keywords(knowledge_point)

    # 速度优化：缓存命中直接返回，避免重复打 LLM。
    # kb_context / reference_text 太长不进 key（避免哈希开销），只取前后 32 字符 + 长度作为指纹。
    kb_fingerprint = (kb_context[:32] + "|" + str(len(kb_context))) if kb_context else ""
    ref_fingerprint = (reference_text[:32] + "|" + str(len(reference_text))) if reference_text else ""
    cache_key = (
        subject, knowledge_point, difficulty, question_type, count,
        kb_fingerprint, ref_fingerprint, kp_keywords,
    )
    cached = _llm_cache_get(cache_key)
    if cached:
        logger.info("[llm-cache hit] %s/%s/%s/%s×%d", subject, knowledge_point, question_type, difficulty, count)
        # 命中时 copy 一份 questions 列表，避免外部修改污染缓存
        import copy as _copy
        return LLMResult(
            content="cached",
            used_llm=True,
            error="",
            data=_copy.deepcopy(cached),
        )

    prompt = render_question_prompt(
        subject=subject,
        knowledge_point=knowledge_point,
        difficulty=difficulty,
        question_type=question_type,
        count=count,
        kp_status=kp_status,
        mistake_summary=mistake_summary,
        misconception_profile=json.dumps(misconception_profile, ensure_ascii=False),
        recommend_mode=mode or "自由选择",
        kb_context=kb_context,
        reference_text=reference_text,
        reference_answer=reference_answer,
        strict_kb=strict_kb,
        kp_keywords=kp_keywords,
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            chat_json,
            [
                {
                    "role": "system",
                    "content": "你是 408 考研命题教师。所有事实必须基于用户给出的【知识库参考资料】；未引用即不合格。",
                },
                {"role": "user", "content": prompt},
            ],
            fallback_data,
        )
        try:
            result = future.result(timeout=_NODE_TIMEOUT)
            # 写入缓存（仅缓存 LLM 成功响应）
            if result.used_llm and (result.data or {}).get("questions"):
                _llm_cache_set(cache_key, result.data or {"questions": []})
            return result
        except FutureTimeout:
            pool.shutdown(wait=False)
            logger.error("[timeout] generate_questions: LLM timed out after %ds", _NODE_TIMEOUT)
            return LLMResult(
                content="",
                used_llm=False,
                error=f"timed out after {_NODE_TIMEOUT}s",
                data=fallback_data,
            )


def _vt_for_index(vt: str, index: int) -> str:
    if vt != "mixed":
        return vt
    cycle = ["choice", "fill", "essay", "choice", "comprehensive"]
    return cycle[index % len(cycle)]


def _qtype_for_vt(vt: str, fallback: str = "选择题") -> str:
    return _vt_to_zh(vt) if vt != "mixed" else fallback


def _kp_point_name(point: KnowledgePoint) -> str:
    return (point.section or point.name or "").strip()


def _kp_chapter_name(point: KnowledgePoint) -> str:
    return (point.name or point.parent_name or point.section or "").strip()


def _is_chapter_training(scope: str, mode: str) -> bool:
    return scope == "chapter" or "章节" in (mode or "")


def _chapter_children(db: Session, subject: str, chapter: str = "", chapter_id: int | None = None) -> list[KnowledgePoint]:
    if not db or not subject:
        return []
    chapter_point = None
    if chapter_id:
        chapter_point = (
            db.query(KnowledgePoint)
            .filter(KnowledgePoint.id == chapter_id, KnowledgePoint.is_deleted == False)
            .first()
        )
    if not chapter_point and chapter:
        chapter_point = (
            db.query(KnowledgePoint)
            .filter(
                KnowledgePoint.subject == subject,
                KnowledgePoint.name == chapter,
                KnowledgePoint.is_deleted == False,
            )
            .order_by(KnowledgePoint.level.asc(), KnowledgePoint.id.asc())
            .first()
        )

    candidates = []
    if chapter_point:
        chapter_name = _kp_chapter_name(chapter_point)
        candidates = (
            db.query(KnowledgePoint)
            .filter(
                KnowledgePoint.subject == chapter_point.subject,
                KnowledgePoint.name == chapter_name,
                KnowledgePoint.is_deleted == False,
            )
            .order_by(KnowledgePoint.is_high_frequency.desc(), KnowledgePoint.id.asc())
            .all()
        )
    elif chapter:
        candidates = (
            db.query(KnowledgePoint)
            .filter(
                KnowledgePoint.subject == subject,
                KnowledgePoint.name == chapter,
                KnowledgePoint.is_deleted == False,
            )
            .order_by(KnowledgePoint.is_high_frequency.desc(), KnowledgePoint.id.asc())
            .all()
        )

    seen: set[str] = set()
    children = []
    for point in candidates:
        kp = _kp_point_name(point)
        if not kp or kp in seen:
            continue
        seen.add(kp)
        children.append(point)
    return children


def _point_exists(db: Session, subject: str, point_name: str) -> bool:
    if not db or not subject or not point_name:
        return False
    return (
        db.query(KnowledgePoint.id)
        .filter(
            KnowledgePoint.subject == subject,
            KnowledgePoint.section == point_name,
            KnowledgePoint.is_deleted == False,
        )
        .first()
        is not None
    )


def _rank_target_points(db: Session, user_id: int, subject: str, points: list[KnowledgePoint], count: int) -> list[str]:
    if not points:
        return []
    names = [_kp_point_name(point) for point in points if _kp_point_name(point)]
    rows = (
        db.query(KnowledgeMastery)
        .filter(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.subject == subject,
            KnowledgeMastery.knowledge_point.in_(names),
        )
        .all()
        if db and user_id and names
        else []
    )
    by_name = {row.knowledge_point: row for row in rows}

    def priority(point: KnowledgePoint) -> tuple[int, int, int]:
        name = _kp_point_name(point)
        row = by_name.get(name)
        has_behavior = bool(row and (row.total_answer_count or row.user_mark_status or row.last_answer_time or (row.mastery_score or 0) > 0))
        score = int(row.mastery_score or 0) if row else 0
        weak = int(row.weak_score or 0) if row else 0
        return (0 if not has_behavior else 1, score, -weak)

    ordered = sorted(points, key=priority)
    picked = [_kp_point_name(point) for point in ordered if _kp_point_name(point)]
    return picked[: max(1, min(count, len(picked)))]


def _resolve_difficulty(db: Session | None, user_id: int, subject: str, target_points: list[str], difficulty: str) -> str:
    requested = (difficulty or "中等").strip()
    if requested != "自适应":
        return requested if requested in {"简单", "中等", "较难", "困难"} else "中等"
    if not db or not user_id or not subject or not target_points:
        return "中等"
    rows = (
        db.query(KnowledgeMastery)
        .filter(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.subject == subject,
            KnowledgeMastery.knowledge_point.in_(target_points),
        )
        .all()
    )
    if not rows:
        return "中等"
    weak = max(float(row.weak_score or 0) for row in rows)
    total_answers = sum(int(row.total_answer_count or 0) for row in rows)
    total_correct = sum(int(row.correct_count or 0) for row in rows)
    status_set = {row.final_status for row in rows}
    if weak >= 6 or status_set & {"薄弱点", "不会"}:
        return "简单"
    if weak >= 3 or "不熟" in status_set:
        return "中等"
    if total_answers >= 5 and total_correct / max(total_answers, 1) >= 0.8:
        return "较难"
    return "中等"


def _resolve_generation_target(state: QuestionState) -> dict:
    db = _get_db()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = (state.get("knowledge_point", "") or "").strip()
    chapter = (state.get("chapter", "") or "").strip()
    chapter_id = state.get("chapter_id")
    scope = (state.get("scope", "") or "").strip()
    mode = state.get("mode", "")
    count = state.get("count", 3)

    explicit_chapter = _is_chapter_training(scope, mode)
    chapter_name = chapter or knowledge_point
    children = _chapter_children(db, subject, chapter_name, chapter_id) if db and chapter_name else []
    implicit_chapter = bool(children) and not _point_exists(db, subject, knowledge_point)

    if explicit_chapter or implicit_chapter:
        target_points = _rank_target_points(db, user_id, subject, children, count) if db else []
        if target_points:
            prompt_kp = f"{chapter_name}章节（本组题分别覆盖：{'、'.join(target_points)}）"
            return {
                "scope": "chapter",
                "chapter": chapter_name,
                "target_points": target_points,
                "prompt_knowledge_point": prompt_kp,
            }

    return {
        "scope": scope or "point",
        "chapter": chapter,
        "target_points": [knowledge_point] if knowledge_point else [],
        "prompt_knowledge_point": knowledge_point,
    }


def _prompt_kp(state: QuestionState) -> str:
    return state.get("prompt_knowledge_point") or state.get("knowledge_point", "")


def _target_for_question(state: QuestionState, item: dict, index: int) -> str:
    targets = [p for p in state.get("target_points", []) if p]
    if not targets:
        return state.get("knowledge_point", "")
    raw = (item.get("knowledge_point") or item.get("target_knowledge_point") or "").strip()
    if raw in targets:
        return raw
    return targets[index % len(targets)]


def _build_target_fallback(state: QuestionState, vt: str, subject: str, count: int) -> list[dict]:
    targets = [p for p in state.get("target_points", []) if p] or [state.get("knowledge_point", "")]
    if not targets:
        return _build_fallback(vt, subject, "", count)
    out: list[dict] = []
    per_target = max(1, (count + len(targets) - 1) // len(targets))
    for i in range(count):
        target = targets[i % len(targets)]
        item_vt = _vt_for_index(vt, i)
        pool = _build_fallback(item_vt, subject, target, per_target)
        item = dict(pool[(i // len(targets)) % len(pool)])
        item["target_knowledge_point"] = target
        item["_variant_type"] = item_vt
        item["_question_type"] = _qtype_for_vt(item_vt)
        out.append(item)
    return out


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
    """构造 fallback 题列表（LLM 出题/自检全部失败时使用）。

    优先级：
    1) 从 seed_questions.json 按 (subject, kp, vt) 精确抽题
    2) 精确没抽到 → 按 (subject, kp) 模糊抽题（不限 vt）
    3) 仍抽不到 → 用 fill/essay/comprehensive 的题型通用模板（保留题型骨架，避免出现空白题）
    4) 不再使用「通用 choice 套话模板」（题干与知识点脱钩、质量低劣）

    KP 在匹配前会归一化（去除 (xxx) 后缀），保证 OCR 推断出的 KP 也能匹配到 seed 库。
    """
    if count <= 0:
        return []

    if vt == "mixed":
        out: list[dict] = []
        for i in range(count):
            item_vt = _vt_for_index(vt, i)
            item = dict(_build_fallback(item_vt, subject, knowledge_point, 1)[0])
            item["_variant_type"] = item_vt
            item["_question_type"] = _qtype_for_vt(item_vt)
            out.append(item)
        return out

    # KP 归一化
    kp_normalized = _normalize_kp(knowledge_point)

    # 1 & 2：从种子题库抽题（用归一化 KP）
    picked = _pick_seed_questions(subject, kp_normalized, vt, count)
    if picked and len(picked) >= count:
        return picked[:count]

    # 3：不再使用任何模板题（选择题、填空、简答、综合的元话术模板都已弃用）。
    # 没有真实题目时直接返回 refusal 占位题，由下游过滤掉，前端会展示
    # “当前网络问题，请稍后重试”，避免把元话术题塞给用户。
    out: list[dict] = list(picked or [])
    for _ in range(count):
        out.append({
            "question_text": "__REFUSAL__",
            "options": [],
            "standard_answer": "",
            "explanation": "当前网络问题，请稍后重试。",
            "hints": [],
            "easy_mistakes": "",
            "quality_flag": "deprecated",
        })
    return out


def _structured_templates_for_kp(vt: str, subject: str, kp_label: str, count: int) -> list[dict]:
    """填/简答/综合题硬编码模板已废弃，保留空函数避免调用崩溃。
    所有兜底路径都走 refusal 标记，由下游过滤 + 前端提示重试。"""
    return []


def _with_target_prefix(text: str, subject: str, knowledge_point: str) -> str:
    prefix = f"【{subject} · {knowledge_point}】"
    return text if text.startswith(prefix) else f"{prefix}{text}"


def _questions_match_target(items: list[dict], subject: str, knowledge_point: str) -> bool:
    if not items:
        return False
    kp_normalized = _normalize_kp(knowledge_point)
    target_keywords = {subject, kp_normalized}
    if kp_normalized == "页面置换算法":
        target_keywords.update({"页面", "置换", "缺页", "LRU", "FIFO", "OPT", "Clock"})
    if kp_normalized == "传输层":
        target_keywords.update({"TCP", "UDP", "传输层", "握手", "挥手"})
    if kp_normalized == "树与二叉树":
        target_keywords.update({"树", "二叉树", "遍历", "前序", "中序", "后序"})
    # 指令集体系结构 / 指令系统 KP 关键词兜底
    if kp_normalized == "指令集体系结构" or kp_normalized == "指令系统":
        target_keywords.update({"指令", "ISA", "RISC", "CISC", "寻址", "指令字", "操作码", "微程序"})
    if kp_normalized == "计算机组成原理":
        target_keywords.update({"CPU", "指令", "存储器", "总线", "微程序", "数据通路", "控制器", "运算器", "寄存器", "Cache"})
    text = "\n".join(str(item.get("question_text", "")) for item in items)
    return any(keyword and keyword in text for keyword in target_keywords)


def _questions_match_state_targets(items: list[dict], state: QuestionState, subject: str, fallback_kp: str) -> bool:
    targets = [p for p in state.get("target_points", []) if p]
    if not targets:
        return _questions_match_target(items, subject, fallback_kp)
    return any(_questions_match_target(items, subject, target) for target in targets)


def _get_mastery_text(state: QuestionState) -> str:
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    target_points = state.get("target_points", []) or [knowledge_point]
    db = _get_db()
    if db and subject and target_points and state.get("user_id"):
        rows = (
            db.query(KnowledgeMastery)
            .filter(
                KnowledgeMastery.user_id == state["user_id"],
                KnowledgeMastery.subject == subject,
                KnowledgeMastery.knowledge_point.in_(target_points),
            )
            .all()
        )
        if rows:
            return "；".join(
                f"{row.knowledge_point}: 掌握度={row.final_status}, 正确率={row.correct_count/max(row.total_answer_count,1):.0%}"
                for row in rows[:5]
            )
    return "暂无掌握度数据"


def _get_user_recent_mistakes(state: QuestionState, limit: int = 5) -> str:
    """从 mistake / answer_record 表取用户最近 N 条错题的摘要，注入 prompt。"""
    db = _get_db()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    target_points = state.get("target_points", []) or [knowledge_point]
    if not db or not user_id or not subject or not target_points:
        return "无历史错题"

    try:
        from models import Mistake
        rows = (
            db.query(Mistake)
            .filter(
                Mistake.user_id == user_id,
                Mistake.subject == subject,
                Mistake.knowledge_point.in_(target_points),
                Mistake.status == "active",
            )
            .order_by(Mistake.create_time.desc())
            .limit(limit)
            .all()
        )
    except Exception:
        return "无历史错题"

    if not rows:
        return "无历史错题"

    lines = []
    for i, m in enumerate(rows, 1):
        err_type = m.error_type or "未分类"
        err_reason = (m.error_reason or "")[:80]
        lines.append(f"{i}. [{err_type}] {err_reason}")
    return "\n".join(lines)


def _build_misconception_profile(state: QuestionState, limit: int = 5) -> dict:
    """Build a compact error-pattern profile that can be turned into distractors."""
    db = _get_db()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    target_points = state.get("target_points", []) or [knowledge_point]
    if not db or not user_id or not subject or not target_points:
        return {"items": [], "summary": "无"}

    try:
        from models import Mistake
        rows = (
            db.query(Mistake)
            .filter(
                Mistake.user_id == user_id,
                Mistake.subject == subject,
                Mistake.knowledge_point.in_(target_points),
                Mistake.status == "active",
            )
            .order_by(Mistake.create_time.desc())
            .limit(limit)
            .all()
        )
    except Exception:
        return {"items": [], "summary": "无"}

    items = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        error_type = (row.error_type or "未分类").strip()
        reason = (row.error_reason or "").strip()
        key = (error_type, reason[:40])
        if key in seen:
            continue
        seen.add(key)
        trap = _trap_option_for_error(error_type, reason, row.knowledge_point or knowledge_point)
        items.append({
            "error_type": error_type,
            "error_reason": reason[:120],
            "trap_option": trap,
            "target_hint": _target_hint_for_error(error_type),
        })

    if not items:
        return {"items": [], "summary": "无"}
    summary = "；".join(f"{it['error_type']} -> {it['trap_option']}" for it in items[:3])
    return {"items": items[:3], "summary": summary}


def _target_hint_for_error(error_type: str) -> str:
    if "审题" in error_type:
        return "干扰项应故意忽略题干条件或边界。"
    if "计算" in error_type:
        return "干扰项应体现漏算初始状态、少一步更新或边界次数错误。"
    if "步骤" in error_type:
        return "干扰项应跳过关键状态更新或把步骤顺序颠倒。"
    if "规则" in error_type or "概念" in error_type:
        return "干扰项应混淆相近概念、规则适用条件或判定依据。"
    if "遗忘" in error_type:
        return "干扰项应使用看似熟悉但条件错误的记忆点。"
    return "干扰项应贴近用户最近错因，而不是使用无关选项。"


def _trap_option_for_error(error_type: str, reason: str, knowledge_point: str) -> str:
    text = f"{error_type} {reason} {knowledge_point}"
    if any(word in text for word in ("页面置换", "LRU", "FIFO", "缺页", "页框")):
        if "FIFO" in text or "LRU" in text or "规则" in error_type or "概念" in error_type:
            return "LRU 与 FIFO 的淘汰依据相同，都是淘汰最早进入内存的页面"
        if "命中" in text or "步骤" in error_type:
            return "页面命中时不需要更新 LRU 的最近访问顺序"
        if "计算" in error_type or "缺页" in text:
            return "只有发生页面置换时才算缺页，初始装入页面不计入缺页次数"
        return "发生缺页时一定会执行页面置换，不需要判断是否还有空闲页框"
    if "TCP" in text or "传输层" in text:
        if "顺序" in text or "步骤" in error_type:
            return "TCP 建立连接和释放连接的报文顺序可以互换，只要最终确认即可"
        return "TIME_WAIT 只用于释放本地端口，与旧报文段消失和最后 ACK 重传无关"
    if "二叉树" in text or "遍历" in text:
        return "只要给出前序和后序序列，就一定能唯一确定任意二叉树"
    if "Cache" in text or "存储" in text:
        return "Cache 命中率计算只看 Cache 容量，不需要考虑映射方式和块内地址"
    if "审题" in error_type:
        return "忽略题干给出的限制条件，直接套用最常见结论即可"
    if "计算" in error_type:
        return "只计算发生替换的次数，不需要统计初始状态或边界步骤"
    if "步骤" in error_type:
        return "中间状态不必逐步更新，只要最后结论形式正确即可"
    if "规则" in error_type or "概念" in error_type:
        return f"{knowledge_point} 的相近概念可以直接互换使用"
    return f"只记住 {knowledge_point} 的名称即可，不需要判断条件和边界"


def _llm_generate_trap_options_async(
    subject: str,
    knowledge_point: str,
    items: list[dict],
):
    """速度优化：让 LLM 生成 trap_option 的调用立即返回 future，由调用方在主 LLM 完成后 join，
    实现 trap LLM 与主 LLM 并行。
    返回 None 表示"错因 < 2 或无可调 LLM"，调用方应跳过 join。"""
    if not items or len(items) < 2 or not subject or not knowledge_point:
        return None
    try:
        from prompts.question_prompt import render_trap_options_prompt
        prompt = render_trap_options_prompt(subject=subject, knowledge_point=knowledge_point, items=items)
    except Exception as exc:
        logger.warning("render_trap_options_prompt 不可用：%s", exc)
        return None

    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="trap")
    future = pool.submit(
        chat_json,
        [
            {"role": "system", "content": "你是 408 考研命题教师。只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        {"traps": [{"error_type": it.get("error_type", ""), "trap_option": it.get("trap_option", "")} for it in items]},
    )
    # 把 pool 挂到 future 上供 join 时 shutdown
    future._trap_pool = pool
    return future


def _llm_generate_trap_options(
    subject: str,
    knowledge_point: str,
    items: list[dict],
    preheated_future=None,
) -> list[dict]:
    """让 LLM 为每个错因生成针对该知识点的"看似合理但实际错误"干扰项文本。
    仅当 LLM 成功时覆盖原 trap_option；失败/超时则保持硬编码默认值。
    preheated_future: 由 _llm_generate_trap_options_async 预先提交的 future，传入时直接 join。
    """
    if not items:
        return items
    if preheated_future is None:
        preheated_future = _llm_generate_trap_options_async(subject, knowledge_point, items)
    if preheated_future is None:
        return items

    try:
        result = preheated_future.result(timeout=_NODE_TIMEOUT)
    except FutureTimeout:
        logger.info("LLM 生成 trap_option 超时，回退硬编码")
        return items
    except Exception as exc:
        logger.info("LLM 生成 trap_option 异常：%s", exc)
        return items
    finally:
        pool = getattr(preheated_future, "_trap_pool", None)
        if pool:
            try:
                pool.shutdown(wait=False)
            except Exception:
                pass

    traps_raw = ((result.data or {}).get("traps") or []) if result.used_llm else []
    if not traps_raw:
        return items

    by_type = {str(t.get("error_type", "")).strip(): str(t.get("trap_option", "")).strip() for t in traps_raw if t.get("error_type")}
    for it in items:
        et = str(it.get("error_type", "")).strip()
        new_text = by_type.get(et)
        if new_text and len(new_text) <= 200:
            it["trap_option"] = new_text
    return items


def _apply_misconception_traps(
    raw_questions: list[dict],
    profile: dict,
    subject: str = "",
    knowledge_point: str = "",
    trap_future=None,
) -> list[dict]:
    items = (profile or {}).get("items") or []
    if not raw_questions or not items:
        return raw_questions

    # 优先让 LLM 为每个错因生成针对该知识点的"陷阱选项"；失败时回退到硬编码。
    # 速度优化：trap_future 由调用方在主 LLM 之前预热，此处 join 即可。
    items = _llm_generate_trap_options(subject, knowledge_point, items, preheated_future=trap_future)

    trap_index = 0
    for q in raw_questions:
        options = q.get("options") or []
        if not isinstance(options, list) or len(options) < 2:
            continue
        answer = str(q.get("standard_answer", "")).strip().upper()
        if answer not in {"A", "B", "C", "D"}:
            continue
        trap = items[trap_index % len(items)]
        trap_text = trap.get("trap_option") or ""
        if not trap_text:
            continue
        answer_idx = ord(answer) - ord("A")
        replace_idx = next((i for i in range(len(options)) if i != answer_idx), None)
        if replace_idx is None:
            continue
        label = chr(ord("A") + replace_idx)
        options[replace_idx] = f"{label}. {trap_text}"
        q["options"] = options
        existing_easy = (q.get("easy_mistakes") or "").strip()
        addition = f"针对最近错因「{trap.get('error_type', '未分类')}」设置干扰项：{trap_text}。"
        q["easy_mistakes"] = f"{existing_easy} {addition}".strip()[:500]
        explanation = (q.get("explanation") or "").strip()
        if trap_text not in explanation:
            q["explanation"] = f"{explanation} 干扰项“{trap_text}”错在：{trap.get('target_hint', '没有满足题干条件。')}".strip()
        trap_index += 1
    return raw_questions


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度。空向量返回 0。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _text_signature(text: str) -> str:
    """生成题干的轻量指纹（取前 32 字 + 全部中文实词），用于 LLM embedding 不可用时的去重兜底。"""
    if not text:
        return ""
    head = text[:32]
    keep = "".join(c for c in text if '\u4e00' <= c <= '\u9fff' or c.isalnum())
    return (head + "|" + keep[:64]).lower()


def _jaccard(a: str, b: str) -> float:
    """字符串集合的 Jaccard 相似度（兜底方案，不依赖 embedding 服务）。"""
    if not a or not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _question_identity(item: dict) -> str:
    """Stable key for exact duplicate questions, including choices when present."""
    text = str(item.get("question_text", ""))
    options = item.get("options") or []
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = [options]
    if not options:
        return ""
    option_text = "|".join(str(opt) for opt in options)
    return _text_signature(f"{text}|{option_text}")


def _unique_question_items(items: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[str] = set()
    for item in items or []:
        key = _question_identity(item)
        if not key:
            unique.append(item)
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _has_generic_bad_options(options: list[Any]) -> bool:
    """Reject meta/exam-form choices that are not real knowledge-point distractors."""
    bad_phrases = (
        "仅考查定义背诵",
        "只考计算过程",
        "只考综合应用",
        "仅以选择题形式出现",
        "仅以大题形式出现",
        "不属于 408 考纲范围",
        "不属于408考纲范围",
        "只有 1 个固定步骤",
        "步骤之间无任何关联",
        "步骤顺序不可调整",
    )
    joined = "\n".join(str(opt) for opt in options or [])
    return any(phrase in joined for phrase in bad_phrases)


# 元话术模板题的特征：题面/解析/易错点直接描述考点类型、考查方式或复习策略，
# 而不是具体知识点内容。这类题目直接被过滤掉，避免展示给用户。
_TEMPLATE_BAD_PATTERNS: tuple[str, ...] = (
    "的复习应优先围绕",
    "的核心内容及一个常见易错点",
    "完成下列小问",
    "易只写概念名称，缺少条件、流程或对比说明",
    "易把综合题答成单句定义，缺少分层说明",
    "易只背",
    "请注意概念成立的前提与边界",
    "易把 .* 的概念理解片面化",
    # 增量：seed 题库里的"X 的核心考查对象通常包括：____"模板（填空题元话术）
    "的核心考查对象通常包括",
    "的考点通常包括",
    "的高频考点为",
    "的常见考法包括",
    "的常见考点包括",
    "应围绕关键词",
    "应重点关注",
    "应掌握的核心是",
    "出题角度通常为",
    "的常见出题形式",
)


def _is_template_question(item: dict) -> bool:
    """检测元话术模板题：题面、解析、易错点出现模板特征短语。"""
    text = "\n".join(
        [
            str(item.get("question_text", "")),
            str(item.get("standard_answer", "")),
            str(item.get("explanation", "")),
            str(item.get("easy_mistakes", "")),
            "\n".join(str(h) for h in item.get("hints", []) or []),
        ]
    )
    return any(pat in text for pat in _TEMPLATE_BAD_PATTERNS)


def analyze_user_state(state: QuestionState) -> dict:
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    mode = state.get("mode", "")
    start = time.time()

    mastery_text = _get_mastery_text(state)
    mistake_summary = _get_user_recent_mistakes(state, limit=5)
    misconception_profile = _build_misconception_profile(state, limit=5)
    out = f"user_id={user_id}, mode={mode}, {mastery_text}, traps={len(misconception_profile.get('items', []))}"
    step = _make_step("analyze_user_state", f"user_id={user_id}, mode={mode}", out, "success", start)
    return {
        "mastery_text": mastery_text,
        "mistake_summary": mistake_summary,
        "misconception_profile": misconception_profile,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def select_target(state: QuestionState) -> dict:
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    target_info = _resolve_generation_target(state)
    target_points = target_info.get("target_points", [])
    prompt_kp = target_info.get("prompt_knowledge_point") or knowledge_point
    resolved_difficulty = _resolve_difficulty(
        _get_db(),
        state.get("user_id", 0),
        subject,
        target_points or [knowledge_point],
        difficulty,
    )

    step = _make_step(
        "select_target",
        f"subject={subject}, kp={knowledge_point}",
        f"type={question_type}, diff={difficulty}->{resolved_difficulty}, targets={target_points or [knowledge_point]}",
        "success",
        start,
    )
    return {
        **target_info,
        "difficulty": resolved_difficulty,
        "requested_difficulty": difficulty,
        "prompt_knowledge_point": prompt_kp,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_question_context(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    target_points = state.get("target_points", []) or [knowledge_point]

    context = []
    if db and subject and target_points:
        # 只参考"已验证 + 质量分 ≥ 60 + 未被多用户标错"的题，避免 LLM 自噬 + 排除被反馈有误的题
        existing = (
            db.query(Question)
            .filter(
                Question.subject == subject,
                Question.knowledge_point.in_(target_points),
                Question.is_deleted == False,
                Question.is_verified == True,
                Question.quality_flag == "normal",
                Question.quality_score >= 60,
                (Question.reported_count == None) | (Question.reported_count < 2),
            )
            .order_by(Question.quality_score.desc(), Question.create_time.desc())
            .limit(3)
            .all()
        )
        context = [question_to_dict(q) for q in existing]

    out = f"found {len(context)} existing questions"
    step = _make_step("retrieve_question_context", f"subject={subject}, kp={knowledge_point}", out, "success", start)
    return {
        "context": context,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _build_rag_text(state: QuestionState) -> tuple[str, list[str]]:
    """调用 Chroma RAG 检索，返回格式化文本 + 原始片段列表（用于自检节点复用）。"""
    db = _get_db()
    subject = state.get("subject", "")
    target_points = [p for p in state.get("target_points", []) if p] or [state.get("knowledge_point", "")]
    if not db or not subject or not target_points:
        return "", []
    try:
        from services.rag_service import retrieve_knowledge
        docs = []
        for target in target_points[:3]:
            rag_result = retrieve_knowledge(
                db=db,
                query=f"{subject} {target}",
                limit=2,
                subject_filter=subject,
                kp_filter=target,
            )
            raw_docs = (
                (rag_result or {}).get("documents")
                or (rag_result or {}).get("items")
                or []
            )[:2]
            for d in raw_docs:
                if isinstance(d, dict):
                    docs.append(d.get("content", "") or d.get("text", ""))
                else:
                    docs.append(str(d))
            if len(docs) >= 4:
                break
        if not docs:
            return "", []
        rag_text = "\n\n【知识库参考资料】（这是你出题的唯一事实来源）\n"
        for i, content in enumerate(docs, 1):
            rag_text += f"[{i}] {content[:300]}\n"
        return rag_text, docs
    except Exception as e:
        logger.warning("RAG 检索失败（不影响出题）: %s", e)
        return "", []


def _build_question_bank_text(context: list[dict]) -> str:
    """题库参考段（含强约束：禁止完全重复）。"""
    if not context:
        return ""
    text = "\n\n【题库参考】（学习已有题目的考法，但禁止原样复刻，题干关键词重合度需 < 30%）\n"
    for i, item in enumerate(context[:3], 1):
        q_text = item.get("question_text", "")[:200]
        opts = item.get("options", [])
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = []
        opts_text = "  ".join(opts[:4]) if opts else ""
        ans = item.get("standard_answer", "")
        text += f"[{i}] {q_text}  {opts_text}  [答案:{ans}]\n"
    return text


def generate_questions_node(state: QuestionState) -> dict:
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = _prompt_kp(state)
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    context = state.get("context", [])
    mastery_text = state.get("mastery_text", "暂无掌握度数据")
    mistake_summary = state.get("mistake_summary", "无历史错题")
    misconception_profile = state.get("misconception_profile", {"items": [], "summary": "无"})
    vt = _to_variant_type(question_type)
    fallback_data = {"questions": _build_target_fallback(state, vt, subject, count)}

    # 速度优化：trap_option LLM 与主 LLM 并行预热。主 LLM 通常 5~10s，
    # 提前让 trap LLM 在后台跑，等主 LLM 完成后 join 时大概率已就绪。
    trap_future = _llm_generate_trap_options_async(
        subject=subject,
        knowledge_point=knowledge_point,
        items=(misconception_profile or {}).get("items") or [],
    )

    # 1. 知识库 RAG（注入 prompt 用作事实约束）
    rag_text, rag_docs = _build_rag_text(state)

    # 2. 题库参考（已 verified 的种子题）
    bank_text = _build_question_bank_text(context)

    # 3. 检测知识库是否为空：为空时启用宽松模式，允许 LLM 基于通用考纲出题
    has_kb = bool((rag_text + bank_text).strip())
    loose_mode = not has_kb
    kb_context = (rag_text + bank_text).strip() or "（知识库与题库均无内容）"

    # 4. 用新 prompt 模板组装（带 hallucination 约束、kb_ref 强制、难度量化）
    from prompts.question_prompt import render_question_prompt
    prompt_question_type = "选择题" if question_type == "混合" else question_type
    prompt = render_question_prompt(
        subject=subject,
        knowledge_point=knowledge_point,
        difficulty=difficulty,
        question_type=prompt_question_type,
        count=count,
        kp_status=mastery_text,
        mistake_summary=mistake_summary,
        misconception_profile=json.dumps(misconception_profile, ensure_ascii=False),
        recommend_mode=mode or "自由选择",
        kb_context=kb_context,
        reference_text=state.get("reference_text", "") or "",
        reference_answer=state.get("reference_answer", "") or "",
        strict_kb=not loose_mode,
    )

    if vt == "mixed":
        # 混合题型也走 LLM：把每道题的题型拆开传给 LLM，避免依赖本地种子题库
        mixed_items: list[dict] = []
        cycle = ["choice", "fill", "essay", "choice", "comprehensive"]
        per_type_counts: dict[str, int] = {}
        for i in range(count):
            item_vt = cycle[i % len(cycle)]
            per_type_counts[item_vt] = per_type_counts.get(item_vt, 0) + 1
        mixed_llm = LLMResult(content="", used_llm=False, error="", data={"questions": []})
        # 速度优化：mixed 题型的 4 个子题型 LLM 调用改为 ThreadPoolExecutor 并行
        sub_args = []
        for sub_vt, sub_count in per_type_counts.items():
            sub_type = {"choice": "选择题", "fill": "填空题", "essay": "简答题", "comprehensive": "综合题"}.get(sub_vt, "选择题")
            sub_args.append((sub_vt, sub_type, sub_count))
        with ThreadPoolExecutor(max_workers=min(4, len(sub_args))) as pool:
            futures = {
                pool.submit(
                    _call_llm_for_questions,
                    subject=subject,
                    knowledge_point=knowledge_point,
                    difficulty=difficulty,
                    question_type=sub_type,
                    count=sub_count,
                    kp_status=mastery_text,
                    mistake_summary=mistake_summary,
                    misconception_profile=misconception_profile,
                    mode=mode,
                    kb_context=kb_context,
                    reference_text=state.get("reference_text", "") or "",
                    reference_answer=state.get("reference_answer", "") or "",
                    strict_kb=not loose_mode,
                    fallback_data={"questions": []},
                ): (sub_vt, sub_type)
                for sub_vt, sub_type, sub_count in sub_args
            }
            for fut, (sub_vt, _sub_type) in futures.items():
                try:
                    sub_llm = fut.result(timeout=_NODE_TIMEOUT)
                except Exception as exc:
                    logger.warning("mixed 子题型 %s LLM 并行调用失败：%s", sub_vt, exc)
                    sub_llm = LLMResult(content="", used_llm=False, error=str(exc), data={"questions": []})
                sub_questions = (sub_llm.data or {}).get("questions") or []
                for q in sub_questions:
                    q["_variant_type"] = sub_vt
                mixed_items.extend(sub_questions)
                if sub_llm.used_llm:
                    mixed_llm.used_llm = True
                if sub_llm.error and not mixed_llm.error:
                    mixed_llm.error = sub_llm.error
        mixed_llm.data = {"questions": mixed_items}
        llm = mixed_llm
    else:
        llm = _call_llm_for_questions(
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            question_type=prompt_question_type,
            count=count,
            kp_status=mastery_text,
            mistake_summary=mistake_summary,
            misconception_profile=misconception_profile,
            mode=mode,
            kb_context=kb_context,
            reference_text=state.get("reference_text", "") or "",
            reference_answer=state.get("reference_answer", "") or "",
            strict_kb=not loose_mode,
            fallback_data=fallback_data,
        )

    raw_questions = (llm.data or fallback_data).get("questions") or fallback_data["questions"]
    raw_questions = _unique_question_items(raw_questions)

    # LLM 保底出题：题数不足时再次调用 LLM 补齐，不使用元话术模板兜底
    if len(raw_questions) < count and not _all_questions_refused(raw_questions):
        need = count - len(raw_questions)
        if vt == "mixed":
            # mixed 题型按 cycle 拆分补题请求，速度优化：4 个子题型并行调 LLM
            cycle = ["choice", "fill", "essay", "choice", "comprehensive"]
            per_type_counts: dict[str, int] = {}
            for i in range(need):
                item_vt = cycle[(len(raw_questions) + i) % len(cycle)]
                per_type_counts[item_vt] = per_type_counts.get(item_vt, 0) + 1
            sub_args = []
            for sub_vt, sub_count in per_type_counts.items():
                sub_type = {"choice": "选择题", "fill": "填空题", "essay": "简答题", "comprehensive": "综合题"}.get(sub_vt, "选择题")
                sub_args.append((sub_vt, sub_type, sub_count))
            with ThreadPoolExecutor(max_workers=min(4, len(sub_args))) as pool:
                futures = {
                    pool.submit(
                        _call_llm_for_questions,
                        subject=subject,
                        knowledge_point=knowledge_point,
                        difficulty=difficulty,
                        question_type=sub_type,
                        count=sub_count,
                        kp_status=mastery_text,
                        mistake_summary=mistake_summary,
                        misconception_profile=misconception_profile,
                        mode=mode,
                        kb_context=kb_context,
                        reference_text=state.get("reference_text", "") or "",
                        reference_answer=state.get("reference_answer", "") or "",
                        strict_kb=not loose_mode,
                        fallback_data={"questions": []},
                    ): sub_vt
                    for sub_vt, sub_type, sub_count in sub_args
                }
                for fut, sub_vt in futures.items():
                    try:
                        retry_llm = fut.result(timeout=_NODE_TIMEOUT)
                    except Exception as exc:
                        logger.warning("mixed refill 子题型 %s LLM 并行调用失败：%s", sub_vt, exc)
                        retry_llm = LLMResult(content="", used_llm=False, error=str(exc), data={"questions": []})
                    retry_questions = (retry_llm.data or {}).get("questions") or []
                    for q in retry_questions:
                        q.setdefault("_variant_type", sub_vt)
                    raw_questions = _unique_question_items(list(raw_questions) + retry_questions)
                    if retry_llm.used_llm:
                        llm.used_llm = True
            logger.info("LLM 第一次出题 %d 道，未达 %d 道，mixed 拆分并行再次调用 LLM 补 %d 道，合计 %d 道", max(0, count - need), count, need, len(raw_questions))
        else:
            retry_llm = _call_llm_for_questions(
                subject=subject,
                knowledge_point=knowledge_point,
                difficulty=difficulty,
                question_type=prompt_question_type,
                count=need,
                kp_status=mastery_text,
                mistake_summary=mistake_summary,
                misconception_profile=misconception_profile,
                mode=mode,
                kb_context=kb_context,
                reference_text=state.get("reference_text", "") or "",
                reference_answer=state.get("reference_answer", "") or "",
                strict_kb=not loose_mode,
                fallback_data={"questions": []},
            )
            retry_questions = (retry_llm.data or {}).get("questions") or []
            if retry_questions:
                raw_questions = _unique_question_items(list(raw_questions) + retry_questions)
                if retry_llm.used_llm:
                    llm.used_llm = True
                    llm.error = llm.error or ""
            logger.info("LLM 第一次出题 %d 道，未达 %d 道，再次调用 LLM 补 %d 道，合计 %d 道", max(0, count - need), count, need, len(raw_questions))

    # 最终仍不足 count 时，用 __REFUSAL__ 占位到指定数量，让下游过滤 + 前端提示重试
    if len(raw_questions) < count:
        lack = count - len(raw_questions)
        for _ in range(lack):
            raw_questions.append({
                "question_text": "__REFUSAL__",
                "options": [],
                "standard_answer": "",
                "explanation": "当前网络问题，请稍后重试。",
                "hints": [],
                "easy_mistakes": "",
                "quality_flag": "deprecated",
            })
        logger.info("LLM 多次重试仍不足 %d 道，剩余 %d 道用 refusal 占位", count, lack)
    raw_questions = _unique_question_items(raw_questions)[:count]

    # 检测 LLM 主动拒答（知识库无内容时按 prompt 规则应输出 __REFUSAL__）
    refused_count = sum(1 for it in raw_questions if "__REFUSAL__" in str(it.get("question_text", "")))
    all_refused = refused_count > 0 and refused_count == len(raw_questions)
    if all_refused:
        # 全部拒答时不再回落到元话术模板题；保持 __REFUSAL__ 让上游过滤。
        # 知识库真正有内容的场景下，supplement 阶段会被 `_unique_question_items` 和
        # 下游 `_has_generic_bad_options` 校验过滤掉，避免低质量题面展示给用户。
        logger.info("LLM 全部拒答（知识库无 %s/%s），保留 refusal 标记由上游过滤", subject, knowledge_point)
        llm.used_llm = False
        llm.error = f"知识库暂无 {knowledge_point} 资料，且未生成可用题。"
    elif llm.used_llm and not _questions_match_state_targets(raw_questions, state, subject, knowledge_point):
        # 题目与目标 KP 不匹配：宁可返回空也不要塞不相关的题。
        logger.info("LLM 题目与 %s/%s 不匹配，清空让上游过滤", subject, knowledge_point)
        llm.used_llm = False
        llm.error = f"AI 题目与 {knowledge_point} 不匹配，已过滤。"
        raw_questions = []

    raw_questions = _apply_misconception_traps(raw_questions, misconception_profile, subject=subject, knowledge_point=knowledge_point, trap_future=trap_future)

    if vt in ("fill", "essay", "mixed"):
        for idx, item in enumerate(raw_questions):
            item_vt = item.get("_variant_type") or _vt_for_index(vt, idx)
            if item_vt not in ("fill", "essay"):
                continue
            item.pop("options", None)
            ans = item.get("standard_answer", "").strip()
            if len(ans) == 1 and 'A' <= ans <= 'Z':
                item["standard_answer"] = item.get("explanation", ans)
    if vt in ("comprehensive", "mixed"):
        for idx, item in enumerate(raw_questions):
            item_vt = item.get("_variant_type") or _vt_for_index(vt, idx)
            if item_vt != "comprehensive":
                continue
            item.pop("options", None)

    # 把 RAG 原文传给下游自检节点用
    step_status = "success" if llm.used_llm else "degraded"
    step_out = f"generated {len(raw_questions)} {question_type} via {'LLM' if llm.used_llm else 'fallback'}"
    step = _make_step("generate_questions", f"count={count}, type={question_type}", step_out, step_status, start)

    return {
        "raw_questions": raw_questions,
        "variant_type": vt,
        "llm_result": llm,
        "llm_used": llm.used_llm,
        "llm_error": llm.error,
        "rag_docs": rag_docs,
        "loose_mode": loose_mode,
        "all_refused": all_refused,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def deduplicate_questions(state: QuestionState) -> dict:
    """对 LLM 生成的题做"和已有 verified 题 + 题干彼此"的相似度去重。

    优先级：embedding 相似度 > 0.85 视为重复；若 embedding 不可用，回退到 Jaccard。
    """
    start = time.time()
    raw_questions = state.get("raw_questions", []) or []
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    # 优先剔除元话术模板题：这类题不是真正的考点问题，会被计入"重复"或后续被过滤。
    if raw_questions:
        pre_filter = [it for it in raw_questions if not _is_template_question(it)]
        template_removed = len(raw_questions) - len(pre_filter)
        if template_removed:
            logger.info("deduplicate 剔除元话术模板题: %s 条", template_removed)
        raw_questions = pre_filter
    if not raw_questions:
        return {
            "raw_questions": [],
            "dedup_removed": 0,
            "agent_steps": state.get("agent_steps", []) + [
                _make_step("deduplicate", "empty input", "skipped", "success", start)
            ],
        }

    db = _get_db()
    existing_texts: list[str] = []
    if db and subject and knowledge_point:
        # 1) 已 verified 的种子题（参考池）
        rows = (
            db.query(Question)
            .filter(
                Question.subject == subject,
                Question.knowledge_point == knowledge_point,
                Question.is_deleted == False,
                Question.is_verified == True,
            )
            .order_by(Question.create_time.desc())
            .limit(20)
            .all()
        )
        existing_texts = [r.question_text for r in rows if r.question_text]
        # 2) 用户近 30 天自己生成的未 verified 题（避免同一知识点连续出题时出现重复题）
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_rows = (
            db.query(Question)
            .filter(
                Question.subject == subject,
                Question.knowledge_point == knowledge_point,
                Question.is_deleted == False,
                Question.is_verified == False,
                Question.create_time >= recent_cutoff,
            )
            .order_by(Question.create_time.desc())
            .limit(30)
            .all()
        )
        existing_texts.extend(r.question_text for r in recent_rows if r.question_text)

    # 拼成批量 embedding 输入：已有题 + 当前新题
    new_texts = [str(it.get("question_text", ""))[:200] for it in raw_questions]
    all_texts = existing_texts + new_texts
    embeddings: list[list[float]] = []
    use_embedding = False
    try:
        from services.vector_embedding_service import embed_texts
        result = embed_texts(all_texts)
        if result.get("success") and result.get("embeddings"):
            embeddings = result["embeddings"]
            use_embedding = True
    except Exception as e:
        logger.warning("deduplicate embedding 不可用，回退到 Jaccard: %s", e)

    threshold = 0.85
    keep: list[dict] = []
    removed = 0
    new_emb = embeddings[len(existing_texts):] if use_embedding else []
    existing_emb = embeddings[:len(existing_texts)] if use_embedding else []

    for i, item in enumerate(raw_questions):
        is_dup = False
        text = str(item.get("question_text", ""))
        if use_embedding and i < len(new_emb):
            # 和已有题去重
            for ee in existing_emb:
                if _cosine_sim(new_emb[i], ee) > threshold:
                    is_dup = True
                    break
            # 和已保留的新题去重
            if not is_dup:
                kept_idx = [raw_questions.index(k) for k in keep]
                for ki in kept_idx:
                    if ki < len(new_emb) and _cosine_sim(new_emb[i], new_emb[ki]) > threshold:
                        is_dup = True
                        break
        else:
            # Jaccard 兜底
            sig = _text_signature(text)
            for ex in existing_texts:
                if _jaccard(sig, _text_signature(ex)) > 0.5:
                    is_dup = True
                    break
            if not is_dup:
                for k in keep:
                    if _jaccard(sig, _text_signature(str(k.get("question_text", "")))) > 0.5:
                        is_dup = True
                        break
        if is_dup:
            removed += 1
        else:
            keep.append(item)

    step = _make_step(
        "deduplicate",
        f"input={len(raw_questions)}",
        f"kept={len(keep)} removed={removed} backend={'embedding' if use_embedding else 'jaccard'}",
        "success",
        start,
    )
    return {
        "raw_questions": keep,
        "dedup_removed": removed,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def self_check_questions(state: QuestionState) -> dict:
    """LLM 自检：对照 RAG 片段判断每道题的事实正确性。

    只有当 LLM 真正被使用过（llm_used=True）且 RAG 文档非空时才自检，否则跳过。
    不通过的题会被剔除（通过 state['raw_questions'] 截断），由 validate 之后的 fallback 补足。
    """
    start = time.time()
    raw_questions = state.get("raw_questions", []) or []
    rag_docs = state.get("rag_docs", []) or []
    llm_used = state.get("llm_used", False)

    if not llm_used or not raw_questions or not rag_docs:
        return {
            "raw_questions": raw_questions,
            "self_check_report": [],
            "self_check_removed": 0,
            "agent_steps": state.get("agent_steps", []) + [
                _make_step("self_check", "skipped", "no LLM or no RAG", "success", start)
            ],
        }

    kb_context = "\n".join(f"[{i+1}] {d[:300]}" for i, d in enumerate(rag_docs[:3]))
    kept: list[dict] = []
    report: list[dict] = []
    removed = 0

    # 速度优化：自检原是逐题串行；改为 ThreadPoolExecutor 并行（最多 4 路）
    # 跳过明显为 fallback 的题（带 __REFUSAL__）
    items_to_check = [it for it in raw_questions if "__REFUSAL__" not in str(it.get("question_text", ""))]

    def _check_one(item: dict) -> tuple[dict, dict]:
        prompt = render_self_check_prompt(
            question_json=json.dumps(item, ensure_ascii=False, indent=2)[:1500],
            kb_context=kb_context,
        )
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                chat_json,
                [
                    {
                        "role": "system",
                        "content": "你是 408 题目质检员。仅输出结构化 JSON。",
                    },
                    {"role": "user", "content": prompt},
                ],
                {"verdict": "uncertain", "issues": [], "suggestion": ""},
            )
            try:
                result = future.result(timeout=_SELF_CHECK_TIMEOUT)
            except FutureTimeout:
                pool.shutdown(wait=False)
                result = LLMResult(content="", used_llm=False, error="timeout", data={"verdict": "uncertain", "issues": [], "suggestion": ""})
        return item, {
            "question_snippet": str(item.get("question_text", ""))[:80],
            "verdict": str((result.data or {}).get("verdict", "uncertain")).lower(),
            "issues": (result.data or {}).get("issues", []),
        }

    with ThreadPoolExecutor(max_workers=min(4, max(1, len(items_to_check)))) as pool:
        for item, r in pool.map(_check_one, items_to_check, chunksize=1):
            report.append(r)
            if r["verdict"] == "pass":
                kept.append(item)
            else:
                removed += 1
                logger.info("self_check removed question: %s, verdict=%s", str(item.get("question_text", ""))[:50], r["verdict"])

    step = _make_step(
        "self_check",
        f"input={len(raw_questions)}",
        f"kept={len(kept)} removed={removed}",
        "success" if removed == 0 else "warning",
        start,
    )
    return {
        "raw_questions": kept,
        "self_check_report": report,
        "self_check_removed": removed,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _assess_difficulty_match(item: dict, difficulty: str) -> bool:
    """难度感知：基于题干的'显性计算/推理信号'粗略判断。

    简单：题干无计算/推理信号或仅 1 处
    中等：2~4 处
    较难：5~6 处
    困难：≥7 处 或 含"综合""分析"等综合信号
    判定不通过表示难度不匹配，建议降级或重新生成。
    """
    text = str(item.get("question_text", ""))
    options = item.get("options", []) or []
    full = text + " " + " ".join(str(o) for o in options)
    if not full.strip():
        return True  # 空内容留给其他校验处理

    signal_keywords = (
        "计算", "推导", "证明", "分析", "综合", "步骤", "缺页", "耗时", "比较",
        "假设", "若", "则", "等于", "依次", "通过", "分页", "调度", "寻址",
    )
    signals = sum(1 for kw in signal_keywords if kw in full)

    if difficulty == "简单":
        return signals <= 2
    if difficulty == "中等":
        return 1 <= signals <= 5
    if difficulty == "较难":
        return 2 <= signals <= 8
    if difficulty == "困难":
        return signals >= 3 or any(kw in full for kw in ("综合", "分析", "证明"))
    return True


def validate_questions(state: QuestionState) -> dict:
    start = time.time()
    raw_questions = state.get("raw_questions", [])
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    vt = _to_variant_type(question_type)

    valid = True
    reasons: list[str] = []
    for idx, item in enumerate(raw_questions):
        item_vt = item.get("_variant_type") or _vt_for_index(vt, idx)
        if not item.get("question_text", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 题干为空")
        if not item.get("standard_answer", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 无标准答案")
        if not item.get("explanation", "").strip():
            reasons.append(f"#{idx+1} 解析为空")
        options = item.get("options", [])
        if item_vt == "choice":
            if not options or len(options) != 4:
                valid = False
                reasons.append(f"#{idx+1} 选项数量为 {len(options) if options else 0}，应为 4")
            else:
                # 答案必须落在 A/B/C/D 之一
                ans = (item.get("standard_answer") or "").strip().upper()
                if ans not in {"A", "B", "C", "D"}:
                    valid = False
                    reasons.append(f"#{idx+1} 选择题答案 {ans!r} 不在 A/B/C/D")
                if _has_generic_bad_options(options):
                    valid = False
                    reasons.append(f"#{idx+1} 选择题选项过于泛化,未形成真实知识点干扰项")
        if item_vt in ("fill", "essay") and not item.get("standard_answer", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 缺少标准答案文本")
        if item_vt == "comprehensive" and not item.get("sub_questions"):
            reasons.append(f"#{idx+1} 综合题缺少子问题")
        # 难度感知（不通过仅记 reason，不直接判 valid，给下游降级机会）
        if not _assess_difficulty_match(item, difficulty):
            reasons.append(f"#{idx+1} 难度信号与 {difficulty} 不匹配")

    if valid and not _questions_match_state_targets(raw_questions, state, subject, knowledge_point):
        valid = False
        reasons.append("知识点不匹配")

    reason_text = "valid" if valid else "; ".join(reasons)
    step = _make_step("validate_questions", f"{len(raw_questions)} questions", reason_text, "success" if valid else "warning", start)
    return {
        "questions_valid": valid,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _refill_questions(state: QuestionState) -> dict:
    """题量不足时（被自检/去重剔除）再次调用 LLM 补足，使最终入库数 = count。
    不再使用元话术模板题兜底，LLM 拒答时填入 __REFUSAL__ 占位让前端提示重试。
    """
    start = time.time()
    raw_questions = state.get("raw_questions", []) or []
    count = state.get("count", 3)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    vt = state.get("variant_type", "choice")
    question_type = state.get("question_type", "选择题")
    misconception_profile = state.get("misconception_profile", {"items": []})
    mastery_text = state.get("mastery_text", "暂无掌握度数据")
    mistake_summary = state.get("mistake_summary", "无历史错题")
    mode = state.get("mode", "")
    loose_mode = state.get("loose_mode", False)
    rag_text, rag_docs = _build_rag_text(state)
    bank_text = _build_question_bank_text(state.get("context", []))
    kb_context = (rag_text + bank_text).strip() or "（知识库与题库均无内容）"

    if len(raw_questions) >= count:
        return {
            "raw_questions": raw_questions[:count],
            "refilled": 0,
            "agent_steps": state.get("agent_steps", []) + [
                _make_step("refill", f"count={len(raw_questions)}", "no need", "success", start)
            ],
        }

    need = count - len(raw_questions)
    filled = 0
    existing_sigs = {_text_signature(str(it.get("question_text", ""))) for it in raw_questions}

    if vt == "mixed":
        cycle = ["choice", "fill", "essay", "choice", "comprehensive"]
        per_type_counts: dict[str, int] = {}
        for i in range(need):
            item_vt = cycle[(len(raw_questions) + i) % len(cycle)]
            per_type_counts[item_vt] = per_type_counts.get(item_vt, 0) + 1
        for sub_vt, sub_count in per_type_counts.items():
            sub_type = {"choice": "选择题", "fill": "填空题", "essay": "简答题", "comprehensive": "综合题"}.get(sub_vt, "选择题")
            retry_llm = _call_llm_for_questions(
                subject=subject,
                knowledge_point=knowledge_point,
                difficulty=state.get("difficulty", "中等"),
                question_type=sub_type,
                count=sub_count,
                kp_status=mastery_text,
                mistake_summary=mistake_summary,
                misconception_profile=misconception_profile,
                mode=mode,
                kb_context=kb_context,
                reference_text=state.get("reference_text", "") or "",
                reference_answer=state.get("reference_answer", "") or "",
                strict_kb=not loose_mode,
                fallback_data={"questions": []},
            )
            retry_questions = (retry_llm.data or {}).get("questions") or []
            for p in retry_questions:
                p.setdefault("_variant_type", sub_vt)
                qtext = str(p.get("question_text", ""))
                if qtext.strip() == "__REFUSAL__":
                    continue
                if _text_signature(qtext) in existing_sigs:
                    continue
                if _is_template_question(p):
                    continue
                options = p.get("options") or []
                if sub_vt == "choice" and _has_generic_bad_options(options):
                    continue
                p.setdefault("hints", ["先定位知识点。", "再按步骤推导。"])
                p.setdefault("easy_mistakes", "本类题易忽略关键步骤，请注意过程严谨。")
                raw_questions.append(p)
                existing_sigs.add(_text_signature(qtext))
                filled += 1
    else:
        retry_llm = _call_llm_for_questions(
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=state.get("difficulty", "中等"),
            question_type=question_type,
            count=need,
            kp_status=mastery_text,
            mistake_summary=mistake_summary,
            misconception_profile=misconception_profile,
            mode=mode,
            kb_context=kb_context,
            reference_text=state.get("reference_text", "") or "",
            reference_answer=state.get("reference_answer", "") or "",
            strict_kb=not loose_mode,
            fallback_data={"questions": []},
        )
        retry_questions = (retry_llm.data or {}).get("questions") or []
        for p in retry_questions:
            qtext = str(p.get("question_text", ""))
            if qtext.strip() == "__REFUSAL__":
                continue
            if _text_signature(qtext) in existing_sigs:
                continue
            if _is_template_question(p):
                continue
            options = p.get("options") or []
            if vt == "choice" and _has_generic_bad_options(options):
                continue
            p.setdefault("hints", ["先定位知识点。", "再按步骤推导。"])
            p.setdefault("easy_mistakes", "本类题易忽略关键步骤，请注意过程严谨。")
            raw_questions.append(p)
            existing_sigs.add(_text_signature(qtext))
            filled += 1

    # 仍不足时填 refusal 占位
    if filled < need:
        lack = need - filled
        for _ in range(lack):
            raw_questions.append({
                "question_text": "__REFUSAL__",
                "options": [],
                "standard_answer": "",
                "explanation": "当前网络问题，请稍后重试。",
                "hints": [],
                "easy_mistakes": "",
                "quality_flag": "deprecated",
            })
        logger.info("_refill_questions: LLM 重试仍不足 %d 道，剩余 %d 道用 refusal 占位", need, lack)

    step = _make_step(
        "refill",
        f"need={need}",
        f"refilled={filled}",
        "success" if filled >= need else "warning",
        start,
    )
    return {
        "raw_questions": _unique_question_items(raw_questions)[:count],
        "refilled": filled,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def save_questions(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    raw_questions = _unique_question_items(state.get("raw_questions", []))[:state.get("count", 3)]
    # 过滤掉 __REFUSAL__ 占位题：占位只是用来对齐题数，不入库、也不展示给用户
    raw_questions = [it for it in raw_questions if "__REFUSAL__" not in str(it.get("question_text", ""))]
    vt = state.get("variant_type", "choice")
    llm = state.get("llm_result", None)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    prompt_knowledge_point = _prompt_kp(state)
    target_points = [p for p in state.get("target_points", []) if p] or [knowledge_point]
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    user_id = state.get("user_id", 0)
    all_refused = bool(state.get("all_refused", False)) or (llm and not llm.used_llm and "知识库暂无" in (llm.error or ""))

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
        reason=f"{mode}：围绕 {subject} / {prompt_knowledge_point} 生成 {count} 道 {difficulty} {question_type}。",
    )
    db.add(session)
    db.flush()

    questions = []
    fallback_data = _build_target_fallback(state, vt, subject, max(count, 1))
    loose_mode = state.get("loose_mode", False)
    for idx, item in enumerate(raw_questions):
        item_vt = item.get("_variant_type") or _vt_for_index(vt, idx)
        item_question_type = item.get("_question_type") or _qtype_for_vt(item_vt, question_type)
        sub_qs = json.dumps(item.get("sub_questions") or [], ensure_ascii=False) if item_vt == "comprehensive" else "[]"
        fallback_item = fallback_data[idx % len(fallback_data)]
        question_kp = _target_for_question(state, item, idx)
        item.setdefault("target_knowledge_point", question_kp)
        question = Question(
            session_id=session.id,
            subject=subject,
            knowledge_point=question_kp,
            difficulty=difficulty,
            question_type=item_question_type,
            variant_type=item_vt,
            question_text=_with_target_prefix(
                item.get("question_text") or fallback_item["question_text"],
                subject,
                question_kp,
            ),
            options_json=json.dumps(item.get("options") or [], ensure_ascii=False),
            sub_questions_json=sub_qs,
            standard_answer=(item.get("standard_answer") or "").strip(),
            explanation=item.get("explanation") or "解析暂缺。",
            hints_json=json.dumps(item.get("hints") or ["先定位知识点。", "再按步骤推导。"], ensure_ascii=False),
            easy_mistakes=(item.get("easy_mistakes") or "").strip()[:500],
            recommend_reason=f"{session.reason} 本题定位：{question_kp}。",
            source="llm" if (llm and llm.used_llm) else "agent_fallback",
            is_verified=False if loose_mode else (True if (llm and llm.used_llm) else False),
            quality_flag="unverified" if loose_mode else "normal",
        )
        db.add(question)
        db.flush()
        questions.append(question_to_dict(question))

    out = f"saved {len(questions)} questions to session {session.id}"
    step = _make_step("save_questions", f"session_id={session.id}", out, "success", start)
    return {
        "session_id": session.id,
        "questions": questions,
        "config": session.reason,
        "target_points": target_points,
        "all_refused": all_refused and not questions,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_questions(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    prompt_knowledge_point = _prompt_kp(state)
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    user_id = state.get("user_id", 0)
    vt = _to_variant_type(question_type)
    fallback_data = _unique_question_items(_build_target_fallback(state, vt, subject, count * 2))
    fallback_data = _apply_misconception_traps(fallback_data, state.get("misconception_profile", {"items": []}), subject=subject, knowledge_point=knowledge_point)
    # 过滤 refusal 占位题和元话术坏题
    filtered_fallback: list[dict] = []
    for item in fallback_data:
        qtext = str(item.get("question_text", "")).strip()
        if qtext == "__REFUSAL__" or not qtext:
            continue
        if _is_template_question(item):
            continue
        if vt == "choice" and _has_generic_bad_options(item.get("options") or []):
            continue
        filtered_fallback.append(item)
    fallback_data = filtered_fallback[:count]

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
        reason=f"{mode}：{subject} / {prompt_knowledge_point} fallback 生成 {count} 道。",
    )
    db.add(session)
    db.flush()

    questions = []
    for idx, item in enumerate(fallback_data):
        item_vt = item.get("_variant_type") or _vt_for_index(vt, idx)
        item_question_type = item.get("_question_type") or _qtype_for_vt(item_vt, question_type)
        sub_qs = json.dumps(item.get("sub_questions") or [], ensure_ascii=False) if item_vt == "comprehensive" else "[]"
        # 识别"抽自 seed 题库的题"：seed 题天然带 source=seed 字段
        is_seed_pick = item.get("source") == "seed"
        question_kp = _target_for_question(state, item, idx)
        question = Question(
            session_id=session.id,
            subject=subject,
            knowledge_point=question_kp,
            difficulty=item.get("difficulty") or difficulty,
            question_type=item_question_type,
            variant_type=item_vt,
            question_text=_with_target_prefix(
                item.get("question_text", ""), subject, question_kp,
            ),
            options_json=json.dumps(item.get("options") or [], ensure_ascii=False),
            sub_questions_json=sub_qs,
            standard_answer=(item.get("standard_answer") or "").strip(),
            explanation=item.get("explanation") or "解析暂缺。",
            hints_json=json.dumps(item.get("hints") or ["先定位知识点。", "再按步骤推导。"], ensure_ascii=False),
            easy_mistakes=(item.get("easy_mistakes") or "").strip()[:500],
            recommend_reason=f"{session.reason} 本题定位：{question_kp}。",
            source=item.get("source") or "agent_fallback",
            is_verified=True if is_seed_pick else False,
            quality_score=100 if is_seed_pick else 0,
            quality_flag="normal",
        )
        db.add(question)
        db.flush()
        questions.append(question_to_dict(question))

    step = _make_step("fallback_questions", f"fallback for {subject}/{prompt_knowledge_point}", f"saved {len(questions)} template questions", "success", start)
    return {
        "session_id": session.id,
        "questions": questions,
        "config": session.reason,
        "llm_used": False,
        "llm_error": "question validation failed, fallback triggered",
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def should_fallback(state: QuestionState) -> Literal["fallback_questions", "save_questions"]:
    if not state.get("questions_valid", True):
        return "fallback_questions"
    return "save_questions"


def _build_question_graph() -> StateGraph:
    workflow = StateGraph(QuestionState)

    for name, fn in [
        ("analyze_user_state", analyze_user_state),
        ("select_target", select_target),
        ("retrieve_question_context", retrieve_question_context),
        ("generate_questions", _with_timeout(generate_questions_node)),
        ("deduplicate", deduplicate_questions),
        ("self_check", self_check_questions),
        ("refill", _refill_questions),
        ("validate_questions", validate_questions),
        ("save_questions", save_questions),
        ("fallback_questions", fallback_questions),
    ]:
        workflow.add_node(name, _safe_node(fn))

    workflow.set_entry_point("select_target")
    workflow.add_edge("select_target", "analyze_user_state")
    workflow.add_edge("analyze_user_state", "retrieve_question_context")
    workflow.add_edge("retrieve_question_context", "generate_questions")
    # 生成 → 去重 → 自检 → 补足 → 校验 → 保存/降级
    workflow.add_edge("generate_questions", "deduplicate")
    workflow.add_edge("deduplicate", "self_check")
    workflow.add_edge("self_check", "refill")
    workflow.add_edge("refill", "validate_questions")
    workflow.add_conditional_edges("validate_questions", should_fallback, {
        "fallback_questions": "fallback_questions",
        "save_questions": "save_questions",
    })
    workflow.add_edge("save_questions", END)
    workflow.add_edge("fallback_questions", END)

    return workflow.compile()


def get_question_graph() -> StateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_question_graph()
    return _GRAPH
