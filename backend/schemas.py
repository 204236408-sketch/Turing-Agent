from pydantic import BaseModel, Field


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
    difficulty: str = "中等"
    question_type: str = "选择题"
    count: int = Field(default=3, ge=1, le=10)
    # OCR 错题场景下携带：原图识别文本 + Agent 推断的标准答案
    # 用于让 LLM 出"与错题同考点/同结构"的同类题（避免凭空出题）
    reference_text: str = ""
    reference_answer: str = ""
    source: str = "manual"  # manual / ocr / smart / weak_kp


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
