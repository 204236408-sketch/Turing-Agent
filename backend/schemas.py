from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str = Field(min_length=6)
    nickname: str = ""


class LoginRequest(BaseModel):
    account: str = "demo@turing408.ai"
    password: str = "123456"


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = None
    daily_minutes: int | None = None
    learning_stage: str | None = None
    target_date: str | None = None


class QaChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class QuestionGenerateRequest(BaseModel):
    mode: str = "自由选择"
    subject: str = "操作系统"
    knowledge_point: str = "页面置换算法"
    scope: str = ""  # point / chapter；为空时后端按 mode 和知识点表自动推断
    chapter: str = ""
    chapter_id: int | None = None
    difficulty: str = "中等"
    question_type: str = "选择题"
    count: int = Field(default=3, ge=1, le=10)
    # OCR 错题场景下携带：原图识别文本 + Agent 推断的标准答案
    # 用于让 LLM 出"与错题同考点/同结构"的同类题（避免凭空出题）
    reference_text: str = ""
    reference_answer: str = ""
    source: str = "manual"  # manual / ocr / smart / weak_kp

    @field_validator("subject")
    @classmethod
    def normalize_subject(cls, value: str) -> str:
        mapping = {
            "计组": "计算机组成原理",
            "组成原理": "计算机组成原理",
            "操作系统原理": "操作系统",
            "网络": "计算机网络",
            "数据结构与算法": "数据结构",
        }
        text = (value or "").strip()
        return mapping.get(text, text or "操作系统")

    @field_validator("difficulty")
    @classmethod
    def normalize_difficulty(cls, value: str) -> str:
        mapping = {
            "容易": "简单",
            "基础": "简单",
            "普通": "中等",
            "一般": "中等",
            "偏难": "较难",
            "真题难度": "较难",
            "困难": "困难",
            "混合": "自适应",
            "自适应": "自适应",
        }
        text = (value or "").strip()
        return mapping.get(text, text if text in {"简单", "中等", "较难", "困难", "自适应"} else "中等")

    @field_validator("question_type")
    @classmethod
    def normalize_question_type(cls, value: str) -> str:
        mapping = {
            "单选题": "选择题",
            "选择": "选择题",
            "choice": "选择题",
            "填空": "填空题",
            "fill": "填空题",
            "简答": "简答题",
            "问答题": "简答题",
            "essay": "简答题",
            "大题": "综合题",
            "综合": "综合题",
            "comprehensive": "综合题",
            "mixed": "混合",
            "随机": "混合",
        }
        text = (value or "").strip()
        normalized = mapping.get(text, text)
        return normalized if normalized in {"选择题", "填空题", "简答题", "综合题", "混合"} else "选择题"


class SmartQuestionGenerateRequest(BaseModel):
    recommend_mode: str = "薄弱点强化"
    count: int = Field(default=3, ge=1, le=20)


class AnswerCheckRequest(BaseModel):
    question_id: int
    user_answer: str


class CauseConfirmRequest(BaseModel):
    answer_record_id: int
    error_types: list[str] = Field(default_factory=list)
    user_note: str = ""
    agent_suggested_types: list[str] = Field(default_factory=list)
    evidence_source: str = "user_confirmed"


class MasteryFeedbackRequest(BaseModel):
    subject: str = ""
    knowledge_point: str = ""
    status: str
    mistake_id: int | None = None
    question_id: int | None = None


class QuestionFeedbackRequest(BaseModel):
    """用户对题目质量的反馈（答案有误 / 偏题 / 错别字 等）。"""
    question_id: int
    feedback_type: str = "wrong_answer"  # wrong_answer / off_topic / typo / other
    content: str = ""


class OcrAnalyzeRequest(BaseModel):
    text: str
    subject: str = "操作系统"
    knowledge_point: str = "页面置换算法"
    user_answer: str = ""
    low_confidence_lines: list[str] = []


class OcrGuessUserAnswerRequest(BaseModel):
    text: str
    subject: str = "操作系统"
    knowledge_point: str = "页面置换算法"


class ForumPostRequest(BaseModel):
    category: str = "学习讨论"
    subject: str = "操作系统"
    knowledge_point: str = ""
    title: str
    content: str


class ForumCommentRequest(BaseModel):
    content: str
    parent_id: int | None = None


class ForumAiFeedbackRequest(BaseModel):
    """AI 回答点赞/采纳反馈（P2-12）"""
    answer_id: int
    is_helpful: bool = True
    feedback: str = ""


class MemoryUpdateRequest(BaseModel):
    memory_type: str = "weak_point"
    subject: str
    knowledge_point: str
    content: str
    evidence: str = ""


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class RetrainRequest(BaseModel):
    mistake_id: int
