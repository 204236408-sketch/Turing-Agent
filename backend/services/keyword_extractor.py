"""
LLM 离线关键词提取服务

用途：
  提前为 KnowledgePoint 和 VideoResource 生成"用于视频-KP 匹配"的关键词列表。
  匹配时纯字符串查表，零网络延迟。

设计：
  - KP 关键词应覆盖"同义/翻译/相关术语"，让 LLM 帮我们找"数据库里视频标题可能用的说法"
  - 视频关键词应覆盖"该视频讲的核心术语"，让 KP 关键词能命中它
  - 输出 3-5 个 2-4 字的短词
"""
import json
import logging
import time
from typing import Iterable

from services.llm_service import chat_json

logger = logging.getLogger(__name__)


# Prompt 设计：
# 给 LLM 一个 KP，要求它"想象"王道视频可能用什么标题来覆盖这个 KP，
# 列出这些"视频标题中可能出现的核心术语"（含同义/翻译）
# 注意：JSON 示例中用 {{}} 双花括号转义以兼容 str.format
KP_MATCHING_KEYWORD_PROMPT = """你是 408 考研计算机学科的"视频-KP 匹配关键词"专家。

任务：给定一个知识点（KP），列出 3-5 个最适合用来在 B 站王道视频标题中搜索到该 KP 相关视频的关键词。

要求（严格 JSON 格式，无其他内容）：
{{
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "reason": "选择这些关键词的理由简述（1 句话）"
}}

关键词选择原则（极其重要）：
1. **短词优先**：每个关键词 2-4 个字（中英文术语都可以）
2. **同义/翻译覆盖**：
   - 例：KP "高速缓冲存储器" → 关键词 ["Cache", "高速缓存", "高速缓冲", "高速缓冲存储器"]
   - 例：KP "虚拟内存管理" → 关键词 ["虚拟内存", "虚拟存储", "Virtual Memory", "页表", "缺页中断"]
   - 例：KP "TCP 流量控制" → 关键词 ["TCP", "流量控制", "拥塞控制", "滑动窗口"]
3. **子主题展开**：除核心词外，列出该 KP 的关键子主题（视频会按子主题拆分）
   - 例：KP "浮点数的表示与运算" → ["浮点数", "IEEE 754", "浮点加减", "浮点运算"]
4. **视频标题语言习惯**：B 站王道视频标题常用"xxx 是什么/基本概念/咸鱼版/原理/基本思想/基本结构/应用/实现/分类/例子/习题/例题"
   - 关键词以核心名词为主，不要带"是什么/基本概念"等修饰后缀
5. **避免重复或近义**：5 个关键词之间应尽量互补，不要把同一概念的不同说法都列出

输入：
科目：{subject}
知识点：{section} > {name}
正文摘要：{content_excerpt}
"""


# 给定一个视频（王道/B站），要求 LLM 提取该视频讲的核心术语
VIDEO_MATCHING_KEYWORD_PROMPT = """你是 408 考研计算机学科的"视频主题关键词"专家。

任务：给定一个视频的元信息（标题、所属 KP、所在章节），列出 3-5 个最能代表该视频所讲内容的核心关键词。

要求（严格 JSON 格式，无其他内容）：
{{
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "reason": "选择这些关键词的理由简述（1 句话）"
}}

关键词选择原则（极其重要）：
1. **短词优先**：每个关键词 2-4 个字（中英文术语都可以）
2. **该视频独有**：不要列所有该章节视频都会讲的通用词（如不要在每个"二叉树"视频都列"二叉树"）
   - 例：视频"二叉树的先序遍历" → ["先序遍历", "前序遍历", "二叉树遍历", "遍历序列"]
   - 例：视频"Cache 替换算法" → ["Cache", "替换算法", "LRU", "FIFO"]
3. **核心名词**：列视频标题里的核心术语
4. **中英文混用**：英文术语（Cache/TCP/IP/CPU/ALU 等）也要保留

输入：
科目：{subject}
章节：{section}
视频 KP 名称：{video_kp}
视频标题：{title}
视频描述：{description_excerpt}
"""


def _truncate(text: str, n: int = 300) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= n:
        return text
    return text[:n] + "…"


def _normalize_keywords(raw) -> list[str]:
    """把 LLM 返回的 keywords 列表清洗成干净的字符串列表"""
    if not raw or not isinstance(raw, list):
        return []
    out = []
    seen = set()
    for kw in raw:
        if not isinstance(kw, str):
            continue
        kw = kw.strip()
        # 去尾部"的"和空白
        kw = kw.strip(" 　的、，。")
        if not kw:
            continue
        # 长度限制
        if len(kw) > 12:
            continue
        if len(kw) < 1:
            continue
        # 去重
        if kw.lower() in seen:
            continue
        seen.add(kw.lower())
        out.append(kw)
        if len(out) >= 6:
            break
    return out


def _parse_keywords_from_llm(result_data) -> list[str]:
    """从 chat_json 返回的 data 中安全提取关键词列表"""
    if not result_data or not isinstance(result_data, dict):
        return []
    kws = result_data.get("keywords") or result_data.get("search_keywords") or []
    return _normalize_keywords(kws)


def extract_kp_matching_keywords(
    subject: str,
    section: str,
    name: str,
    content: str = "",
    max_retries: int = 2,
) -> list[str]:
    """
    提取 KP 用于匹配视频的关键词列表（3-5 个）。
    失败时返回空列表（不会抛异常）。
    """
    fallback = {"keywords": [], "reason": ""}

    user_prompt = KP_MATCHING_KEYWORD_PROMPT.format(
        subject=subject or "未知科目",
        section=section or "(无章节)",
        name=name or "(无名称)",
        content_excerpt=_truncate(content or "", 400),
    )

    messages = [
        {"role": "system", "content": "你只输出合法 JSON，不要任何其他文字。"},
        {"role": "user", "content": user_prompt},
    ]

    last_err = ""
    for attempt in range(max_retries):
        try:
            result = chat_json(messages, fallback, temperature=0.2, max_tokens=500)
            if not result.used_llm:
                last_err = result.error or "LLM 未启用"
                time.sleep(1.0 * (attempt + 1))
                continue
            kws = _parse_keywords_from_llm(result.data)
            if kws:
                return kws
            last_err = "LLM 返回空关键词"
        except Exception as e:
            last_err = f"异常: {e!r}"
        time.sleep(0.5 * (attempt + 1))

    logger.warning("KP 关键词提取失败: subject=%s section=%s name=%s err=%s",
                   subject, section, name, last_err)
    return []


def extract_video_matching_keywords(
    subject: str,
    section: str,
    video_kp: str,
    title: str,
    description: str = "",
    max_retries: int = 2,
) -> list[str]:
    """
    提取视频用于被 KP 匹配的关键词列表（3-5 个）。
    失败时返回空列表（不会抛异常）。
    """
    fallback = {"keywords": [], "reason": ""}

    user_prompt = VIDEO_MATCHING_KEYWORD_PROMPT.format(
        subject=subject or "未知科目",
        section=section or "(无章节)",
        video_kp=video_kp or "(无)",
        title=title or "(无标题)",
        description_excerpt=_truncate(description or "", 200),
    )

    messages = [
        {"role": "system", "content": "你只输出合法 JSON，不要任何其他文字。"},
        {"role": "user", "content": user_prompt},
    ]

    last_err = ""
    for attempt in range(max_retries):
        try:
            result = chat_json(messages, fallback, temperature=0.2, max_tokens=400)
            if not result.used_llm:
                last_err = result.error or "LLM 未启用"
                time.sleep(1.0 * (attempt + 1))
                continue
            kws = _parse_keywords_from_llm(result.data)
            if kws:
                return kws
            last_err = "LLM 返回空关键词"
        except Exception as e:
            last_err = f"异常: {e!r}"
        time.sleep(0.5 * (attempt + 1))

    logger.warning("视频关键词提取失败: title=%s err=%s", title, last_err)
    return []


# ============================================================
# DB 缓存读写辅助
# ============================================================
def _serialize_kws(kws: list[str]) -> str:
    return json.dumps(kws, ensure_ascii=False)


def _deserialize_kws(s: str) -> list[str]:
    if not s:
        return []
    try:
        v = json.loads(s)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, str)]
    except Exception:
        # 兼容旧格式（逗号分隔）
        return [x.strip() for x in s.split(",") if x.strip()]
    return []


def get_kp_keywords(kp) -> list[str]:
    """从 KP 对象的 keywords 字段加载已缓存的关键词列表（兼容旧逗号格式）"""
    if not kp:
        return []
    return _deserialize_kws(kp.keywords or "")


def get_video_keywords(video) -> list[str]:
    """从 VideoResource 对象的 keywords 字段加载已缓存的关键词列表"""
    if not video:
        return []
    return _deserialize_kws(getattr(video, "keywords", "") or "")


def set_kp_keywords(kp, kws: list[str]) -> None:
    """把关键词列表写回 KP.keywords（JSON 格式）"""
    if not kp:
        return
    kp.keywords = _serialize_kws(kws)


def set_video_keywords(video, kws: list[str]) -> None:
    """把关键词列表写回 VideoResource.keywords（JSON 格式）"""
    if not video:
        return
    video.keywords = _serialize_kws(kws)
