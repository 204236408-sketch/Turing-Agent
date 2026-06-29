from __future__ import annotations

from sqlalchemy.orm import Session

from agents.mistake_graph import get_mistake_graph, set_db
from models import Mistake, UserMemory
from services.llm_service import chat_json_with_fallback_models
from services.mastery_service import recalculate_mastery
from services.chroma_service import upsert_document
from config import settings


def confirm_cause(
    db: Session,
    user_id: int,
    answer_record_id: int,
    error_types: list[str],
    user_note: str,
    evidence_source: str,
    agent_suggested_types: list[str] | None = None,
) -> dict:
    """确认错因，写入错题本、长期记忆并更新掌握度。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        answer_record_id: 答题记录 ID。
        error_types: 错因类型列表。
        user_note: 用户备注。
        evidence_source: 证据来源。
        agent_suggested_types: Agent 建议的错因类型（可选）。

    Returns:
        dict: 包含 mistake_id, mastery_status, agent_steps, llm_used, llm_error。
    """
    set_db(db)
    initial_state = {
        "user_id": user_id,
        "answer_record_id": answer_record_id,
        "error_types": error_types or agent_suggested_types or [],
        "user_note": user_note,
        "evidence_source": evidence_source,
        "agent_suggested_types": agent_suggested_types or [],
        "mistake_id": None,
        "memory_id": None,
        "similar_mistakes": [],
        "agent_steps": [],
        "llm_used": False,
        "llm_error": "",
    }

    result = get_mistake_graph().invoke(initial_state)

    steps_out = []
    for s in result.get("agent_steps", []):
        steps_out.append({
            "name": s.get("name", ""),
            "input_summary": s.get("input_summary", ""),
            "output_summary": s.get("output_summary", ""),
            "duration_ms": s.get("duration_ms", 0),
            "status": s.get("status", ""),
        })

    return {
        "mistake_id": result.get("mistake_id"),
        "message": f"已写入错题、长期记忆和知识点掌握状态。",
        "mastery_status": result.get("mastery_status", ""),
        "weak_score": result.get("weak_score", 0),
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "agent_steps": steps_out,
    }


def infer_user_answer_from_ocr(
    db: Session,
    user_id: int,
    text: str,
    subject: str,
    knowledge_point: str,
) -> dict:
    """从 OCR 题干 + 知识点反推用户可能的作答,返回候选答案与置信度。

    用于前端上传错题照片后,在「你的答案」输入框预填 AI 推测答案。
    用户可一键采用或修改。

    v2 增强：
    1. 题型判断（选择题/填空题/简答题/判断题/应用题）
    2. 选择题答案格式约束（仅输出 A/B/C/D 单字母）
    3. 启发式：用户做错题时，优先推断最常错的"易错选项"
    4. 知识点结合：让 LLM 参考 subject / knowledge_point 给出领域相关答案
    """
    fallback = {
        "guessed_user_answer": "",
        "confidence": 0.0,
        "question_type": "未知",
        "reasoning": "题干信息不足或大模型暂不可用,请手动填写你的答案。",
    }
    if not text or len(text.strip()) < 8:
        return {**fallback, "reasoning": "OCR 文本过短,无法反推用户答案。"}

    # 启发式题型判断
    qtype, options = _detect_question_type(text)
    user_prompt_extra = ""
    if qtype == "选择题":
        options_text = " ".join(options[:5]) if options else "(未识别到选项)"
        user_prompt_extra = (
            f"\n【题型识别】本题为选择题,可见选项:{options_text}\n"
            f"约束: guessed_user_answer 只能是一个字母(A/B/C/D/E),代表用户最可能选择的错误选项。"
            f"易错选项优先于正确选项（因为这是错题导入,用户大概率答错）。"
        )
    elif qtype == "判断题":
        user_prompt_extra = (
            "\n【题型识别】本题为判断题。"
            "guessed_user_answer 只能是 '正确' 或 '错误'。"
        )
    elif qtype == "填空题":
        user_prompt_extra = (
            "\n【题型识别】本题为填空题。"
            "guessed_user_answer 应直接给出关键答案（1-3 个字）。"
        )
    else:
        user_prompt_extra = (
            "\n【题型识别】本题可能为简答/应用题。"
            "guessed_user_answer 给出 1-2 句核心错误答案要点。"
        )

    try:
        from services.llm_service import chat_json
        result = chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是考研 408 OCR 错题分析 Agent，专注从题目文本反推用户的可能作答。\n"
                        "任务：基于 OCR 题目内容，**推测用户最可能的错误答案**（错题导入场景,默认用户答错）。\n"
                        "要求：\n"
                        "- 选择题只输出一个字母（A/B/C/D）\n"
                        "- 填空题给 1-3 字关键答案\n"
                        "- 简答题给 1-2 句核心错误答案要点\n"
                        "- 置信度(confidence)取值 0~1，根据题目信息完整度给出\n"
                        "- 只输出合法 JSON,无任何额外文字。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
OCR 识别的题目：{text[:1500]}
前端初步科目：{subject}
前端初步知识点：{knowledge_point}
{user_prompt_extra}

请输出：
{{
  "question_type": "再次确认题型({qtype})",
  "guessed_user_answer": "用户最可能的作答(选择题给单字母,填空给关键词,简答给核心要点)",
  "confidence": 0.85,
  "reasoning": "推断依据(基于题目考查方向与常见错答模式,如「用户对XXX概念理解不清,可能误选A」)"
}}
""",
                },
            ],
            fallback,
            temperature=0.2,
            max_tokens=600,
        )
        data = result.data if isinstance(result.data, dict) else fallback
        return {
            "guessed_user_answer": data.get("guessed_user_answer", ""),
            "confidence": float(data.get("confidence", 0.0) or 0.0),
            "question_type": data.get("question_type", qtype),
            "reasoning": data.get("reasoning", ""),
            "options": options,
            "llm_used": result.used_llm,
        }
    except Exception as exc:
        return {**fallback, "reasoning": f"反推用户答案异常: {exc}"}


def _detect_question_type(text: str) -> tuple[str, list[str]]:
    """启发式题型识别。

    Returns:
        (题型, 选项列表)
    """
    import re
    # 选项模式: A./A、/A. / A.  / A)
    option_re = re.compile(r"([A-E])[\.、\)\s]\s*([^\nA-E]{2,40})")
    options = []
    for m in option_re.finditer(text):
        letter = m.group(1)
        body = m.group(2).strip().rstrip("。,，;；")
        if body and len(body) < 60:
            options.append(f"{letter}.{body[:30]}")
    if options:
        return "选择题", options[:5]
    if "正确" in text and "错误" in text and len(text) < 200:
        return "判断题", []
    if "____" in text or "（    ）" in text or "______" in text:
        return "填空题", []
    if len(text) > 200:
        return "简答题", []
    return "未知", []


def _ocr_question_text_for_summary(error_reason: str) -> str:
    """从 mistake.error_reason 中抽取 OCR 题干,作为 question_summary 兜底。"""
    if not error_reason:
        return ""
    marker = "从图片识别到题目："
    if marker not in error_reason:
        return error_reason[:120]
    text = error_reason.split(marker, 1)[1]
    for stop in ("\n用户答案：", "\nAgent 推断标准答案：", "\n答案解析：", "\n错因分析："):
        if stop in text:
            text = text.split(stop, 1)[0]
    return text.strip()[:200]


def _extract_ocr_field(error_reason: str, key: str) -> str:
    """从 mistake.error_reason 中抽取 '\nkey：value' 字段。"""
    if not error_reason or not key:
        return ""
    needle = f"\n{key}："
    if needle not in error_reason:
        return ""
    tail = error_reason.split(needle, 1)[1]
    for stop in ("\n用户答案：", "\nAgent 推断标准答案：", "\n答案解析：", "\n错因分析：", "\n建议："):
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    return tail.strip()


def _extract_ocr_correct_answer(error_reason: str) -> str:
    return _extract_ocr_field(error_reason, "Agent 推断标准答案")


def _extract_ocr_explanation(error_reason: str) -> str:
    return _extract_ocr_field(error_reason, "答案解析")


def _extract_ocr_user_answer(error_reason: str) -> str:
    val = _extract_ocr_field(error_reason, "用户答案")
    if val == "未填写":
        return ""
    return val


def analyze_ocr_text(
    db: Session,
    user_id: int,
    text: str,
    subject: str,
    knowledge_point: str,
    user_answer: str = "",
    low_confidence_lines: list[str] | None = None,
) -> dict:
    """分析 OCR 识别文本，推断答案、生成错因并写入系统。

    Args:
        db: 数据库会话。
        user_id: 用户 ID。
        text: OCR 识别文本。
        subject: 科目。
        knowledge_point: 知识点。
        user_answer: 用户填写的答案。
        low_confidence_lines: 低置信度行,前端会做行级校对。

    Returns:
        dict: 包含 mistake_id, memory_id, analysis, llm_used, llm_error。
    """
    # 5 分钟内同源 OCR 文本视为重复提交:复用最近一条错题,避免「同图多次点提交」刷出多条记录
    from datetime import datetime, timedelta
    recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
    norm_text = (text or "").strip()
    if norm_text:
        recent = (
            db.query(Mistake)
            .filter(
                Mistake.user_id == user_id,
                Mistake.input_type == "PaddleOCR",
                Mistake.create_time >= recent_cutoff,
                Mistake.error_reason.like(f"从图片识别到题目：{norm_text[:80]}%"),
            )
            .order_by(Mistake.id.desc())
            .first()
        )
        if recent:
            return {
                "mistake_id": recent.id,
                "memory_id": None,
                "recognized_text": text,
                "subject": recent.subject,
                "knowledge_point": recent.knowledge_point,
                "question_summary": _ocr_question_text_for_summary(recent.error_reason or ""),
                "correct_answer": _extract_ocr_correct_answer(recent.error_reason or ""),
                "answer_explanation": _extract_ocr_explanation(recent.error_reason or ""),
                "is_correct": False,
                "error_type": recent.error_type,
                "error_reason": "检测到 5 分钟内已提交过相同 OCR 错题,直接复用。",
                "suggestion": recent.suggestion or "",
                "mastery_status": recent.mastery_status,
                "analysis": {
                    "subject": recent.subject,
                    "knowledge_point": recent.knowledge_point,
                    "question_summary": _ocr_question_text_for_summary(recent.error_reason or ""),
                    "user_answer": _extract_ocr_user_answer(recent.error_reason or ""),
                    "correct_answer": _extract_ocr_correct_answer(recent.error_reason or ""),
                    "answer_explanation": _extract_ocr_explanation(recent.error_reason or ""),
                    "is_correct": False,
                    "possible_causes": [],
                    "error_type": recent.error_type,
                    "error_reason": "5 分钟内重复提交,已复用上次错题。",
                    "suggestion": recent.suggestion or "",
                    "mastery_status": recent.mastery_status,
                },
                "message": "5 分钟内已提交过相同 OCR 错题,已复用上次结果。",
                "llm_used": False,
                "llm_model": "",
                "llm_error": "duplicate_recent_submission",
                "deduped": True,
            }

    fallback = {
        "subject": subject,
        "knowledge_point": knowledge_point,
        "question_summary": text[:120],
        "correct_answer": "AI 未能可靠推断标准答案，请根据题目条件人工校对。",
        "answer_explanation": "OCR 文本信息不足或大模型暂不可用，系统已先保存错题并等待后续校正。",
        "is_correct": False if user_answer else None,
        "possible_causes": ["审题错误", "知识点掌握不稳", "答案待校对"],
        "error_type": "OCR 导入待确认",
        "error_reason": "已导入 OCR 错题，标准答案由 Agent 推断失败或待人工校对。",
        "suggestion": "先校对 OCR 文本和自己的答案，再围绕该知识点完成同类训练。",
        "memory_content": f"OCR 导入错题涉及 {knowledge_point}，需要校对题干并复盘自己的作答过程。",
    }
    llm = chat_json_with_fallback_models(
        [
            {
                "role": "system",
                "content": (
                    "你是考研 408 OCR 错题分析 Agent。根据 OCR 题干和用户答案，"
                    "自行推断标准答案、判断用户是否答错、分析错因并生成复习建议。只输出合法 JSON。"
                ),
            },
            {
                "role": "user",
                "content": f"""
OCR 识别文本：{text}
前端初步科目：{subject}
前端初步知识点：{knowledge_point}
用户答案：{user_answer or "未填写"}
OCR 低置信度行（可能识别有误，请优先校对）：{chr(10).join(low_confidence_lines or []) or "(无)"}

请输出：
{{
  "subject": "可修正后的科目",
  "knowledge_point": "可修正后的知识点",
  "question_summary": "用一句话概括题目",
  "correct_answer": "你推断出的标准答案，含必要单位或选项",
  "answer_explanation": "推导或解析过程",
  "is_correct": false,
  "possible_causes": ["可能错因1", "可能错因2"],
  "error_type": "最主要错因类型",
  "error_reason": "结合用户答案和标准答案的具体错因分析",
  "suggestion": "可执行复习建议",
  "memory_content": "适合写入长期学习记忆的一句话"
}}
""",
            },
        ],
        fallback,
        models=[settings.siliconflow_model, "Qwen/Qwen2.5-14B-Instruct"],
    )
    data = llm.data or fallback
    resolved_subject = data.get("subject") or subject
    resolved_point = data.get("knowledge_point") or knowledge_point
    correct_answer = data.get("correct_answer") or fallback["correct_answer"]
    answer_explanation = data.get("answer_explanation") or fallback["answer_explanation"]
    possible_causes = data.get("possible_causes") or fallback["possible_causes"]
    error_type = data.get("error_type") or "OCR 导入待确认"
    error_reason = data.get("error_reason") or fallback["error_reason"]
    suggestion = data.get("suggestion") or fallback["suggestion"]
    memory_content = data.get("memory_content") or fallback["memory_content"]
    mistake = Mistake(
        user_id=user_id,
        subject=resolved_subject,
        knowledge_point=resolved_point,
        error_type=error_type,
        error_reason=(
            f"从图片识别到题目：{text[:300]}"
            f"\n用户答案：{user_answer or '未填写'}"
            f"\nAgent 推断标准答案：{correct_answer}"
            f"\n答案解析：{answer_explanation}"
            f"\n错因分析：{error_reason}"
        ),
        suggestion=suggestion,
        input_type="PaddleOCR",
        # OCR 导入的错题默认进「不会题本」,因为这是用户答错/未掌握的题
        # recalculate_mastery 后续会按答题记录把它升级为「薄弱点」或降级为「不熟」
        mastery_status="不会",
    )
    db.add(mistake)
    db.flush()
    memory = UserMemory(
        user_id=user_id,
        memory_type="weak_point",
        subject=resolved_subject,
        knowledge_point=resolved_point,
        content=memory_content,
        evidence=f"ocr_mistake:{mistake.id}",
    )
    db.add(memory)
    db.flush()

    upsert_document(
        "mistake_summary",
        f"ocr_mistake_{mistake.id}",
        f"[{resolved_subject}/{resolved_point}] OCR 错因：{error_type}。分析：{error_reason}。建议：{suggestion}",
        {
            "subject": resolved_subject,
            "knowledge_point": resolved_point,
            "error_type": error_type,
            "mistake_id": mistake.id,
            "source": "ocr",
        },
    )

    mastery = recalculate_mastery(db, user_id, resolved_subject, resolved_point)
    db.flush()
    analysis = {
        "subject": resolved_subject,
        "knowledge_point": resolved_point,
        "question_summary": data.get("question_summary") or fallback["question_summary"],
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "answer_explanation": answer_explanation,
        "is_correct": data.get("is_correct"),
        "possible_causes": possible_causes,
        "error_type": error_type,
        "error_reason": error_reason,
        "suggestion": mistake.suggestion,
        "mastery_status": mastery.final_status,
    }
    return {
        "mistake_id": mistake.id,
        "memory_id": memory.id,
        "recognized_text": text,
        "subject": resolved_subject,
        "knowledge_point": resolved_point,
        "question_summary": analysis["question_summary"],
        # correct_answer 兼容 dict(多空答案)与 str,统一转成可读字符串给前端展示
        "correct_answer": (
            "; ".join(f"{k}={v}" for k, v in (correct_answer or {}).items())
            if isinstance(correct_answer, dict)
            else (correct_answer or "")
        ),
        "answer_explanation": answer_explanation,
        "is_correct": data.get("is_correct"),
        "error_type": error_type,
        "error_reason": error_reason,
        "suggestion": mistake.suggestion,
        "mastery_status": mistake.mastery_status,
        "analysis": analysis,
        "message": "已提交错题分析 Agent，并写入错题、长期记忆和知识点掌握状态。",
        "llm_used": llm.used_llm,
        "llm_model": (llm.data or {}).get("_llm_model") if isinstance(llm.data, dict) else "",
        "llm_error": llm.error,
    }
