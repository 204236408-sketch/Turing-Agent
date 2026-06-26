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


class OcrAnalyzeRequest(BaseModel):
    text: str
    subject: str = "操作系统"
    knowledge_point: str = "页面置换算法"
    user_answer: str = ""


class ForumPostRequest(BaseModel):
    category: str = "学习讨论"
    subject: str = "操作系统"
    knowledge_point: str = ""
    title: str
    content: str


class ForumCommentRequest(BaseModel):
    content: str
    parent_id: int | None = None


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
