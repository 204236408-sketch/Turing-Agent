from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


def now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64), default="408 同学")
    password_hash: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    profile = relationship("UserProfile", back_populates="user", uselist=False)


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    target_exam: Mapped[str] = mapped_column(String(64), default="考研 408")
    target_date: Mapped[str] = mapped_column(String(32), default="2026-12-19")
    daily_minutes: Mapped[int] = mapped_column(Integer, default=90)
    learning_stage: Mapped[str] = mapped_column(String(64), default="强化复习")
    long_profile: Mapped[str] = mapped_column(Text, default="")

    user = relationship("User", back_populates="profile")


class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class KnowledgePoint(Base):
    __tablename__ = "knowledge_point"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    parent_name: Mapped[str] = mapped_column(String(128), default="")
    level: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, default="")
    common_mistakes: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    is_high_frequency: Mapped[bool] = mapped_column(Boolean, default=False)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class QuestionGenerationSession(Base):
    __tablename__ = "question_generation_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    generation_mode: Mapped[str] = mapped_column(String(64), default="manual")
    recommend_mode: Mapped[str] = mapped_column(String(64), default="")
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    difficulty: Mapped[str] = mapped_column(String(32), default="中等")
    question_type: Mapped[str] = mapped_column(String(32), default="选择题")
    question_count: Mapped[int] = mapped_column(Integer, default=3)
    reason: Mapped[str] = mapped_column(Text, default="")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)

    questions = relationship("Question", back_populates="session")


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("question_generation_session.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    difficulty: Mapped[str] = mapped_column(String(32), default="中等")
    question_type: Mapped[str] = mapped_column(String(32), default="选择题")
    variant_type: Mapped[str] = mapped_column(String(32), default="choice")
    question_text: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    sub_questions_json: Mapped[str] = mapped_column(Text, default="[]")
    standard_answer: Mapped[str] = mapped_column(String(64), default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    hints_json: Mapped[str] = mapped_column(Text, default="[]")
    recommend_reason: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(64), default="agent_mock")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)

    session = relationship("QuestionGenerationSession", back_populates="questions")


class AnswerRecord(Base):
    __tablename__ = "answer_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    user_answer: Mapped[str] = mapped_column(String(128), default="")
    standard_answer: Mapped[str] = mapped_column(String(128), default="")
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[str] = mapped_column(Text, default="")
    mastery_feedback: Mapped[str] = mapped_column(String(32), default="")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)


class KnowledgeMastery(Base):
    __tablename__ = "knowledge_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    final_status: Mapped[str] = mapped_column(String(32), default="未学")
    total_answer_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    unfamiliar_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    mastered_count: Mapped[int] = mapped_column(Integer, default=0)
    ocr_mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    qa_count: Mapped[int] = mapped_column(Integer, default=0)
    forum_count: Mapped[int] = mapped_column(Integer, default=0)
    user_mark_status: Mapped[str] = mapped_column(String(32), default="")
    weak_score: Mapped[float] = mapped_column(Float, default=0)
    continuous_wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    last_answer_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Mistake(Base):
    __tablename__ = "mistake"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    answer_record_id: Mapped[int | None] = mapped_column(ForeignKey("answer_record.id"), nullable=True)
    question_id: Mapped[int | None] = mapped_column(ForeignKey("question.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    error_type: Mapped[str] = mapped_column(String(128), default="")
    error_reason: Mapped[str] = mapped_column(Text, default="")
    suggestion: Mapped[str] = mapped_column(Text, default="")
    input_type: Mapped[str] = mapped_column(String(64), default="系统出题")
    status: Mapped[str] = mapped_column(String(32), default="active")
    mastery_status: Mapped[str] = mapped_column(String(32), default="")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)


class UserMemory(Base):
    __tablename__ = "user_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    memory_type: Mapped[str] = mapped_column(String(64), default="weak_point")
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    content: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(128), default="408 问答")
    summary: Mapped[str] = mapped_column(Text, default="")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ConversationMessage(Base):
    __tablename__ = "conversation_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)


class ForumCategory(Base):
    __tablename__ = "forum_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ForumPost(Base):
    __tablename__ = "forum_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), default="")
    title: Mapped[str] = mapped_column(String(180))
    content: Mapped[str] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    is_top: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="normal")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ForumComment(Base):
    __tablename__ = "forum_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_post.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)


class ForumCheckin(Base):
    __tablename__ = "forum_checkin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    checkin_date: Mapped[str] = mapped_column(String(10), index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)


class VideoResource(Base):
    __tablename__ = "video_resource"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(180))
    platform: Mapped[str] = mapped_column(String(64), default="Bilibili")
    url: Mapped[str] = mapped_column(String(255), default="")
    reason: Mapped[str] = mapped_column(Text, default="")


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(128), default="学习报告")
    summary: Mapped[str] = mapped_column(Text, default="")
    weak_points: Mapped[str] = mapped_column(Text, default="")
    main_error_type: Mapped[str] = mapped_column(Text, default="")
    qa_focus: Mapped[str] = mapped_column(Text, default="")
    forum_focus: Mapped[str] = mapped_column(Text, default="")
    video_suggestion: Mapped[str] = mapped_column(Text, default="")
    plan_json: Mapped[str] = mapped_column(Text, default="[]")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now)
