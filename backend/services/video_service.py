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

from models import VideoResource
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
            "cover_url": video.cover_url or "",
            "duration": video.duration or "",
            "author": video.author or "",
            "reason": video.reason or "",
            "subject": video.subject,
            "knowledge_point": video.knowledge_point or "",
            "quality_score": video.quality_score or 0,
        }
    else:
        item = {
            "id": 0,
            "title": video.get("title", ""),
            "platform": "Bilibili",
            "url": video.get("url", ""),
            "cover_url": video.get("cover_url", ""),
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
                    cover_url=raw.get("cover_url", ""),
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
