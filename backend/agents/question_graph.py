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
from models import Question, QuestionGenerationSession, KnowledgeMastery
from services.llm_service import LLMResult, chat_json, chat_completion
from services.serialization import question_to_dict
from prompts.hallucination_guard_prompt import render_self_check_prompt

logger = logging.getLogger("question_graph")

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)
_SELF_CHECK_TIMEOUT = 15  # 单题自检超时（秒），超时按 uncertain 处理

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
            _SEED_QUESTIONS_CACHE = data
        elif isinstance(data, dict):
            # 兼容 {"questions": [...]} 格式
            _SEED_QUESTIONS_CACHE = data.get("questions", [])
        else:
            _SEED_QUESTIONS_CACHE = []
    except Exception as exc:
        logger.warning("加载 seed_questions.json 失败：%s", exc)
        _SEED_QUESTIONS_CACHE = []
    return _SEED_QUESTIONS_CACHE


def _pick_seed_questions(subject: str, knowledge_point: str, vt: str, count: int) -> list[dict]:
    """从种子题库按 (subject, knowledge_point, vt) 抽题。

    四层匹配（按优先级）：
    1) 精确匹配 (subject, kp, vt) — 首选
    2) 模糊匹配 (subject, kp, 任意 vt) — 抽到后映射题型
    3) 语义匹配 (subject) + 题干含 KP 关键词 — KP 命名在 seed 库中粒度不同（如"内存管理"含"页面置换"题）时兜底
    4) 仍抽不到 → 返回空（让上层走通用模板兜底）

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

    # 第 3 步：语义匹配（仅同 subject） + 题干含 KP 的关键概念词
    keywords = _kp_semantic_keywords(kp_normalized)
    if keywords:
        sem = [
            dict(it) for it in pool
            if it.get("subject") == subject_match
            and any(kw in (it.get("question_text") or "") for kw in keywords)
        ]
        if sem:
            return _shuffle_round_robin(sem, count)

    return []


def _normalize_kp(knowledge_point: str) -> str:
    """KP 名称归一化:去除括号后缀（(ISA)/(X86) 等），方便 seed 库模糊匹配。"""
    if not knowledge_point:
        return ""
    import re
    return re.sub(r"[\(（][^)）]*[\)）]", "", knowledge_point).strip()


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


def _vt_to_zh(vt: str) -> str:
    return {"choice": "选择题", "fill": "填空题", "essay": "简答题", "comprehensive": "综合题"}.get(vt, "选择题")


def _shuffle_round_robin(items: list[dict], count: int) -> list[dict]:
    """轮转抽取：保证每道种子题尽量均匀出现，避免连续多道相同题。"""
    if not items:
        return []
    n = len(items)
    # 起点用确定性偏移（基于调用次数的 hash），避免每次随机洗牌造成用户刷新看到不同题
    start = (int(time.time()) // 30) % n  # 每 30 秒切换一次起点
    picked = [items[(start + i) % n] for i in range(count)]
    return picked


def set_db(db: Session | None) -> None:
    _db_context.set(db)


def _get_db() -> Session | None:
    return _db_context.get()

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

    # KP 归一化
    kp_normalized = _normalize_kp(knowledge_point)

    # 1 & 2：从种子题库抽题（用归一化 KP）
    picked = _pick_seed_questions(subject, kp_normalized, vt, count)
    if picked:
        return picked

    # 3：题型通用模板（仅作兜底，标 quality_flag=deprecated 阻断其进入参考池）
    #    模板中的 KP 显示为归一化后的名字（去除 (ISA) 等括号后缀），更干净
    if vt == "fill":
        return [
            {
                "question_text": f"【{subject} · {kp_normalized}】请填空：{kp_normalized} 的核心定义是什么？",
                "standard_answer": f"{kp_normalized} 的标准定义（根据教材）",
                "explanation": f"本题考查 {kp_normalized} 的概念理解，需完整表述。",
                "hints": ["先回忆教材定义。", "注意关键词不能遗漏。"],
                "quality_flag": "deprecated",
            } for _ in range(count)
        ]
    if vt == "essay":
        return [
            {
                "question_text": f"【{subject} · {kp_normalized}】请简要分析 {kp_normalized} 在 408 中的考查方式。",
                "standard_answer": f"{kp_normalized} 通常考查：概念理解、过程推导、边界条件辨析。",
                "explanation": f"408 对 {kp_normalized} 的考查兼顾定义理解和应用能力。",
                "hints": ["从概念、过程和边界三个维度回答。", "结合一道典型题目说明。"],
                "quality_flag": "deprecated",
            } for _ in range(count)
        ]
    if vt == "comprehensive":
        return [
            {
                "question_text": f"【{subject} · {kp_normalized}】综合题",
                "sub_questions": [
                    {"title": f"简述 {kp_normalized} 的基本概念。", "standard_answer": f"{kp_normalized} 是 {subject} 中的重要知识点。"},
                    {"title": f"在实际题目中，{kp_normalized} 的常见考法有哪些？", "options": ["A. 概念辨析", "B. 过程计算", "C. 边界条件", "D. 以上都是"], "standard_answer": "D"},
                ],
                "explanation": f"综合题考查 {kp_normalized} 的多角度理解。",
                "hints": ["先回答概念部分。", "再分析具体应用。"],
                "quality_flag": "deprecated",
            } for _ in range(count)
        ]
    # choice 的兜底：使用选择题通用模板（避免返回空列表导致前端无可用题）
    # 注：模板必须保证 count 道题彼此不同（题干问法/选项内容/答案都要有变化），
    #     否则会被下游 dedup 标记为重复,导致「3 道题一模一样」的现象
    kp_label = (kp_normalized or "该知识点").strip() or "该知识点"
    sub_label = (subject or "408 考研").strip() or "408 考研"
    choice_templates = [
        {
            "stem": f"【{sub_label} · {kp_label}】下列关于 {kp_label} 的核心概念，说法最准确的一项是？",
            "options": ["A. 仅考查定义背诵", "B. 兼顾概念理解与边界条件辨析", "C. 只考计算过程", "D. 只考综合应用"],
            "answer": "B",
            "hints": [f"先回忆 {kp_label} 的核心定义。", "再考虑定义成立的前提条件。"],
            "explain": f"本题考查 {kp_label} 的概念理解与适用条件，408 历年真题多从「定义+边界」角度设问。",
        },
        {
            "stem": f"【{sub_label} · {kp_label}】关于 {kp_label} 的过程/步骤，下列描述中正确的是？",
            "options": ["A. 仅有 1 个固定步骤", "B. 步骤顺序不可调整", "C. 包含多个有序子过程，且依赖关系明确", "D. 步骤之间无任何关联"],
            "answer": "C",
            "hints": [f"画出 {kp_label} 的执行流程图。", "标注每一步的前后依赖。"],
            "explain": f"{kp_label} 通常由若干有序子过程构成，理解子过程之间的依赖是解题关键。",
        },
        {
            "stem": f"【{sub_label} · {kp_label}】在 408 历年真题中，关于 {kp_label} 的典型命题方向是？",
            "options": ["A. 仅以选择题形式出现", "B. 仅以大题形式出现", "C. 选择题与大题均常见，且常结合其他考点综合命题", "D. 不属于 408 考纲范围"],
            "answer": "C",
            "hints": ["回顾近 5 年真题。", "留意 {kp_label} 的常见组合考点。".format(kp_label=kp_label)],
            "explain": f"408 命题对 {kp_label} 的考查兼顾选择与大题，且常与相近考点联合出题，复习时需注意知识体系。",
        },
    ]
    out: list[dict] = []
    for i in range(count):
        t = choice_templates[i % len(choice_templates)]
        out.append({
            "question_text": t["stem"],
            "options": list(t["options"]),
            "standard_answer": t["answer"],
            "explanation": t["explain"],
            "hints": list(t["hints"]),
            "easy_mistakes": f"易把 {kp_label} 的概念理解片面化，请注意概念成立的前提与边界。",
            "quality_flag": "deprecated",
        })
    return out


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


def _get_mastery_text(state: QuestionState) -> str:
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    db = _get_db()
    if db and subject and knowledge_point and state.get("user_id"):
        row = (
            db.query(KnowledgeMastery)
            .filter(
                KnowledgeMastery.user_id == state["user_id"],
                KnowledgeMastery.subject == subject,
                KnowledgeMastery.knowledge_point == knowledge_point,
            )
            .first()
        )
        if row:
            return f"掌握度={row.final_status}, 正确率={row.correct_count/max(row.total_answer_count,1):.0%}"
    return "暂无掌握度数据"


def _get_user_recent_mistakes(state: QuestionState, limit: int = 5) -> str:
    """从 mistake / answer_record 表取用户最近 N 条错题的摘要，注入 prompt。"""
    db = _get_db()
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    if not db or not user_id or not subject or not knowledge_point:
        return "无历史错题"

    try:
        from models import Mistake
        rows = (
            db.query(Mistake)
            .filter(
                Mistake.user_id == user_id,
                Mistake.subject == subject,
                Mistake.knowledge_point == knowledge_point,
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


def analyze_user_state(state: QuestionState) -> dict:
    user_id = state.get("user_id", 0)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    mode = state.get("mode", "")
    start = time.time()

    mastery_text = _get_mastery_text(state)
    mistake_summary = _get_user_recent_mistakes(state, limit=5)
    out = f"user_id={user_id}, mode={mode}, {mastery_text}"
    step = _make_step("analyze_user_state", f"user_id={user_id}, mode={mode}", out, "success", start)
    return {
        "mastery_text": mastery_text,
        "mistake_summary": mistake_summary,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def select_target(state: QuestionState) -> dict:
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")

    step = _make_step("select_target", f"subject={subject}, kp={knowledge_point}", f"type={question_type}, diff={difficulty}", "success", start)
    return {
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def retrieve_question_context(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")

    context = []
    if db and subject and knowledge_point:
        # 只参考"已验证 + 质量分 ≥ 60"的题，避免 LLM 自噬 + 排除被反馈有误的题
        existing = (
            db.query(Question)
            .filter(
                Question.subject == subject,
                Question.knowledge_point == knowledge_point,
                Question.is_deleted == False,
                Question.is_verified == True,
                Question.quality_flag != "deprecated",
                Question.quality_score >= 60,
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
    knowledge_point = state.get("knowledge_point", "")
    if not db or not subject or not knowledge_point:
        return "", []
    try:
        from services.rag_service import retrieve_knowledge
        rag_result = retrieve_knowledge(
            db=db,
            query=f"{subject} {knowledge_point}",
            limit=3,
            subject_filter=subject,
            kp_filter=knowledge_point,
        )
        docs = []
        if rag_result and rag_result.get("documents"):
            raw_docs = rag_result["documents"][:3]
            for d in raw_docs:
                if isinstance(d, dict):
                    docs.append(d.get("content", "") or d.get("text", ""))
                else:
                    docs.append(str(d))
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
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    context = state.get("context", [])
    mastery_text = state.get("mastery_text", "暂无掌握度数据")
    mistake_summary = state.get("mistake_summary", "无历史错题")
    vt = _to_variant_type(question_type)
    fallback_data = {"questions": _build_fallback(vt, subject, knowledge_point, count)}

    # 1. 知识库 RAG（注入 prompt 用作事实约束）
    rag_text, rag_docs = _build_rag_text(state)

    # 2. 题库参考（已 verified 的种子题）
    bank_text = _build_question_bank_text(context)

    # 3. 用新 prompt 模板组装（带 hallucination 约束、kb_ref 强制、难度量化）
    from prompts.question_prompt import render_question_prompt
    kb_context = (rag_text + bank_text).strip() or "（知识库与题库均无内容，请在 question_text 写 __REFUSAL__）"
    prompt = render_question_prompt(
        subject=subject,
        knowledge_point=knowledge_point,
        difficulty=difficulty,
        question_type=question_type,
        count=count,
        kp_status=mastery_text,
        mistake_summary=mistake_summary,
        recommend_mode=mode or "自由选择",
        kb_context=kb_context,
        reference_text=state.get("reference_text", "") or "",
        reference_answer=state.get("reference_answer", "") or "",
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
            llm = future.result(timeout=_NODE_TIMEOUT)
        except FutureTimeout:
            pool.shutdown(wait=False)
            logger.error("[timeout] generate_questions: LLM timed out after %ds", _NODE_TIMEOUT)
            llm = LLMResult(content="", used_llm=False, error=f"timed out after {_NODE_TIMEOUT}s", data=fallback_data)

    raw_questions = (llm.data or fallback_data).get("questions") or fallback_data["questions"]
    raw_questions = raw_questions[:count]

    # 最终兜底：如果 LLM 和 fallback 加起来都不足 count 道，用 _build_fallback 补齐（choice 类型已有通用模板）
    if len(raw_questions) < count:
        need = count - len(raw_questions)
        supplemental = _build_fallback(vt, subject, knowledge_point, need)
        if supplemental:
            raw_questions = list(raw_questions) + supplemental
            logger.info("LLM+seed 不足 %d 道，已用通用模板补足 %d 道", count, len(supplemental))

    # 检测 LLM 主动拒答（知识库无内容时按 prompt 规则应输出 __REFUSAL__）
    refused_count = sum(1 for it in raw_questions if "__REFUSAL__" in str(it.get("question_text", "")))
    if refused_count > 0 and refused_count == len(raw_questions):
        logger.info("LLM 全部拒答（知识库无 %s/%s），降级到 fallback 池", subject, knowledge_point)
        llm.used_llm = False
        llm.error = f"知识库暂无 {knowledge_point} 资料，已使用权威题库"
        raw_questions = fallback_data["questions"][:count]
    elif llm.used_llm and not _questions_match_target(raw_questions, subject, knowledge_point):
        llm.used_llm = False
        llm.error = "AI 题目与指定科目/知识点不匹配，已自动降级为本地保底题。"
        raw_questions = fallback_data["questions"][:count]

    if vt in ("fill", "essay"):
        for item in raw_questions:
            item.pop("options", None)
            ans = item.get("standard_answer", "").strip()
            if len(ans) == 1 and 'A' <= ans <= 'Z':
                item["standard_answer"] = item.get("explanation", ans)
    elif vt == "comprehensive":
        for item in raw_questions:
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

    for item in raw_questions:
        # 跳过明显为 fallback 的题（带 __REFUSAL__）
        if "__REFUSAL__" in str(item.get("question_text", "")):
            continue
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

        verdict = str((result.data or {}).get("verdict", "uncertain")).lower()
        report.append({
            "question_snippet": str(item.get("question_text", ""))[:80],
            "verdict": verdict,
            "issues": (result.data or {}).get("issues", []),
        })
        if verdict == "pass":
            kept.append(item)
        else:
            # fail / uncertain 都剔除，避免带幻觉的题入库
            removed += 1
            logger.info("self_check removed question: %s, verdict=%s", str(item.get("question_text", ""))[:50], verdict)

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
        if not item.get("question_text", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 题干为空")
        if not item.get("standard_answer", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 无标准答案")
        if not item.get("explanation", "").strip():
            reasons.append(f"#{idx+1} 解析为空")
        options = item.get("options", [])
        if vt == "choice":
            if not options or len(options) != 4:
                valid = False
                reasons.append(f"#{idx+1} 选项数量为 {len(options) if options else 0}，应为 4")
            else:
                # 答案必须落在 A/B/C/D 之一
                ans = (item.get("standard_answer") or "").strip().upper()
                if ans not in {"A", "B", "C", "D"}:
                    valid = False
                    reasons.append(f"#{idx+1} 选择题答案 {ans!r} 不在 A/B/C/D")
        if vt in ("fill", "essay") and not item.get("standard_answer", "").strip():
            valid = False
            reasons.append(f"#{idx+1} 缺少标准答案文本")
        if vt == "comprehensive" and not item.get("sub_questions"):
            reasons.append(f"#{idx+1} 综合题缺少子问题")
        # 难度感知（不通过仅记 reason，不直接判 valid，给下游降级机会）
        if not _assess_difficulty_match(item, difficulty):
            reasons.append(f"#{idx+1} 难度信号与 {difficulty} 不匹配")

    if valid and not _questions_match_target(raw_questions, subject, knowledge_point):
        valid = False
        reasons.append("知识点不匹配")

    reason_text = "valid" if valid else "; ".join(reasons)
    step = _make_step("validate_questions", f"{len(raw_questions)} questions", reason_text, "success" if valid else "warning", start)
    return {
        "questions_valid": valid,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def _refill_questions(state: QuestionState) -> dict:
    """题量不足时（被自检/去重剔除）用 fallback 池补足，使最终入库数 = count。"""
    start = time.time()
    raw_questions = state.get("raw_questions", []) or []
    count = state.get("count", 3)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    vt = state.get("variant_type", "choice")

    if len(raw_questions) >= count:
        return {
            "raw_questions": raw_questions[:count],
            "refilled": 0,
            "agent_steps": state.get("agent_steps", []) + [
                _make_step("refill", f"count={len(raw_questions)}", "no need", "success", start)
            ],
        }

    need = count - len(raw_questions)
    pool = _build_fallback(vt, subject, knowledge_point, need)
    # 题干去重：新题和已有题不能重复
    existing_sigs = {_text_signature(str(it.get("question_text", ""))) for it in raw_questions}
    filled = 0
    for p in pool:
        if filled >= need:
            break
        if _text_signature(str(p.get("question_text", ""))) in existing_sigs:
            continue
        # 补一道填空/简答的 easy_mistakes
        p.setdefault("hints", ["先定位知识点。", "再按步骤推导。"])
        p.setdefault("easy_mistakes", "本类题易忽略关键步骤，请注意过程严谨。")
        raw_questions.append(p)
        existing_sigs.add(_text_signature(str(p.get("question_text", ""))))
        filled += 1

    step = _make_step(
        "refill",
        f"need={need}",
        f"refilled={filled}",
        "success" if filled >= need else "warning",
        start,
    )
    return {
        "raw_questions": raw_questions,
        "refilled": filled,
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def save_questions(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    raw_questions = state.get("raw_questions", [])
    vt = state.get("variant_type", "choice")
    llm = state.get("llm_result", None)
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    user_id = state.get("user_id", 0)

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
        reason=f"{mode}：围绕 {subject} / {knowledge_point} 生成 {count} 道 {difficulty} {question_type}。",
    )
    db.add(session)
    db.flush()

    questions = []
    fallback_data = _build_fallback(vt, subject, knowledge_point, max(count, 1))
    for idx, item in enumerate(raw_questions):
        sub_qs = json.dumps(item.get("sub_questions") or [], ensure_ascii=False) if vt == "comprehensive" else "[]"
        fallback_item = fallback_data[idx % len(fallback_data)]
        question = Question(
            session_id=session.id,
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            question_type=question_type,
            variant_type=vt,
            question_text=_with_target_prefix(
                item.get("question_text") or fallback_item["question_text"],
                subject,
                knowledge_point,
            ),
            options_json=json.dumps(item.get("options") or [], ensure_ascii=False),
            sub_questions_json=sub_qs,
            standard_answer=(item.get("standard_answer") or "").strip(),
            explanation=item.get("explanation") or "解析暂缺。",
            hints_json=json.dumps(item.get("hints") or ["先定位知识点。", "再按步骤推导。"], ensure_ascii=False),
            easy_mistakes=(item.get("easy_mistakes") or "").strip()[:500],
            recommend_reason=session.reason,
            source="llm" if (llm and llm.used_llm) else "agent_fallback",
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
        "agent_steps": state.get("agent_steps", []) + [step],
    }


def fallback_questions(state: QuestionState) -> dict:
    db = _get_db()
    start = time.time()
    subject = state.get("subject", "")
    knowledge_point = state.get("knowledge_point", "")
    difficulty = state.get("difficulty", "中等")
    question_type = state.get("question_type", "选择题")
    count = state.get("count", 3)
    mode = state.get("mode", "")
    user_id = state.get("user_id", 0)
    vt = _to_variant_type(question_type)
    fallback_data = _build_fallback(vt, subject, knowledge_point, count)

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
        reason=f"{mode}：{subject} / {knowledge_point} fallback 生成 {count} 道。",
    )
    db.add(session)
    db.flush()

    questions = []
    for idx, item in enumerate(fallback_data):
        sub_qs = json.dumps(item.get("sub_questions") or [], ensure_ascii=False) if vt == "comprehensive" else "[]"
        # 识别"抽自 seed 题库的题"：seed 题天然带 source=seed 字段
        is_seed_pick = item.get("source") == "seed"
        question = Question(
            session_id=session.id,
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=item.get("difficulty") or difficulty,
            question_type=question_type,
            variant_type=vt,
            question_text=_with_target_prefix(
                item.get("question_text", ""), subject, knowledge_point,
            ),
            options_json=json.dumps(item.get("options") or [], ensure_ascii=False),
            sub_questions_json=sub_qs,
            standard_answer=(item.get("standard_answer") or "").strip(),
            explanation=item.get("explanation") or "解析暂缺。",
            hints_json=json.dumps(item.get("hints") or ["先定位知识点。", "再按步骤推导。"], ensure_ascii=False),
            easy_mistakes=(item.get("easy_mistakes") or "").strip()[:500],
            recommend_reason=session.reason,
            source=item.get("source") or "agent_fallback",
            is_verified=True if is_seed_pick else False,
            quality_score=100 if is_seed_pick else 0,
            quality_flag="normal",
        )
        db.add(question)
        db.flush()
        questions.append(question_to_dict(question))

    step = _make_step("fallback_questions", f"fallback for {subject}/{knowledge_point}", f"saved {len(questions)} template questions", "success", start)
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

    workflow.set_entry_point("analyze_user_state")
    workflow.add_edge("analyze_user_state", "select_target")
    workflow.add_edge("select_target", "retrieve_question_context")
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
