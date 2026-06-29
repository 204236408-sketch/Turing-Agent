"""
视频推荐服务 - 增强版

流程：
题目文本 → LLM关键词提取 → [本地视频匹配 + 实时爬虫补充] → 融合评分 → Top3推荐

核心文件：
- backend/services/video_service.py
- backend/services/llm_service.py
- backend/services/video_crawler_service.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from models import KnowledgePoint, VideoResource
from services.video_crawler_service import _popularity_score, _search_bilibili

logger = logging.getLogger("video_service")

# ============================================================================
# 第一部分：增强版规则提取（解决原有6个问题）
# ============================================================================

# 扩充后的知识点别名表（带权重级别标注）
KP_ALIASES: dict[str, tuple[set[str], str]] = {
    # 格式：(别名集合, 权重级别)  core=核心, concept=相关概念, general=泛称
    "栈、队列和数组": ({"栈和队列", "栈", "队列", "数组", "顺序栈", "链栈", "循环队列"}, "core"),
    "树与二叉树": ({"树与二叉树", "二叉树", "树", "树、森林", "完全二叉树", "满二叉树", "平衡二叉树", "AVL", "BST", "哈夫曼树", "线索二叉树"}, "core"),
    "进程与线程": ({"进程与线程", "进程", "线程", "同步与互斥", "进程同步", "死锁", "PV操作", "信号量", "临界区", "管程"}, "core"),
    "内存管理": ({"内存管理", "分页", "分页管理", "虚拟内存", "页面置换", "LRU", "FIFO", "OPT", "页面置换算法", "缺页", "快表", "段表"}, "core"),
    "计算机系统概述": ({"计算机系统概述", "概述", "OS概述", "操作系统的基本概念"}, "general"),
    "输入输出系统": ({"输入输出系统", "I/O", "IO", "输入输出", "IO系统", "总线与 I/O", "总线与IO", "DMA", "通道"}, "core"),
    "总线": ({"总线", "总线与 I/O", "总线与IO", "系统总线", "数据总线", "地址总线", "控制总线"}, "core"),
    "中央处理器": ({"中央处理器", "CPU", "数据通路", "控制器", "运算器", "指令周期", "机器周期", "时钟周期"}, "core"),
    "数据的表示和运算": ({"数据的表示和运算", "数据表示", "运算", "数据表示与运算", "浮点数", "定点数", "原码", "补码", "反码", "移码"}, "core"),
    "文件管理": ({"文件管理", "文件系统", "文件", "目录", "文件描述符", "FCB", "索引节点", "位图法"}, "core"),
    "输入输出管理": ({"输入输出管理", "I/O管理", "IO管理", "输入输出", "I/O", "IO系统", "设备独立性"}, "core"),
    "传输层": ({"传输层", "TCP", "UDP", "三次握手", "四次挥手", "可靠传输", "流量控制", "拥塞控制"}, "core"),
    "计算机网络体系结构": ({"计算机网络体系结构", "体系结构", "网络体系结构", "OSI", "TCP/IP", "五层协议"}, "general"),
    "串": ({"串", "字符串", "KMP", "朴素模式匹配", "next数组"}, "core"),
    "查找": ({"查找", "散列", "哈希表", "散列表", "二分查找", "顺序查找", "折半查找", "B树", "B+树"}, "core"),
    "排序": ({"排序", "直接插入排序", "希尔排序", "冒泡排序", "快速排序", "简单选择排序", "堆排序", "归并排序", "基数排序"}, "core"),
    "图": ({"图", "有向图", "无向图", "连通图", "强连通图", "邻接矩阵", "邻接表", "深度优先", "广度优先", "Dijkstra", "Floyd", "Prim", "Kruskal", "拓扑排序", "关键路径"}, "core"),
    "线性表": ({"线性表", "链表", "顺序表", "单链表", "双链表", "循环链表", "头指针", "头结点"}, "core"),
    "存储系统": ({"存储系统", "Cache", "主存", "存储器", "高速缓冲", "虚拟存储器", "Cache映射", "直接映射", "组相联映射"}, "core"),
    "指令系统": ({"指令系统", "指令", "寻址", "CISC", "RISC", "流水线", "指令流水线", "超标量", "转移预测"}, "core"),
    "物理层": ({"物理层", "通信基础", "传输介质", "奈奎斯特", "香农定理", "调制解调", "编码解码", "电路交换", "报文交换", "分组交换"}, "core"),
    "数据链路层": ({"数据链路层", "介质访问", "局域网", "差错控制", "CRC", "海明码", "停止-等待", "滑动窗口", "PPP", "HDLC"}, "core"),
    "网络层": ({"网络层", "IP", "IPv4", "IPv6", "路由", "RIP", "OSPF", "BGP", "ARP", "ICMP", "NAT", "子网划分", "CIDR"}, "core"),
    "应用层": ({"应用层", "DNS", "万维网", "HTTP", "HTTPS", "电子邮件", "SMTP", "POP3", "IMAP", "FTP", "TELNET", "SSH"}, "core"),
    "绪论": ({"绪论", "算法", "算法评价", "时间复杂度", "空间复杂度", "大O表示法"}, "core"),
}

# 扩充后的英文停用词表（50+个）
ENG_STOP_WORDS: set[str] = {
    "THE", "AND", "FOR", "NOT", "ARE", "ALL", "CAN", "HAS", "WILL", "MAY",
    "THIS", "THAT", "WITH", "FROM", "THAN", "ALSO", "IS", "OF", "IN", "ON",
    "AT", "TO", "BY", "AN", "AS", "OR", "IF", "SO", "NO", "YES", "UP",
    "OUT", "OVER", "UNDER", "BUT", "HAD", "HAVE", "BEEN", "BEING", "WERE",
    "THEIR", "THERE", "HERE", "WHEN", "WHERE", "WHY", "HOW", "WHICH", "WHO",
    "WHAT", "VERY", "MORE", "MOST", "SOME", "SUCH", "INTO", "THROUGH",
    # 题目选项相关
    "CHOICE", "OPTION", "PLEASE", "SELECT", "CHOOSE", "WRONG", "RIGHT", "CORRECT",
}

# 已知技术术语白名单（精确匹配，优先提取）
KNOWN_TECH_TERMS: set[str] = {
    # 数据结构
    "LRU", "FIFO", "OPT", "BST", "AVL", "KMP", "BFS", "DFS", "Dijkstra", "Prim", "Kruskal",
    # 计算机组成
    "CPU", "DMA", "PCI", "ROM", "RAM", "Cache", "TLB", "PCB", "JCB",
    # 网络
    "TCP", "UDP", "HTTP", "HTTPS", "DNS", "FTP", "SMTP", "POP3", "IMAP", "SSH", "TELNET",
    "IP", "IPv4", "IPv6", "ARP", "ICMP", "NAT", "RIP", "OSPF", "BGP", "CIDR",
    "MAC", "PPP", "HDLC", "CRC",
    # 操作系统
    "PV", "SEMA", "MUTEX", "SEMAPHORE",
    # 其他
    "OS", "API", "GUI", "CLI", "SQL", "URL", "URI",
}

# 中文停用词（常见的无意义词）
CHINESE_STOP_WORDS: set[str] = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很",
    "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "这个", "那个",
    "下列", "关于", "对于", "以及", "或者", "还是", "但", "而", "且", "并", "且", "把", "被", "让",
    "由", "在", "向", "对", "为", "以", "及", "等", "等等", "如", "即", "则", "又", "再",
}

# 反向排除上下文（这些词组合时不算匹配）
EXCLUDE_PATTERNS: list[tuple[str, list[str]]] = [
    ("图", ["图片", "地图", "图形", "图表", "如图", "图示", "示意图", "流程图", "结构图"]),
    ("树", ["树形", "子树", "决策树", "决策树算法"]),
    ("进程", ["进程中", "进程进行", "进程序列"]),
    ("线程", ["线程池"]),
    ("栈", ["栈帧", "调用栈"]),
]


def _safe_contains(text: str, term: str) -> bool:
    """安全的子串匹配，检查边界避免误匹配"""
    # 检查是否是排除上下文
    for base, excludes in EXCLUDE_PATTERNS:
        if base == term:
            for exc in excludes:
                if exc in text:
                    return False

    # 构建边界正则：term前后必须是字符串边界、标点、空格、中文非汉字边界
    # 或者term本身就是独立的词（长度>=2）
    if len(term) <= 1:
        return False

    # 直接子串匹配（简化版，适用于大多数情况）
    return term in text


def _filter_chinese_stop_words(text: str) -> str:
    """过滤中文停用词"""
    for stop in CHINESE_STOP_WORDS:
        # 用空格替换停用词（保持位置）
        text = text.replace(stop, " ")
    return text


def extract_question_keywords_v2(text: str, knowledge_point: str = "", subject: str = "") -> dict:
    """
    增强版关键词提取，返回带权重的结构化结果

    返回: {
        "core_keywords": [...],      # 核心关键词（权重最高的3-5个）
        "concept_keywords": [...],    # 相关概念
        "subject_keywords": [...],   # 科目/泛称
        "weighted_keywords": {...},   # 带权重的完整词典
        "question_type": str,        # 题型
        "difficulty_hint": str,      # 难度暗示
        "extract_method": str,        # 提取方式
    }
    """
    if not text:
        result = {
            "core_keywords": [knowledge_point] if knowledge_point else [],
            "concept_keywords": [],
            "subject_keywords": [subject] if subject else [],
            "weighted_keywords": {},
            "question_type": "未知",
            "difficulty_hint": "未知",
            "extract_method": "knowledge_point_fallback",
        }
        if knowledge_point:
            result["weighted_keywords"][knowledge_point] = 1.0
        if subject:
            result["subject_keywords"].append(subject)
            result["weighted_keywords"][subject] = 0.3
        return result

    text_filtered = _filter_chinese_stop_words(text)
    text_lower = text_filtered.lower()

    weighted: dict[str, float] = {}
    core_kw, concept_kw, subject_kw = [], [], []

    # 1. 从别名表提取知识点关键词（分级加权）
    for kp, (aliases, level) in KP_ALIASES.items():
        weight = 1.0 if level == "core" else 0.7
        for term in aliases:
            if _safe_contains(text_lower, term.lower()):
                if term not in weighted or weighted[term] < weight:
                    weighted[term] = weight
                    if kp not in weighted:
                        weighted[kp] = weight * 0.9  # 知识点本身稍低

    # 2. 英文术语提取（白名单优先 + 停用词过滤）
    eng_terms = re.findall(r'\b[A-Za-z][A-Za-z0-9+#.\-/]*\b', text)
    for t in eng_terms:
        t_upper = t.upper()
        if len(t) < 2:
            continue
        if t_upper in ENG_STOP_WORDS:
            continue
        if t_lower := t.lower() in text_lower:
            if t_upper in KNOWN_TECH_TERMS:
                if t not in weighted or weighted[t] < 1.0:
                    weighted[t] = 1.0
            elif t_upper not in ENG_STOP_WORDS and len(t) >= 3:
                if t not in weighted or weighted[t] < 0.8:
                    weighted[t] = 0.8

    # 3. 科目名称
    subjects = {"数据结构", "计算机组成原理", "操作系统", "计算机网络"}
    for s in subjects:
        if s in text:
            subject_kw.append(s)
            if s not in weighted or weighted[s] < 0.3:
                weighted[s] = 0.3

    # 4. 知识点的知识点优先
    if knowledge_point and knowledge_point not in weighted:
        weighted[knowledge_point] = 1.0
        core_kw.append(knowledge_point)

    # 5. 题型识别
    question_type = "未知"
    if any(p in text for p in ["选择题", "单选", "多选", "A.", "B.", "C.", "D."]):
        question_type = "选择题"
    elif "填空" in text:
        question_type = "填空题"
    elif any(p in text for p in ["简答", "简述", "说明", "为什么"]):
        question_type = "简答题"
    elif any(p in text for p in ["综合", "应用题", "设计题"]):
        question_type = "综合题"
    elif "计算" in text:
        question_type = "计算题"

    # 6. 难度暗示
    difficulty_hint = "中等"
    if any(p in text for p in ["简单", "容易", "基础", "基本"]):
        difficulty_hint = "简单"
    elif any(p in text for p in ["难", "复杂", "综合", "深入", "困难"]):
        difficulty_hint = "困难"

    # 7. 按权重排序，分类输出
    sorted_kw = sorted(weighted.items(), key=lambda x: -x[1])

    # 取前8个作为核心关键词
    top_kw = [k for k, v in sorted_kw[:8]]

    core_kw = [k for k, v in sorted_kw[:5] if v >= 0.8] or top_kw[:3]
    concept_kw = [k for k, v in sorted_kw[5:8] if v >= 0.5]
    subject_kw = [k for k, v in sorted_kw if v <= 0.3]

    return {
        "core_keywords": core_kw,
        "concept_keywords": concept_kw,
        "subject_keywords": list(set(subject_kw)),
        "weighted_keywords": dict(sorted_kw[:12]),  # 最多12个带权重
        "question_type": question_type,
        "difficulty_hint": difficulty_hint,
        "extract_method": "rule_enhanced",
    }


# ============================================================================
# 第二部分：LLM关键词提取
# ============================================================================

LLM_KEYWORD_SYSTEM_PROMPT = """你是408考研计算机学科的视频搜索关键词专家。请从题目中提取2-3个最适合用于B站视频搜索的高质量关键词。

输出要求（严格JSON格式，无其他内容）：
{
  "search_keywords": ["关键词1", "关键词2", "关键词3"],
  "search_reason": "选择这些关键词的理由简述"
}

关键词选择原则（极其重要）：
- **必须是2-4个字的短词或术语**，不是完整句子或长词组
- 例：正确 ["二叉树", "普通树", "左右孩子", "度为2"]  错误 ["二叉树与普通树的区别", "二叉树左右孩子区分"]
- 优先选择视频标题中可能直接出现的词（如"二叉树"、"平衡树"、"遍历"、"排序"）
- 中英文术语都可以，优先用题目中出现的原文
- 只需返回2-3个最有区分度的关键词，不要贪多
- 如果是选择题，注意选项中出现的关键技术词汇
"""

KP_KEYWORD_SYSTEM_PROMPT = """你是408考研计算机学科的视频搜索关键词专家。现在给定一个知识点名称，请生成2-3个最适合用于B站视频搜索的高质量关键词。

输出要求（严格JSON格式，无其他内容）：
{
  "search_keywords": ["关键词1", "关键词2", "关键词3"],
  "search_reason": "选择这些关键词的理由简述"
}

关键词选择原则（极其重要）：
- **必须是2-4个字的短词或术语**，不是完整句子或长词组
- 优先选择B站视频标题中最常出现的表述方式（如"二叉树遍历"、"进程同步"、"页面置换"）
- 可以在知识点基础上补充"408考研"、"王道考研"等高频搜索后缀词来提高搜索精准度
- 中英文术语都可以，如"TCP三次握手"、"LRU页面置换"
- 只需返回2-3个最有区分度的关键词，不要贪多
"""


def extract_keywords_with_llm(question_text: str, subject: str = "", knowledge_point: str = "", options: list = None) -> dict | None:
    """
    使用LLM提取高质量搜索关键词

    两种场景：
    - 有题目文本 → 从题目中提取（LLM_KEYWORD_SYSTEM_PROMPT）
    - 无题目文本（知识点详情页场景）→ 从知识点描述中扩展生成（KP_KEYWORD_SYSTEM_PROMPT）
    """
    try:
        from services.llm_service import chat_json

        # 根据是否有题目文本选择不同的 prompt
        is_kp_scene = not question_text or len(question_text) < 10
        system_prompt = KP_KEYWORD_SYSTEM_PROMPT if is_kp_scene else LLM_KEYWORD_SYSTEM_PROMPT

        # 组装提示信息
        prompt_parts = []
        if subject:
            prompt_parts.append(f"科目：{subject}")
        if knowledge_point:
            prompt_parts.append(f"知识点：{knowledge_point}")

        if is_kp_scene:
            # 知识点场景：将 question_text 作为知识点描述传入
            if question_text:
                prompt_parts.append(f"知识点描述：{question_text[:500]}")
        else:
            # 题目场景：完整题目信息
            prompt_parts.append(f"题目：{question_text}")
            if options and isinstance(options, list) and len(options) > 0:
                opt_strs = []
                for o in options:
                    if isinstance(o, dict):
                        k = o.get("key", "")
                        t = o.get("text", "")
                        if t:
                            opt_strs.append(f"{k}. {t}" if k else t)
                    elif isinstance(o, str) and o.strip():
                        opt_strs.append(o.strip())
                if opt_strs:
                    prompt_parts.append(f"选项：{'  '.join(opt_strs)}")

        user_prompt = "\n".join(prompt_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        fallback = {
            "search_keywords": [],
            "search_reason": "",
        }

        result = chat_json(messages, fallback, temperature=0.2, max_tokens=400)

        if not result.used_llm:
            logger.warning("LLM关键词提取失败，降级到规则提取: %s", result.error)
            return None

        data = result.data
        if not data or not isinstance(data, dict):
            return None

        # 验证返回质量
        search_kw = data.get("search_keywords", [])
        if not search_kw or not isinstance(search_kw, list):
            logger.warning("LLM返回格式异常，降级到规则提取")
            return None

        # 统一转换为 core_keywords 格式以保持兼容性
        data["core_keywords"] = search_kw[:3]  # 只取前3个
        data["concept_keywords"] = []
        data["exam_focus"] = data.get("search_reason", "")
        data["difficulty_terms"] = []
        data["search_terms"] = search_kw[:3]
        data["extract_method"] = "llm"
        logger.info("LLM关键词提取成功: search_keywords=%s", search_kw[:3])
        return data

    except Exception as e:
        logger.error("LLM关键词提取异常: %s", e)
        return None


def extract_keywords(
    question_text: str,
    subject: str = "",
    knowledge_point: str = "",
    options: list = None,
    use_llm: bool = True,
    llm_threshold: int = 0,
) -> dict:
    """
    综合关键词提取（优先LLM，规则兜底）

    策略：
    - use_llm=True → 优先 LLM 提取（不论题目长度）
    - LLM 失败 / use_llm=False → 降级到规则提取
    """
    # 优先尝试LLM提取（用户明确要求用LLM理解题目语义）
    if use_llm and question_text:
        llm_result = extract_keywords_with_llm(question_text, subject, knowledge_point, options)
        if llm_result:
            return llm_result

    # LLM失败/未启用，降级到规则提取
    result = extract_question_keywords_v2(question_text, knowledge_point, subject)
    result["extract_method"] = "rule_fallback"
    return result


# ============================================================================
# 第三部分：核心评分（关键词匹配为主）
# ============================================================================


def _keyword_match_score(text: str, keywords: list[str]) -> tuple[float, list[str]]:
    """
    核心评分：关键词命中率（短词分词匹配）

    返回: (匹配率0-1, 匹配到的关键词列表)

    匹配规则：
    1. 完整包含任一关键词 → 命中
    2. 关键词中包含2字以上短词（去除停用词后）→ 命中
    3. 整体匹配率 = 命中关键词数 / 总关键词数
    """
    if not keywords:
        return 0.0, []

    text_lower = text.lower()
    matched = []
    for kw in keywords:
        if not kw:
            continue
        kw_lower = kw.lower()
        # 规则1: 完整包含
        if kw_lower in text_lower:
            matched.append(kw)
            continue
        # 规则2: 分词匹配 - 提取2字以上子词
        sub_words = _split_keyword(kw)
        if any(sw in text_lower for sw in sub_words):
            matched.append(kw)
    return len(matched) / len(keywords), matched


def _split_keyword(kw: str) -> list[str]:
    """
    将复合关键词拆分为2字以上子词

    例：
    "二叉树与普通树的区别" → ["二叉树", "普通树", "区别"]
    "二叉树左右孩子" → ["二叉树", "左右", "孩子"]
    """
    # 停用词
    stop_words = {
        "的", "与", "和", "或", "及", "在", "是", "了", "为", "以", "把",
        "a", "an", "the", "of", "for", "to", "in", "on", "and", "or",
    }

    # 中英混合分词策略：
    # 1. 中文按2-3字滑动窗口分词
    # 2. 英文单词按空格分
    words = []

    # 先按非字母数字汉字分
    import re as _re
    parts = _re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", kw)
    for part in parts:
        if not part:
            continue
        # 中文部分用滑动窗口
        if _re.match(r"[\u4e00-\u9fff]+", part):
            # 2字和3字窗口
            for n in (3, 2):
                for i in range(len(part) - n + 1):
                    w = part[i:i+n]
                    if w and w not in stop_words and w not in words:
                        words.append(w)
        else:
            # 英文/数字
            if part.lower() not in stop_words and part not in words:
                words.append(part)

    return words


def _calculate_kp_align_score(video_kp: str, target_kp: str) -> float:
    """知识点对齐度（辅助评分）"""
    if not video_kp or not target_kp:
        return 0.3
    if video_kp == target_kp:
        return 1.0
    if video_kp in target_kp or target_kp in video_kp:
        return 0.7
    return 0.3


def _calculate_quality_score(video) -> float:
    """视频质量分（辅助评分）"""
    if isinstance(video, VideoResource):
        play = video.play_count or 0
        return min(play / 10000, 1.0)  # 1万播放为满分
    else:
        play = video.get("play_count", 0) or 0
        return min(play / 10000, 1.0)


def _fused_score(
    video,
    llm_keywords: list[str],
    target_kp: str,
) -> tuple[float, float, str]:
    """
    简化评分：关键词匹配为主，知识点+质量为辅

    返回: (keyword_match_score, final_score, match_level)
    """
    # 提取视频文本
    if isinstance(video, VideoResource):
        title = video.title or ""
        reason = video.reason or ""
        video_kp = video.knowledge_point or ""
    else:
        title = video.get("title", "")
        reason = video.get("description", "") + " " + video.get("tag", "")
        video_kp = video.get("knowledge_point", "")

    # 核心：关键词匹配（标题 + 知识点 + 描述）
    target_text = f"{title} {video_kp} {reason}"
    kw_score, _ = _keyword_match_score(target_text, llm_keywords)

    # 辅助：知识点对齐 + 视频质量
    kp_score = _calculate_kp_align_score(video_kp, target_kp)
    quality_score = _calculate_quality_score(video)

    # 综合分 = 关键词匹配 70% + 知识点对齐 20% + 质量 10%
    final = kw_score * 0.70 + kp_score * 0.20 + quality_score * 0.10

    # 匹配等级
    if kw_score >= 0.66 and kp_score >= 0.7:
        match_level = "exact"
    elif kw_score >= 0.33:
        match_level = "keyword"
    elif kp_score >= 0.7:
        match_level = "alias"
    else:
        match_level = "subject"

    return round(kw_score, 4), round(final, 4), match_level


def _generate_match_reason(
    video: dict | VideoResource,
    llm_keywords: list[str],
    match_level: str,
    extract_method: str,
) -> str:
    """生成推荐理由"""
    if isinstance(video, VideoResource):
        title = video.title or "未知标题"
        author = video.author or "未知作者"
        kp = video.knowledge_point or ""
    else:
        title = video.get("title", "未知标题")
        author = video.get("author", "未知作者")
        kp = video.get("knowledge_point", "")

    # 匹配关键词说明
    matched_kw = [kw for kw in llm_keywords[:3] if kw.lower() in title.lower()]
    kw_desc = " ".join(f"「{kw}」" for kw in matched_kw) if matched_kw else ""

    # 根据匹配等级生成不同推荐语
    level_desc = {
        "exact": "精确匹配",
        "keyword": "关键词匹配",
        "alias": "相关推荐",
        "subject": "同类推荐",
    }.get(match_level, "")

    source_desc = "📚本地" if isinstance(video, VideoResource) else "🔍实时爬取"
    method_desc = "AI推荐" if extract_method == "llm" else "规则匹配"

    if kw_desc:
        return f"{source_desc} · {method_desc} · {level_desc} · 匹配{kw_desc} · {author}讲解"
    else:
        return f"{source_desc} · {method_desc} · {level_desc} · {kp}相关 · {author}讲解"


def _format_video_item(
    video: dict | VideoResource,
    match_level: str,
    kw_score: float,
    final_score: float,
    source: str,
    subject: str,
    knowledge_point: str,
    llm_keywords: list[str],
    extract_method: str,
) -> dict:
    """格式化视频条目"""
    if isinstance(video, VideoResource):
        item = {
            "id": video.id,
            "title": video.title,
            "platform": video.platform or "Bilibili",
            "url": video.url,
            "cover_url": _normalize_cover_url(video.cover_url or ""),
            "duration": video.duration or "",
            "author": video.author or "",
            "reason": video.reason or "",
            "subject": video.subject,
            "knowledge_point": video.knowledge_point or "",
            "quality_score": video.quality_score or 0,
        }
    else:
        # 实时爬虫视频：cover_url 是 B 站图床 URL，走代理端点绕过防盗链
        raw_cover = video.get("cover_url", "")
        cover_url = _proxy_bili_cover(raw_cover)
        item = {
            "id": 0,
            "title": video.get("title", ""),
            "platform": "Bilibili",
            "url": video.get("url", ""),
            "cover_url": cover_url,
            "duration": video.get("duration", ""),
            "author": video.get("author", ""),
            "reason": f"实时搜索 · 匹配关键词" if source == "bilibili" else "",
            "subject": subject,
            "knowledge_point": knowledge_point,
            "quality_score": video.get("quality_score", 50),
        }

    item.update({
        "match_level": match_level,
        "keyword_match_score": kw_score,
        "final_score": round(final_score, 4),
        "source": source,
        "match_explanation": _generate_match_reason(video, llm_keywords, match_level, extract_method),
    })

    return item


# ============================================================================
# 第四部分：缓存机制
# ============================================================================

# 简单内存缓存：question_id -> (timestamp, result)
_VIDEO_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 600  # 10分钟


def _get_cache_key(question_id: int | None, subject: str, kp: str, text_hash: str) -> str:
    """生成缓存键"""
    key_parts = [
        str(question_id or "noid"),
        subject or "",
        kp or "",
        text_hash[:16],
    ]
    return hashlib.md5("|".join(key_parts).encode()).hexdigest()


def _get_cache(key: str) -> dict | None:
    """获取缓存"""
    if key in _VIDEO_CACHE:
        timestamp, result = _VIDEO_CACHE[key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            return result
        del _VIDEO_CACHE[key]
    return None


def _set_cache(key: str, result: dict) -> None:
    """设置缓存"""
    _VIDEO_CACHE[key] = (time.time(), result)
    # 防止缓存无限增长
    if len(_VIDEO_CACHE) > 1000:
        oldest = min(_VIDEO_CACHE.items(), key=lambda x: x[1][0])
        del _VIDEO_CACHE[oldest[0]]


# ============================================================================
# 第五部分：主推荐函数
# ============================================================================


def recommend_videos_v2(
    db: Session,
    question_id: int | None = None,
    subject: str = "",
    knowledge_point: str = "",
    question_text: str = "",
    options: list = None,
    limit: int = 3,
    use_llm: bool = True,
    user_id: int | None = None,
) -> dict:
    """
    增强版视频推荐 - 并行检索 + 匹配度优先

    流程：
    1. 查缓存
    2. 关键词提取（LLM或规则）
    3. 【并行】本地库检索 + B站实时爬虫
    4. 合并候选池 + URL去重
    5. 统一评分（关键词匹配为主）
    6. 按匹配度排序 → Top N
    7. 高质量爬虫结果入库 + 写入缓存

    返回: {
        "items": [...],
        "llm_keywords": [...],
        "keyword_extract_method": str,
        "subject": str,
        "knowledge_point": str,
        "total_candidates": int,
        "cache_hit": bool,
    }
    """
    # 1. 检查缓存
    text_hash = hashlib.md5((question_text or "").encode()).hexdigest()
    cache_key = _get_cache_key(question_id, subject, knowledge_point, text_hash)

    cached = _get_cache(cache_key)
    if cached and limit <= 3:
        cached["cache_hit"] = True
        logger.info("视频推荐缓存命中: key=%s", cache_key[:8])
        return cached

    # 2. 关键词提取
    kw_result = extract_keywords(
        question_text,
        subject,
        knowledge_point,
        options=options,
        use_llm=use_llm,
        llm_threshold=50,
    )

    all_keywords = (
        kw_result.get("core_keywords", [])
        + kw_result.get("concept_keywords", [])
    )
    extract_method = kw_result.get("extract_method", "unknown")

    logger.info(
        "视频推荐 | subject=%s kp=%s keywords=%s method=%s",
        subject, knowledge_point, all_keywords[:5], extract_method
    )

    # 3. 【并行】本地库检索 + B站实时爬虫
    local_videos: list[VideoResource] = []
    bili_raw: list[dict] = []

    def _fetch_local():
        query = db.query(VideoResource).filter(VideoResource.is_deleted == False)
        if subject:
            query = query.filter(VideoResource.subject == subject)
        if knowledge_point:
            # 精确匹配 + 别名扩展
            kp_aliases = KP_ALIASES.get(knowledge_point, ({knowledge_point}, "core"))[0] if knowledge_point in KP_ALIASES else {knowledge_point}
            from sqlalchemy import or_
            conditions = [VideoResource.knowledge_point == knowledge_point]
            for alias in kp_aliases:
                if alias != knowledge_point:
                    conditions.append(VideoResource.knowledge_point.contains(alias))
            query = query.filter(or_(*conditions))
        return query.all()

    def _fetch_crawl():
        if not all_keywords:
            return []
        try:
            search_terms = all_keywords[:4]
            if knowledge_point:
                search_terms.insert(0, knowledge_point)
            search_query = f"{' '.join(search_terms)} 408 考研"
            logger.info("B站实时搜索: %s", search_query)
            results = _search_bilibili(search_query, limit=20, order="click")
            if not results:
                results = _search_bilibili(search_query, limit=20, order="click", duration=0)
            return results
        except Exception as e:
            logger.error("B站实时搜索失败: %s", e)
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_local = executor.submit(_fetch_local)
        future_crawl = executor.submit(_fetch_crawl)
        local_videos = future_local.result()
        bili_raw = future_crawl.result()

    logger.info("候选池 | 本地=%d 爬虫=%d", len(local_videos), len(bili_raw))

    # 4. 合并候选池（带 source 标签，URL 去重）
    candidates: list[tuple[Any, str, str]] = []  # (video_obj, source, url)
    seen_urls: set[str] = set()

    for v in local_videos:
        url = v.url or ""
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        candidates.append((v, "local_seed", url))

    for v in bili_raw:
        url = v.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        candidates.append((v, "realtime_crawl", url))

    # 5. 统一评分（关键词匹配为主，不区分来源）
    scored: list[tuple[float, float, str, Any, str]] = []  # (kw_score, final, label, video, source)
    for video, source, url in candidates:
        kw_score, final, label = _fused_score(video, all_keywords, knowledge_point)
        scored.append((kw_score, final, label, video, source))

    # 5.5 个性化加权（用户点击过的作者/知识点视频加权）
    if user_id:
        _apply_user_preference_weight(db, scored, user_id)

    # 6. 按 final_score 降序（匹配度优先，不偏向本地库）
    scored.sort(key=lambda x: -x[1])

    # 7. 取 Top N
    result_items: list[dict] = []
    for kw_score, final, label, video, source in scored[:limit]:
        if isinstance(video, VideoResource):
            item = _format_video_item(
                video, label, kw_score, final, source,
                video.subject, video.knowledge_point or "",
                all_keywords, extract_method
            )
        else:
            item = _format_video_item(
                video, label, kw_score, final, source,
                subject, knowledge_point,
                all_keywords, extract_method
            )
        result_items.append(item)

    # 8. 高质量爬虫视频入库（评分 >= 0.6 且不在本地库）
    _persist_quality_crawl_videos(db, bili_raw, subject, knowledge_point, all_keywords)

    # 9. 构建返回结果
    result = {
        "items": result_items,
        "llm_keywords": all_keywords[:6],
        "keyword_extract_method": extract_method,
        "subject": subject,
        "knowledge_point": knowledge_point,
        "total_candidates": len(scored),
        "local_count": len(local_videos),
        "crawl_count": len(bili_raw),
        "cache_hit": False,
        "question_type": kw_result.get("question_type", "未知"),
        "difficulty_hint": kw_result.get("difficulty_hint", "中等"),
    }

    # 10. 写入缓存
    _set_cache(cache_key, result)
    logger.info("视频推荐完成: candidates=%d returned=%d cache_key=%s",
                len(scored), len(result_items), cache_key[:8])
    return result


def _persist_quality_crawl_videos(
    db: Session,
    bili_raw: list[dict],
    subject: str,
    knowledge_point: str,
    keywords: list[str],
) -> int:
    """
    将高质量的爬虫视频入库（URL去重 + 评分过滤）

    返回: 成功入库数量
    """
    if not bili_raw or not subject:
        return 0

    saved_count = 0
    try:
        # 取出本地已存在的 URL
        existing_urls = {
            row[0] for row in db.query(VideoResource.url).filter(
                VideoResource.is_deleted == False
            ).all() if row[0]
        }

        for raw in bili_raw:
            url = raw.get("url", "")
            if not url or url in existing_urls:
                continue

            # 用本地评分逻辑评估该爬虫视频
            kw_score, final, _ = _fused_score(raw, keywords, knowledge_point)
            if final < 0.5:  # 质量门槛
                continue

            try:
                new_video = VideoResource(
                    title=raw.get("title", "")[:255],
                    url=url,
                    platform=raw.get("platform", "Bilibili"),
                    author=raw.get("author", "")[:128] if raw.get("author") else None,
                    cover_url=_normalize_cover_url(raw.get("cover_url", "")),
                    duration=raw.get("duration", ""),
                    subject=subject,
                    knowledge_point=knowledge_point or None,
                    description=raw.get("description", "")[:500] if raw.get("description") else None,
                    play_count=raw.get("play_count", 0) or 0,
                    quality_score=int(final * 100),
                    crawl_source="realtime",
                    is_active=True,
                )
                db.add(new_video)
                existing_urls.add(url)
                saved_count += 1
                if saved_count >= 5:  # 一次最多入库5条
                    break
            except Exception as e:
                logger.warning("爬虫视频入库失败: %s, url=%s", e, url)
                continue

        if saved_count > 0:
            db.commit()
            logger.info("高质量爬虫视频入库: count=%d", saved_count)
    except Exception as e:
        logger.error("爬虫视频入库异常: %s", e)
        db.rollback()

    return saved_count


def _apply_user_preference_weight(
    db: Session,
    scored: list[tuple[float, float, str, Any, str]],
    user_id: int,
) -> None:
    """
    个性化加权：用户点击过的作者/知识点视频加权 +0.1

    不改变评分排序的主逻辑，只在匹配度相同时倾向于用户偏好的视频
    """
    try:
        from datetime import datetime, timedelta
        from models import VideoViewLog

        # 查询用户最近30天的点击记录（去重 author + knowledge_point）
        recent_time = datetime.utcnow() - timedelta(days=30)
        logs = (
            db.query(VideoViewLog)
            .filter(VideoViewLog.user_id == user_id)
            .filter(VideoViewLog.create_time >= recent_time)
            .all()
        )

        if not logs:
            return

        # 收集用户偏好
        preferred_authors = {log.author for log in logs if log.author}
        preferred_kps = {log.knowledge_point for log in logs if log.knowledge_point}

        # 加权
        user_weight = 0.1
        for i, (kw_score, final, label, video, source) in enumerate(scored):
            video_author = video.author if isinstance(video, VideoResource) else video.get("author", "")
            video_kp = video.knowledge_point if isinstance(video, VideoResource) else video.get("knowledge_point", "")

            bonus = 0.0
            if video_author and video_author in preferred_authors:
                bonus += user_weight
            if video_kp and video_kp in preferred_kps:
                bonus += user_weight * 0.5

            if bonus > 0:
                scored[i] = (kw_score, final + bonus, label, video, source)
    except Exception as e:
        logger.warning("用户偏好加权失败: %s", e)


# ============================================================================
# 第六部分：兼容旧接口
# ============================================================================

# 为了向后兼容，保留原函数签名但调用新实现
def recommend_videos(
    db: Session,
    subject: str = "",
    knowledge_point: str = "",
    question_text: str = "",
    limit: int = 8,
) -> list[dict]:
    """
    兼容旧接口的视频推荐

    注意：新代码应使用 recommend_videos_v2
    """
    result = recommend_videos_v2(
        db,
        question_id=None,
        subject=subject,
        knowledge_point=knowledge_point,
        question_text=question_text,
        limit=limit,
        use_llm=True,
    )
    return result.get("items", [])


# ============================================================================
# 第七部分：知识点详情页专用 - 王道视频优先
# ============================================================================
#
# 规则（与"智能出题推荐"分离，互不影响）：
#   1. 仅当 knowledge_point_id 命中 DB 中的 KnowledgePoint 时生效
#   2. 匹配三档强度（强/中/弱），低于"中"质量门槛的全部丢弃（防"基本概念"误匹配）
#   3. 同档内按分数 + id 稳定排序，返回 1 ~ max_count 条
#   4. 0 命中直接空，不回退到爬虫/seed，避免无关视频混进学习资源
#   5. 智能出题（带 question_text）的推荐路径完全不动
# ============================================================================

# 通用后缀/词缀：太常见，作为 token 比对会引发"X的基本概念"误匹配"Y的基本概念"
GENERIC_KP_SUFFIXES = (
    "的基本概念", "的概念", "的基本思想", "的基本原理", "的基本结构",
    "的定义", "的定义和基本操作", "的定义和性质", "的定义及特点",
    "的特点", "的性质", "的特性",
    "的表示", "的表示方法", "的表示和运算",
    "的实现", "的实现方法", "的实现方式",
    "的方法", "的算法", "的算法实现",
    "的操作", "的基本操作", "的应用", "的应用举例",
    "的存储", "的存储结构", "的物理存储", "的物理结构", "的逻辑结构",
    "的引入", "的引出", "的引入和动机", "的由来", "的起源",
    "的组成", "的组成和特征",
    "的分类", "的分类和比较",
    "的对比", "的比较", "的异同",
    "的用途", "的作用", "的意义",
    "的总结", "的小结", "的回顾", "的内容",
    "和算法", "的算法评价",
    # 单字后缀：用于将"内存管理概念" 还原为 "内存管理"，但保留这些词
    # 在 kp_name / v_kp 字面意义（避免丢失"机制/原理/概念"等判别性术语）
    "概念", "定义", "特点", "性质", "特性", "原理", "机制",
    "实现", "方法", "表示", "应用", "操作", "存储", "结构",
    "分类", "比较", "由来", "起源", "用途", "作用", "意义",
)
GENERIC_KP_SUFFIXES_BARE = (  # 慎用：与"的X"形式分开，避免过度剥离
    "的实现", "的实现方法", "的实现方式",
    "的方法", "的算法", "的算法实现",
    "小结", "回顾", "总结",
)
GENERIC_KP_SUFFIXES = GENERIC_KP_SUFFIXES + GENERIC_KP_SUFFIXES_BARE

GENERIC_STOP_TOKENS = {
    # 中文 1-2 字冠词/连词/泛指
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要",
    "去", "你", "会", "着", "没", "看", "好", "自", "己", "这", "那", "这个", "那个", "与", "及", "或", "并", "把",
    "被", "让", "由", "向", "对", "为", "以", "等", "如", "即", "则", "再", "其", "其他", "其它",
    # 学科/课程/考试泛称
    "408", "考研", "王道", "课程", "基础", "入门", "讲解", "教程", "学习", "复习", "考试",
}

# 同义词/翻译表：用于在 v_kp / v_title 中识别 KP section 的"另一说法"
# 例：KP section="高速缓冲存储器"，但王道 v_kp 全用英文 "Cache"
# → 当 sec_token "高速缓冲存储器" 不命中时，"Cache" 应视为同义命中
WANGDAO_SECTION_SYNONYMS = {
    # 计算机组成原理
    "高速缓冲存储器": ["Cache", "高速缓存", "高速缓冲"],
    "高速缓存": ["Cache", "高速缓冲存储器", "高速缓冲"],
    "虚拟存储器": ["虚拟存储", "Virtual Memory", "虚存"],
    "主存储器": ["主存", "内存", "Main Memory"],
    "外部存储器": ["外存", "辅存", "二级存储器", "Secondary Storage"],
    "磁盘存储器": ["磁盘", "硬盘", "磁表面存储器"],
    "中央处理器": ["CPU", "处理器", "Central Processing Unit"],
    "运算器": ["ALU", "算数逻辑单元", "算术逻辑单元"],
    "控制器": ["Control Unit", "CU"],
    "指令系统": ["ISA", "指令集", "Instruction Set"],
    "指令集体系结构": ["ISA", "Instruction Set Architecture", "指令系统"],
    "数据通路": ["Datapath", "数据通路的功能和基本结构"],
    "总线": ["BUS", "Bus"],
    "指令流水线": ["Pipeline", "流水线"],
    "微程序": ["Microprogram", "微程序控制器"],
    "存储器概述": ["存储系统基本概念", "存储器的基本概念", "存储器层级结构"],
    "寻址方式": ["寻址", "指令寻址", "数据寻址", "立即寻址", "直接寻址", "间接寻址"],
    "通道方式": ["通道", "Channel"],
    # 操作系统
    "虚拟内存管理": ["虚拟内存", "虚拟存储", "Virtual Memory", "虚存管理"],
    "进程管理": ["进程", "Process"],
    "处理机调度": ["CPU调度", "调度"],
    "进程同步": ["同步", "Synchronization", "进程同步与互斥"],
    "死锁": ["Deadlock", "死锁处理"],
    "内存管理": ["Memory Management", "存储管理"],
    "文件系统": ["File System", "FS"],
    "设备管理": ["I/O管理", "IO管理", "设备管理概述"],
    "操作系统发展历程": ["操作系统的发展与分类", "操作系统发展", "OS发展历程", "OS的发展历程", "操作系统演化"],
    "操作系统的基本概念": ["操作系统的概念", "操作系统的概念、功能和目标", "OS基本概念"],
    "操作系统的运行环境": ["操作系统的运行机制", "OS运行环境", "OS运行机制", "运行机制"],
    "本章疑难点": ["疑难点", "本章总结", "本章复习", "复习课", "本章小结"],
    "设备独立性软件": ["缓冲区管理", "假脱机技术", "SPOOLing", "设备独立性"],
    # 数据结构
    "线性表": ["Linear List", "线性结构"],
    "栈": ["Stack"],
    "队列": ["Queue"],
    "串": ["String"],
    "数组": ["Array"],
    "树": ["Tree", "树形结构"],
    "二叉树": ["Binary Tree"],
    "图": ["Graph", "图结构"],
    "查找": ["Search", "检索"],
    "排序": ["Sort", "Sorting"],
    "递归": ["Recursion"],
    "存储结构": ["Storage Structure"],
    "链式表示": ["单链表", "双链表", "循环链表", "静态链表", "链表"],
    "顺序表示": ["顺序表"],
    "树型查找": ["二叉排序树", "平衡二叉树", "B树", "B+树", "二叉查找树", "BST", "AVL"],
    "内部排序": ["插入排序", "冒泡排序", "快速排序", "堆排序", "希尔排序", "归并排序", "选择排序"],
    "图的应用": ["最小生成树", "最短路径", "拓扑排序", "关键路径", "Dijkstra", "Floyd", "Prim", "Kruskal"],
    "线索二叉树": ["二叉树的线索化", "线索二叉树的概念", "中序线索"],
    "二叉树的遍历": ["二叉树的先中后序遍历", "二叉树遍历", "层次遍历"],
    # 计算机网络
    "物理层": ["Physical Layer"],
    "数据链路层": ["Data Link Layer", "链路层"],
    "网络层": ["Network Layer"],
    "传输层": ["Transport Layer"],
    "应用层": ["Application Layer"],
    "TCP": ["传输控制协议", "Transmission Control Protocol"],
    "UDP": ["用户数据报协议", "User Datagram Protocol"],
    "IP": ["网际协议", "Internet Protocol"],
    "路由": ["Routing", "路由选择"],
    "介质访问控制": ["MAC", "Medium Access Control", "媒体接入控制"],
    "计算机网络概述": ["计算机网络的概念", "计算机网络的组成", "计算机网络的分类", "计算机网络的概念（咸鱼版）"],
    "计算机网络体系结构与参考模型": ["计算机网络分层结构", "OSI参考模型", "TCP/IP参考模型", "计算机网络体系结构"],
    "数据链路层设备": ["以太网交换机", "网桥", "集线器", "交换机"],
}


def _section_synonym_hits(sec_text: str, v_text: str) -> int:
    """检查 sec_text 在 v_text 中是否有同义词命中，返回最强命中长度（0 表示未命中）。"""
    if not sec_text or not v_text:
        return 0
    if sec_text in v_text:
        return len(sec_text)
    syns = WANGDAO_SECTION_SYNONYMS.get(sec_text, [])
    for s in syns:
        if s and s in v_text:
            return len(s)
    return 0


def _strip_generic_suffix(text: str) -> str:
    """去掉通用后缀，便于做"裸名"匹配。

    例：
      "数据结构的基本概念" -> "数据结构"
      "二叉树的遍历"       -> "二叉树的遍历"（无匹配后缀，保持原样）
      "排序"               -> "排序"
      "数据结构的三要素（旧版）" -> "数据结构的三要素"（再去掉"的三要素"...剥到不能再剥）
    """
    if not text:
        return ""
    # 先剥括号注解
    import re as _re
    text = _re.sub(r"[\(（][^\)）]*[\)）]\s*$", "", text).strip()
    changed = True
    while changed:
        changed = False
        for sfx in GENERIC_KP_SUFFIXES:
            if text.endswith(sfx) and len(text) - len(sfx) >= 2:
                text = text[: -len(sfx)].strip()
                changed = True
                break
    return text


def _wangdao_match_score(
    video: VideoResource,
    kp_name: str,
    kp_section: str,
    subject: str,
) -> int:
    """
    计算王道视频与目标知识点的匹配分（0-100）。分高 = 越贴合。

    关键防误判规则：
      - 比较前先把 kp/v_kp 的"subject 前缀"剥掉（如"数据结构XXX"→"XXX"）
      - 如果两边剥后一边为空（或只剩 1-2 字常见词），说明只是共享科目名，不算匹配
      - 例：KP section="数据结构的基本概念" vs v_kp="数据结构的三要素（旧版）"
        剥 subject 后剩 "的基本概念" vs "的三要素" → 完全不同 → 不匹配

    评分规则（自上而下取 max，避免弱匹配污染强匹配）：
      100  kp_name  == v_kp
       95  去后缀后 kp_name  == 去后缀后 v_kp
       90  kp_name  ∈ v_kp
       85  去后缀后 kp_name  ∈ 去后缀后 v_kp
       80  v_kp     ∈ kp_name
       75  kp_name  == v_title 去掉"-"前缀后的部分
       70  kp_name  ∈ v_title（去前缀后）
       70  kp_section 的所有 token 都出现在 v_kp（强 section 命中）
       65  kp_section 的 token（3字+ 专属术语）出现在 v_kp
       60  kp_section == v_kp
       55  kp_section 的 token（2字 泛指）出现在 v_kp
       55  去后缀后 kp_section == 去后缀后 v_kp
       50  kp_section 的 token 出现在 v_title（标题中含章节信息）
       50  kp_section ∈ v_kp  或  v_kp ∈ kp_section（**要求专属部分**）
       45  kp_name 拆 token（去停用词）后全部出现在 v_kp（**要求专属部分**）
       40  kp_name 拆 token 后任一 token 出现在 v_kp（**要求专属部分**）
    """
    v_kp = (video.knowledge_point or "").strip()
    v_title = (video.title or "").strip()
    score = 0

    # 通用：剥 subject 前缀
    kp_name_specific = _strip_subject_prefix(kp_name, subject)
    v_kp_specific = _strip_subject_prefix(v_kp, subject)

    # 当 kp_section 存在且 ≠ kp_name 时，kp_name 只是"父章节"上下文
    # 此时父章节匹配不应压过"section 专属术语"匹配
    # 例：KP "内存管理/虚拟内存管理" 下，v_kp "内存管理的概念"（父章节匹配 95）
    #   不应压过 v_kp "虚拟内存的基本概念"（section 匹配）
    is_parent_only = bool(
        kp_section and kp_section not in {subject, ""} and kp_section != kp_name
    )
    # 父章节上下文下，所有 kp_name 匹配的得分上限
    # 必须 < WANGDAO_MIN_SCORE(45)，保证 parent 命中不通过质量门槛，
    # 从而触发 fallback 去找更精准的 section 视频（而非显示父章节不相关视频）
    parent_cap = 40 if is_parent_only else 100

    if kp_name and kp_name not in {subject, ""}:
        if v_kp == kp_name:
            score = max(score, min(100, parent_cap))
        # 去后缀再比
        kp_stem = _strip_generic_suffix(kp_name)
        v_stem = _strip_generic_suffix(v_kp)
        if kp_stem and v_stem:
            if kp_stem == v_stem:
                score = max(score, min(95, parent_cap))
            elif len(kp_stem) >= 2 and kp_stem in v_stem:
                score = max(score, min(85, parent_cap))
            # 再剥一层"的"：处理"数据结构三要素" vs "数据结构的三要素"
            kp_stem_nd = kp_stem.replace("的", "")
            v_stem_nd = v_stem.replace("的", "")
            if (
                kp_stem_nd and v_stem_nd
                and len(kp_stem_nd) >= 2
                and kp_stem_nd == v_stem_nd
            ):
                score = max(score, min(60, parent_cap))
        if v_kp and kp_name in v_kp:
            score = max(score, min(90, parent_cap))
        if v_kp and v_kp in kp_name:
            score = max(score, min(80, parent_cap))
        v_title_part = v_title.split(" - ", 1)[-1] if " - " in v_title else v_title
        if v_title_part:
            if v_title_part == kp_name:
                score = max(score, min(75, parent_cap))
            if kp_name in v_title_part:
                score = max(score, min(70, parent_cap))

    if kp_section and kp_section not in {subject, ""}:
        if v_kp == kp_section:
            score = max(score, 60)
        sec_stem = _strip_generic_suffix(kp_section)
        v_stem2 = _strip_generic_suffix(v_kp)
        if sec_stem and v_stem2:
            if sec_stem == v_stem2:
                score = max(score, 55)
            elif len(sec_stem) >= 2 and sec_stem in v_stem2:
                # ★ 必须"专属部分"也包含，subject 前缀不算
                sec_specific = _strip_subject_prefix(sec_stem, subject)
                v_specific = _strip_subject_prefix(v_stem2, subject)
                if _is_meaningful_topic(sec_specific) and _is_meaningful_topic(v_specific):
                    if sec_specific in v_specific or v_specific in sec_specific:
                        score = max(score, 50)
            elif len(v_stem2) >= 2 and v_stem2 in sec_stem:
                # ★ 对称检查：v_stem2 是 sec_stem 的"核心词子集"
                # 例：sec_stem="虚拟内存管理", v_stem2="虚拟内存" → True
                # 这种情况 v_kp 是 section 的具体化（"虚拟内存"是"虚拟内存管理"的核心）
                #
                # 严格性：v_stem2 应是 sec_stem 剥掉"尾部泛指后缀"后的核心
                # 反例：sec_stem="操作系统的运行环境" (8字), v_stem2="操作系统的运行" (6字)
                #       剩下的"环境"是判别性词，剥错 → 拒绝匹配
                tail = sec_stem[len(v_stem2):]
                if len(tail) <= 2 and tail in {"管理", "概念", "技术", "方法", "基础", "原理", "机制", "概述", "应用", "总览", "结构", "组成", "类型", "形式", "实现"}:
                    sec_specific = _strip_subject_prefix(sec_stem, subject)
                    v_specific = _strip_subject_prefix(v_stem2, subject)
                    if _is_meaningful_topic(sec_specific) and _is_meaningful_topic(v_specific):
                        if v_specific in sec_specific or sec_specific in v_specific:
                            score = max(score, 50)
            # 同样剥"的"
            sec_nd = sec_stem.replace("的", "")
            v_nd = v_stem2.replace("的", "")
            if sec_nd and v_nd and len(sec_nd) >= 2 and sec_nd == v_nd:
                score = max(score, 50)
        if v_kp and (kp_section in v_kp or v_kp in kp_section):
            # ★ 同样要求"专属部分"非空
            sec_specific = _strip_subject_prefix(kp_section, subject)
            v_specific = _strip_subject_prefix(v_kp, subject)
            if _is_meaningful_topic(sec_specific) and _is_meaningful_topic(v_specific):
                if sec_specific in v_specific or v_specific in sec_specific:
                    score = max(score, 50)

    # === 新增：Section token 匹配（解决"特殊矩阵"等专属术语被遗漏）===
    # 当 KP 有明确 section 时，section 中的"判别性术语"（如"特殊矩阵"）
    # 出现在 v_kp 中，应作为强相关信号。这能解决：
    #   - KP section="数组和特殊矩阵" → 命中视频"3.4.1-3.4.4_特殊矩阵的压缩存储"
    #   - KP section="二叉树的遍历" → 命中"二叉树的先中后序遍历"等
    #
    # 泛指 token 集合：这些 token 即使匹配也说明不了"专属于此 section"
    # 例：section="图的基本概念" → "图" 是判别性的，但"基本概念"是泛指
    #     当 v_kp 只命中"基本概念"（如"队列的基本概念"）时，不应给高分
    GENERIC_SECTION_TOKENS = {
        "基本概念", "基本思想", "基本原理", "基本结构", "基本操作", "基本方法", "基本术语",
        "概念", "定义", "思想", "原理", "机制", "结构", "组成", "概述", "简介", "介绍",
        "实现", "方法", "表示", "应用", "操作", "存储", "分类", "比较", "由来", "起源",
        "用途", "作用", "意义", "总结", "小结", "回顾", "内容",
        "基本", "总的", "总论", "总体", "一般", "基础", "通用", "常用",
        "计算机", "数据结构", "操作系统", "组成原理",
    }
    if kp_section and kp_section not in {subject, ""} and v_kp:
        sec_tokens = _split_kp_tokens(kp_section, exclude={subject})
        if sec_tokens and _is_meaningful_topic(v_kp_specific):
            v_target = v_kp_specific + v_kp  # 优先在 v_kp 专属部分找
            sec_hits = [t for t in sec_tokens if t in v_target]
            if sec_hits:
                # 区分"判别性 token"和"泛指 token"
                discriminative_hits = [t for t in sec_hits if t not in GENERIC_SECTION_TOKENS and len(t) >= 2]
                max_len = max(len(t) for t in sec_hits)
                n_hits = len(sec_hits)
                n_total = len(sec_tokens)
                n_disc = len(discriminative_hits)
                if n_hits == n_total and n_total >= 2:
                    # 所有 section token 全部命中（多 token section）→ 强相关
                    score = max(score, 70)
                elif max_len >= 3 and n_disc >= 1:
                    # 命中 3字+ 专属术语（如"特殊矩阵"、"二叉树"）→ 中强相关
                    score = max(score, 65)
                elif max_len >= 3 and n_disc == 0:
                    # 只命中泛指 token（如"基本概念"4字）→ 弱相关
                    # 这是 section 偏泛指的情况，命中只说明"是同章节"而非"专属"
                    score = max(score, 50)
                else:
                    # 仅命中 2字 泛指术语 → 中等相关
                    # 但要避免"next数组"误匹配"数组"——要求 token 出现在 v_kp 开头/结尾
                    # 且 token 边界前/后是中文/标点/空白（不能紧贴英文/数字，如 "next数组"）
                    def _is_standalone(token, text):
                        """检查 token 在 text 中是否作为独立词出现（不被英文/数字粘住）"""
                        idx = 0
                        while True:
                            i = text.find(token, idx)
                            if i < 0:
                                return False
                            # 检查前一个字符
                            if i > 0 and re.match(r"[A-Za-z0-9]", text[i - 1]):
                                idx = i + 1
                                continue
                            # 检查后一个字符
                            j = i + len(token)
                            if j < len(text) and re.match(r"[A-Za-z0-9]", text[j]):
                                idx = i + 1
                                continue
                            return True

                    end_hit = any(_is_standalone(t, v_kp) and v_kp.endswith(t) for t in sec_hits)
                    leading_hit = any(_is_standalone(t, v_kp) and v_kp.startswith(t) for t in sec_hits)
                    if leading_hit or end_hit:
                        # 2字 token 在开头/结尾（且独立成词）→ 中等相关（>50，确保能压过 kp_name 50 匹配）
                        score = max(score, 55)
                    # 否则不计分（避免复合词中的 2字 token 误匹配，如 "next数组"）

            # 标题中可能含更具体的章节信息（如"3.4.1-3.4.4_特殊矩阵的压缩存储"）
            # 对 title 单独做一次 section token 匹配
            if v_title:
                title_hits = [t for t in sec_tokens if t in v_title]
                if title_hits:
                    max_len = max(len(t) for t in title_hits)
                    if max_len >= 3:
                        score = max(score, 50)
                    else:
                        # 2字 泛指：要求在标题中也是"leading" 位置
                        leading_in_title = any(
                            t in v_title and (
                                v_title.startswith(t)
                                or t + '的' in v_title
                                or t + '、' in v_title
                                or t + '_' in v_title
                            )
                            for t in title_hits
                        )
                        if leading_in_title:
                            score = max(score, 45)

            # ★ 新增：同义词命中（处理"高速缓冲存储器" vs "Cache" 等翻译差异）
            # 当 sec_tokens 字面都没在 v_kp/v_title 命中时（同义/翻译问题），
            # 通过 WANGDAO_SECTION_SYNONYMS 翻译表查一次
            syn_kp = _section_synonym_hits(kp_section, v_kp)
            syn_title = _section_synonym_hits(kp_section, v_title) if v_title else 0
            if syn_kp or syn_title:
                syn_len = max(syn_kp, syn_title)
                if syn_len >= 4:
                    # 4字+ 强同义（如 "Cache" 4字 / "高速缓存" 4字）→ 中等相关
                    score = max(score, 55)
                elif syn_len >= 2:
                    # 短同义（"CU" 2字）→ 弱相关
                    score = max(score, 45)

    # === Token 匹配：必须考虑专属部分 ===
    if kp_name and kp_name not in {subject, ""} and v_kp:
        name_tokens = _split_kp_tokens(kp_name, exclude={subject})
        # 过滤掉"在 v_kp 专属部分之外"的 token：即只保留"非 subject 前缀相关"的
        if name_tokens and _is_meaningful_topic(v_kp_specific):
            v_target = v_kp_specific + v_kp  # 优先看专属部分
            hits = [t for t in name_tokens if t in v_target]
            # 是否处于"父章节上下文"——只有当 kp_section 与 kp_name 不一致时，
            # section 才是 kp_name 的子主题；二者一致时 kp_name 即为当前 KP
            is_parent_context = bool(
                kp_section
                and kp_section not in {subject, ""}
                and kp_section != kp_name
            )
            if len(hits) == len(name_tokens) and len(hits) > 0:
                if is_parent_context:
                    # 父章节 token 全命中：例如 KP "树与二叉树/二叉树的遍历"
                    # 下，v_kp "平衡二叉树的删除" 的 name_token ['树','二叉树'] 全命中
                    # 但这是父章节相关，不是 section 相关 → 强制低分
                    score = max(score, 30)
                else:
                    score = max(score, 45)
            elif hits:
                # 单 token 命中：需要根据上下文判断强度
                max_len = max(len(t) for t in hits)
                if is_parent_context:
                    # user 在 section 上，kp_name 是父章节 → 单 token 命中
                    # 仅能说明"在同章节"但未必是当前 section，强制低分（不通过 45 门槛）
                    score = max(score, 25)
                else:
                    # 无 section 或 section == kp_name：kp_name 即当前 KP
                    # 2字 泛指 术语（如"进程"、"线程"）若 KP 聚焦（≤2 token）也接受
                    if max_len >= 3 or len(name_tokens) <= 2:
                        score = max(score, 45)
                    else:
                        score = max(score, 40)

    return score


def _wangdao_section_alignment(
    video: VideoResource,
    kp_name: str,
    kp_section: str,
    subject: str,
) -> int:
    """
    计算王道视频与目标 section 的"对齐度"（0-100），仅用于同分排序时的 tie-breaker。

    核心思想：v_kp 的开头部分与 section 越对齐 → 越像"专门讲这个 section 的视频"
        - 100: v_kp 以 sec_stem 开头
        - 80:  v_kp 以 sec_stem + "的" 等小差异开头
        - 70:  v_kp 以 section 的首个长 token（≥3字）开头
        - 50:  section 出现在 v_kp 标题中
        - 30:  section token 在 v_kp 中是修饰成分
        - 0:   section 不在 v_kp 中

    例：KP section="浮点数的表示与运算"
        - "浮点数的表示_IEEE_754"                → 100（v_kp 以 "浮点数的表示" 开头）
        - "浮点数的表示_IEEE_754（例题训练）"    → 80
        - "浮点数的表示范围、几种特殊状态（上）"  → 70
        - "浮点数的加减运算（溢出问题）"         → 50
    """
    v_kp = (video.knowledge_point or "").strip()
    v_title = (video.title or "").strip()
    if not kp_section or kp_section in {subject, ""} or not v_kp:
        return 0

    # 1) v_kp 跟 kp_section 的开头 / 包含关系（去后缀后比较）
    sec_stem = _strip_generic_suffix(kp_section)
    v_stem = _strip_generic_suffix(v_kp)
    if sec_stem and v_stem:
        if v_stem.startswith(sec_stem):
            # v_kp 完整地以 section 开头（如 sec="栈", v="栈的基本概念"）
            return 100
        if sec_stem in v_stem[:len(sec_stem) + 2]:
            return 80
        # 去"的"后比较：处理"数据结构三要素" vs "数据结构的三要素" 等同义形式
        sec_nd = sec_stem.replace("的", "")
        v_nd = v_stem.replace("的", "")
        if sec_nd and v_nd and len(sec_nd) >= 2 and sec_nd == v_nd:
            return 90
        # ★ 新增：v_stem 是 sec_stem 的子集（v_kp 是 section 的具体化）
        # 例：sec_stem="虚拟内存管理"（6字），v_stem="虚拟内存"（4字）→ 4字 是 6字 的"核心词"
        if len(v_stem) >= 3 and v_stem in sec_stem and len(sec_stem) - len(v_stem) <= 3:
            # v_stem 是 sec_stem 剥掉"管理/概念/机制/概述/结构"等泛指后缀后的核心
            tail = sec_stem[len(v_stem):]
            if tail in {"管理", "概念", "技术", "方法", "基础", "原理", "机制", "概述", "应用", "总览", "结构", "组成", "类型", "形式", "实现", "简介", "系统", "存储"}:
                return 95
            return 80

    # 2) section 的"长 token"在 v_kp 开头 → 按 token 长度给高分
    sec_tokens = _split_kp_tokens(kp_section, exclude={subject})
    if sec_tokens:
        long_tokens = sorted(
            [t for t in sec_tokens if len(t) >= 3],
            key=lambda x: -len(x),
        )
        for t in long_tokens:
            if v_stem.startswith(t) or v_kp.startswith(t):
                # 按 token 长度分级：≥6 字 → 90，4-5 字 → 70，3 字 → 55
                if len(t) >= 6:
                    return 90
                if len(t) >= 4:
                    return 70
                return 55
            if v_stem.startswith(t[:len(t)-1]) and len(t) >= 4:
                return 65

    # 3) 标题里包含 section 名 → 中等对齐
    if v_title and sec_stem and sec_stem in v_title:
        return 50

    # 4) section token 在 v_kp 中是修饰成分
    if sec_tokens and any(t in v_kp for t in sec_tokens):
        return 30

    return 0


def _wangdao_llm_keyword_score(
    video,
    kp_keywords: list[str],
    kp_section: str = "",
    subject: str = "",
) -> int:
    """
    基于 LLM 离线关键词的匹配分（0-100）。

    思想：LLM 已经把 KP 的"同义/翻译/相关术语"提取为 kp_keywords 列表。
    视频 v_kp / v_title 命中其中越多 → 越相关。
    同时参考视频自身的 keywords 字段（双方 LLM 都认为相关 → 强信号）。

    重要约束（防 LLM 关键词"误升级" sub-topic 视频）：
      - 即使 LLM 关键词命中多，但 v_kp 跟 section 字面无共享词时（说明这是 sub-topic 视频），
        不能压过"v_kp 标题直接对应 section"的视频。
      - 解决：把 sub-topic 视频的 LLM 关键词加分"封顶"在 50 分（除非 v_kp/v_title 直接含 section 核心词）。

    评分规则：
      n = kp_keywords 在 v_kp / v_title 中命中数（排除 subject）
      n >= 3              → 75（多关键词命中，强相关）
      n == 2              → 65
      n == 1              → 50/55/60（视 common 数量）
      双方 keywords 交集>=2 → 55（LLM 双向验证）
      双方 keywords 交集>=3 → 60
      其他                 → 0
    """
    v_kp = (video.knowledge_point or "").strip()
    v_title = (video.title or "").strip()
    if not kp_keywords or not v_kp:
        return 0

    v_kp_lower = v_kp.lower()
    v_title_lower = v_title.lower() if v_title else ""
    subject_lower = (subject or "").strip().lower()

    # 维度 1：v_kp / v_title 命中 KP 关键词的命中数（去重，每个 kw 只算 1 次，排除 subject）
    n_hit = 0
    seen_hit: set[str] = set()
    for kw in kp_keywords:
        if not kw:
            continue
        kw_l = kw.lower()
        if kw_l in seen_hit:
            continue
        # ★ 排除 subject 自身：避免"操作系统"出现在所有 OS 视频的 v_title 里
        # → 把所有 OS 视频都算成"命中"
        if subject_lower and kw_l == subject_lower:
            continue
        if kw_l in v_kp_lower or (v_title_lower and kw_l in v_title_lower):
            n_hit += 1
            seen_hit.add(kw_l)

    # 维度 2：双方 LLM 关键词交集
    common_count = 0
    v_kws_str = (getattr(video, "keywords", "") or "").strip()
    if v_kws_str:
        from services.keyword_extractor import _deserialize_kws as _kw_load
        v_kws = _kw_load(v_kws_str)
        if v_kws:
            kp_set = {k.lower() for k in kp_keywords if k}
            v_set = {k.lower() for k in v_kws if k}
            common = kp_set & v_set
            common_count = len(common)

    # 字面相关性保护：v_kp 跟 section 是否字面相关
    # 当 v_kp 跟 section 完全字面无关时（说明该视频是 sub-topic），
    # LLM 关键词加分封顶 60 分（避免压过 v_kp 命中 section 的视频）
    section_specific_present = False
    if kp_section and subject:
        # 复用既有工具：判断 v_kp 跟 section 是否有"section token 命中"
        # 用更宽松的检查：v_kp 包含 section 任意 3+字 token
        sec_tokens = _split_kp_tokens(kp_section, exclude={subject})
        long_tokens = [t for t in sec_tokens if len(t) >= 3]
        v_target = (v_kp + " " + v_title).lower()
        if any(t.lower() in v_target for t in long_tokens):
            section_specific_present = True

    base_score = 0
    # 优先级：n_hit 直接命中（更可靠）> common 双向验证
    if n_hit >= 3:
        base_score = 75
    elif n_hit == 2:
        base_score = 65
    elif n_hit == 1:
        # 1 个直接命中 + common>=1 → 升级
        if common_count >= 2:
            base_score = 60
        elif common_count == 1:
            base_score = 55
        else:
            base_score = 50
    elif common_count >= 3:
        base_score = 60
    elif common_count >= 2:
        base_score = 55
    elif common_count == 1:
        base_score = 45

    # 字面保护：sub-topic 视频封顶 50（不让它压过 v_kp 命中 section 的视频）
    # 关键：v_kp 跟 section 字面不相关时（sub-topic），即使 LLM 关键词命中多，
    # 也不能压过 section-title 视频（section-title 视频 final 通常 50+，大多 60+）
    if base_score >= 55 and not section_specific_present:
        base_score = 50

    return base_score


def _strip_subject_prefix(text: str, subject: str) -> str:
    """剥掉 subject 前缀，剩下"专属"部分（去"的"首字）。"""
    if not text or not subject:
        return text
    t = text.strip()
    if t.startswith(subject):
        rest = t[len(subject):].lstrip("的、，, ").strip()
        return rest
    return t


def _is_meaningful_topic(text: str) -> bool:
    """判断一段文本是否够"具体"——不是空、不是只 1-2 字、能撑起一个话题。"""
    if not text:
        return False
    t = text.strip()
    if len(t) < 2:
        return False
    # 单独 1 个中文字或 2 个纯连词 → 不算
    if t in {"的", "与", "和", "或", "及", "中", "在", "为", "了"}:
        return False
    return True


def _split_kp_tokens(text: str, exclude: set[str] | None = None) -> list[str]:
    """
    把知识点名称拆成有意义的 token（拆出来的都是判别性较强的短语）。

    处理顺序：
      1) 同时考虑"原文本"和"去后缀文本"，合并 token
        例：原始 "内存管理概念" + 去后缀 "内存管理" → ['内存管理概念', '内存管理']
        这样可同时匹配:
          - v_kp "内存管理的概念"（通过 '内存管理' token）
          - v_kp "内存管理概念"（通过 '内存管理概念' token）
      2) 按分隔符（、，, 和与及或空格）切出"短语"——而非字面滑窗——避免"树与"、"与二"这种碎片
      3) 再在中文短语内按"的"切分，剥出更细的判别性 token
      4) 过滤停用词 + 1-字碎片

    例：
      "数据结构的基本概念" -> ["数据结构基本概念", "数据结构"]
      "进程与线程"          -> ["进程", "线程"]
      "树与二叉树"          -> ["树", "二叉树"]
      "栈、队列和数组"      -> ["栈", "队列", "数组"]
      "内存管理概念"        -> ["内存管理概念", "内存管理"]
      "CPU调度"             -> ["CPU", "调度"]
    """
    if not text:
        return []
    exclude = set(exclude or set()) | GENERIC_STOP_TOKENS

    # 1) 同时考虑"原文本"和"去后缀文本"（兼容"内存管理概念" 与 "内存管理的概念" 互匹配）
    stem = _strip_generic_suffix(text) or text
    sources = [text, stem] if stem != text else [text]

    out: list[str] = []
    seen: set[str] = set()

    for src in sources:
        # 1a) 整体作为 token 优先（"内存管理概念" 整串）——只在原文本中加
        if src == text and len(src) >= 1 and src not in exclude and src not in seen:
            # 整体原串（如 "内存管理概念" / "栈"）作为最强 token
            out.append(src)
            seen.add(src)
        # 1a-bonus) 即使整体已加入，也跑一次"和与及或"切，把更细的 token 抽出
        # 例：整体"浮点数的表示与运算"已加 → 仍要切出 "表示" / "运算" 用于匹配
        # "浮点数的表示_IEEE_754"（含 "表示"）和 "浮点数的加减运算"（含 "运算"）
        if len(src) >= 2:
            for sub in re.split(r"和|与|及|或", src):
                sub = sub.strip()
                if len(sub) >= 2 and sub not in exclude and sub not in seen:
                    out.append(sub)
                    seen.add(sub)
                # 再做"的"切（"浮点数的表示" → "浮点数" + "表示"）
                if "的" in sub and len(sub) >= 4:
                    for sub2 in re.split(r"的", sub):
                        sub2 = sub2.strip()
                        if len(sub2) >= 2 and sub2 not in exclude and sub2 not in seen:
                            out.append(sub2)
                            seen.add(sub2)
        # 1b) 中英文粗分
        raw_parts = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+", src)
        for p in raw_parts:
            if not p:
                continue
            # 英文/数字 整体保留
            if re.match(r"^[A-Za-z0-9]+$", p):
                if p.lower() not in {e.lower() for e in exclude} and p not in seen:
                    out.append(p)
                    seen.add(p)
                continue
            # 中文：按"短语分隔符"切分
            phrases = re.split(r"[、，, \t]+|和|与|及|或", p)
            for ph in phrases:
                ph = ph.strip()
                if len(ph) < 2 or ph in exclude or ph in seen:
                    continue
                out.append(ph)
                seen.add(ph)
                # 1c) 在中文短语内按"的"再切（"内存管理的概念" → "内存管理" + "概念"）
                if "的" in ph and len(ph) >= 4:
                    for sub in re.split(r"的", ph):
                        sub = sub.strip()
                        if len(sub) >= 2 and sub not in exclude and sub not in seen:
                            out.append(sub)
                            seen.add(sub)

    return out


def _normalize_cover_url(url: str) -> str:
    """统一 cover_url 为 https：H5/小程序/HTTPS 页会拒绝 http 图片（混合内容）。"""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def _proxy_bili_cover(url: str) -> str:
    """把 B 站图床 URL 转成代理端点 URL，绕过 Referer 防盗链。

    已本地化（/covers/...）或其他非 B 站图床 URL 直接返回原值。
    """
    if not url:
        return ""
    url = url.strip()
    # 已经是本地路径或代理端点 → 不处理
    if url.startswith("/covers/") or url.startswith("/api/"):
        return url
    # B 站图床 URL → 走代理端点
    if "hdslb.com" in url:
        from urllib.parse import quote
        return f"/api/videos/proxy-image?url={quote(url, safe='')}"
    return url


def _format_wangdao_item(video: VideoResource, match_score: int) -> dict:
    """把 VideoResource 行格式化为前端 videoCard 所需结构。"""
    return {
        "id": video.id,
        "title": video.title or "",
        "platform": video.platform or "Bilibili",
        "url": video.url or "",
        "cover_url": _normalize_cover_url(video.cover_url or ""),
        "duration": video.duration or "",
        "author": video.author or "王道计算机教育",
        "reason": video.reason or "王道官方 408 课程",
        "subject": video.subject or "",
        "knowledge_point": video.knowledge_point or "",
        "section": video.section or "",
        "quality_score": video.quality_score or 85,
        "match_level": "wangdao_exact" if match_score >= 80 else "wangdao_fuzzy",
        "keyword_match_score": round(min(match_score / 100.0, 1.0), 4),
        "final_score": round(min(match_score / 100.0, 1.0), 4),
        "source": "wangdao_db",
        "match_explanation": (
            f"📚王道官方 · 王道考研408公益课程 · 章节{video.section or '-'} · "
            f"{video.knowledge_point or ''}"
        ),
    }


# ============================================================================
# 数量与质量门槛（知识点页专用，不影响智能出题推荐）
# ============================================================================
WANGDAO_MIN_SCORE: int = 45   # 低于此分的命中直接丢弃（防"基本概念"串味）
WANGDAO_MAX_COUNT: int = 8    # 单次最多返回 8 条（保证同一章节的多个相关视频都能展示）
WANGDAO_MIN_COUNT: int = 1    # 至少返回 1 条时启用；=0 时不显示学习资源区


def recommend_wangdao_for_knowledge_point(
    db: Session,
    knowledge_point_id: int,
    limit: int | None = None,
) -> dict:
    """
    知识点详情页专用：规则匹配 DB 中的王道视频。

    数量规则（不再固定 3 条）：
      - 只保留 score >= WANGDAO_MIN_SCORE 的命中
      - 返回 1 ~ WANGDAO_MAX_COUNT 条（按 score 降序、同分按 id 倒序）
      - 0 命中 → 直接返回空（不回退爬虫/seed，避免混入不相关内容）

    返回结构：
        {
            "items": [...],
            "subject": str,
            "knowledge_point": str,
            "wangdao_matched": int,  # 过滤前命中数
            "wangdao_passed": int,   # 过滤后（过质量门槛）数
            "total_returned": int,
            "source_priority": "wangdao_db",
            "min_score": int,
            "max_count": int,
        }
    """
    point = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.id == knowledge_point_id, KnowledgePoint.is_deleted == False)
        .first()
    )
    if not point:
        return {
            "items": [],
            "subject": "",
            "knowledge_point": "",
            "wangdao_matched": 0,
            "wangdao_passed": 0,
            "total_returned": 0,
            "source_priority": "wangdao_db",
            "min_score": WANGDAO_MIN_SCORE,
            "max_count": WANGDAO_MAX_COUNT,
        }

    subject = point.subject or ""
    kp_name = (point.name or "").strip()
    kp_section = (point.section or "").strip()

    # 1) 拉同科目的全部王道视频（同科目一般 80-100 条，量很小，in-memory 评分即可）
    wd_videos = (
        db.query(VideoResource)
        .filter(
            VideoResource.subject == subject,
            VideoResource.crawl_source == "crawl_wangdao",
            VideoResource.is_deleted == False,
            VideoResource.is_active == True,
        )
        .all()
    )

    # 2) 规则打分 + 质量门槛过滤
    # 排序键：(-match_score, -section_alignment, -v_quality, v_kp_length, -v_id)
    #   - match_score:    核心匹配度（0-100）
    #   - section_alignment: section 对齐度（解决"都 65 分"时的排名问题）
    #   - v_quality:      视频质量分（quality_score 高的优先）
    #   - v_kp_length:    v_kp 短的优先（更聚焦）
    #   - -v_id:          新视频优先
    # ★ LLM 关键词作为加分维度（独立打分 max 100，与 match_score 取大后再加权重加成）
    from services.keyword_extractor import _deserialize_kws as _kw_load
    kp_kws = _kw_load(point.keywords or "")
    scored: list[tuple[int, int, int, int, int, int, VideoResource]] = []
    for v in wd_videos:
        s = _wangdao_match_score(v, kp_name, kp_section, subject)
        # LLM 关键词命中分（独立维度，传 section+subject 用于字面保护）
        llm_s = _wangdao_llm_keyword_score(v, kp_kws, kp_section, subject) if kp_kws else 0
        # 融合：取 max，但要求 LLM 关键词命中能"加成"
        # - 两者都命中时优先采用 LLM 关键词维度（语义更准）
        # - 规则命中但 LLM 没命中：保持规则结果
        if llm_s >= 60 and llm_s > s:
            # LLM 关键词强烈匹配 → 提升基础分
            s = max(s, llm_s)
        elif llm_s >= 40 and s > 0:
            # LLM 关键词弱命中 → 加成（但不超过规则结果+10）
            # ★ 修复：s=0 时不进 elif，避免"信号"这种 0 分视频被 +5 抬到 50 分
            s = min(100, max(s, llm_s) + 5)
        if s >= WANGDAO_MIN_SCORE:
            align = _wangdao_section_alignment(v, kp_name, kp_section, subject)
            v_quality = v.quality_score or 80
            v_kp_len = len(v.knowledge_point or "")
            # 保存 5 元组 + 实际生效的 final_score，避免重复计算
            scored.append((s, align, v_quality, v_kp_len, -v.id, llm_s, v))
    scored.sort(key=lambda x: (-x[0], -x[1], -x[2], x[3], x[4]))

    # 3) 应用上下限：取 1 ~ max_count
    max_n = min(limit, WANGDAO_MAX_COUNT) if limit else WANGDAO_MAX_COUNT
    if len(scored) < WANGDAO_MIN_COUNT:
        # 0 命中：不强凑，留空
        items: list[dict] = []
    else:
        items = []
        seen_urls: set[str] = set()
        for tup in scored[:max_n]:
            final_s, align, _, _, _, llm_s, v = tup
            # 透传 LLM 命中分到 item，调试用
            item = _format_wangdao_item(v, final_s)
            item["keyword_match_score"] = round(llm_s / 100, 2)
            if item["url"] and item["url"] not in seen_urls:
                items.append(item)
                seen_urls.add(item["url"])

    # 4) 王道不足 max_n 时的回退策略
    #    核心原则：王道有"强相关"命中时，不应被"泛相关"种子视频稀释
    #    - 有 ≥ 1 个高分（≥50）王道命中 → 信任王道的精准性，不再回退补足
    #    - 有 1+ 中分（45-49）命中、且未达 max_n → 用 section 名搜索，更精准
    #    - 0 命中 → 才退到 recommend_videos_v2（保留旧兜底）
    has_strong = any(tup[0] >= 50 for tup in scored)
    if has_strong:
        # 信任王道精准匹配，停止补足
        pass
    elif len(items) < max_n:
        # 中等命中或 0 命中：兜底到通用推荐
        # 优先用 section 名搜索（更精准），fallback 到 kp_name，最后到 subject
        fallback_query = kp_section or kp_name or subject
        try:
            fallback = recommend_videos_v2(
                db,
                question_id=None,
                subject=subject,
                knowledge_point=fallback_query,
                question_text=fallback_query,
                limit=max_n - len(items),
                use_llm=False,
            )
            seen_urls = {it["url"] for it in items if it.get("url")}
            for it in fallback.get("items", []):
                if not it.get("url") or it["url"] in seen_urls:
                    continue
                it["source"] = f"wangdao_db_fallback_{it.get('source', 'realtime')}"
                it["match_explanation"] = (
                    "📚王道暂无强匹配，" + (it.get("match_explanation") or "已为你补充相关推荐")
                )
                items.append(it)
                seen_urls.add(it["url"])
                if len(items) >= max_n:
                    break
        except Exception as exc:  # noqa
            logger.warning("王道回退失败 (kp_id=%s): %s", knowledge_point_id, exc)

    return {
        "items": items,
        "subject": subject,
        "knowledge_point": kp_name,
        "wangdao_matched": len(scored),
        "wangdao_passed": len(items),
        "total_returned": len(items),
        "source_priority": "wangdao_db",
        "min_score": WANGDAO_MIN_SCORE,
        "max_count": WANGDAO_MAX_COUNT,
    }
