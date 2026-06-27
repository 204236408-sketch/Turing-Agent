from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Index, UniqueConstraint, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from database import Base

# -------------------------- 1. 用户表 User --------------------------
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(128), nullable=False, unique=True)
    username = Column(String(64), nullable=False, unique=True)
    nickname = Column(String(64), nullable=False, default="408 同学")
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(255), default="")
    status = Column(String(32), default="active")
    is_deleted = Column(Boolean, default=False)
    delete_time = Column(DateTime, nullable=True)
    create_ip = Column(String(64), default="")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    profile = relationship("UserProfile", back_populates="user", cascade="all, delete")
    __table_args__ = (
        Index("idx_user_status", "status"),
        Index("idx_user_isdel", "is_deleted"),
    )

# -------------------------- 2. 用户学习资料 UserProfile --------------------------
class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    target_exam = Column(String(64), default="考研 408")
    target_date = Column(String(32), default="2026-12-19")
    daily_minutes = Column(Integer, default=90)
    learning_stage = Column(String(32), default="强化")
    long_profile = Column(Text, default="")
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    __table_args__ = (
        Index("idx_user_profile_uid", "user_id"),
    )

# -------------------------- 3. 科目表 Subject --------------------------
class Subject(Base):
    __tablename__ = "subject"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kp_list = relationship("KnowledgePoint", back_populates="subject_ref")
    __table_args__ = (
        Index("idx_subject_del", "is_deleted"),
    )

# -------------------------- 4. 知识点表 KnowledgePoint --------------------------
class KnowledgePoint(Base):
    __tablename__ = "knowledge_point"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="RESTRICT"), nullable=False)
    subject = Column(String(64), nullable=False)
    parent_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="SET NULL"), nullable=True)
    parent_name = Column(String(128), default="")
    name = Column(String(128), nullable=False)
    section = Column(String(128), nullable=False, default="")
    level = Column(Integer, default=1)
    content = Column(Text)
    common_mistakes = Column(Text)
    keywords = Column(Text)
    is_high_frequency = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject_ref = relationship("Subject", back_populates="kp_list")
    parent = relationship("KnowledgePoint", remote_side=[id], back_populates="children")
    children = relationship("KnowledgePoint", back_populates="parent")
    __table_args__ = (
        UniqueConstraint("subject", "name", "section", name="uk_kp_sub_name_sec"),
        Index("idx_kp_subject_id", "subject_id"),
        Index("idx_kp_parent_id", "parent_id"),
        Index("idx_kp_highfreq", "is_high_frequency"),
        Index("idx_kp_del", "is_deleted"),
    )

# -------------------------- 5. AI出题会话 QuestionGenerationSession --------------------------
class QuestionGenerationSession(Base):
    __tablename__ = "question_generation_session"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    generation_mode = Column(String(32), default="manual")
    recommend_mode = Column(String(64), default="")
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    difficulty = Column(String(32), default="中等")
    question_type = Column(String(32), default="选择题")
    question_count = Column(Integer, default=3)
    reason = Column(Text)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_session_uid", "user_id"),
        Index("idx_session_sub_kp", "subject", "knowledge_point"),
        Index("idx_session_del", "is_deleted"),
    )

# -------------------------- 6. 题目表 Question --------------------------
class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("question_generation_session.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    difficulty = Column(String(32), default="中等")
    question_type = Column(String(32), default="选择题")
    variant_type = Column(String(32), default="choice")
    question_text = Column(Text, nullable=False)
    options_json = Column(JSON, default=[])
    sub_questions_json = Column(JSON, default=[])
    standard_answer = Column(String(64), default="")
    explanation = Column(Text, default="")
    hints_json = Column(JSON, default=[])
    recommend_reason = Column(Text, default="")
    source = Column(String(32), default="agent_mock")
    is_deleted = Column(Boolean, default=False)
    # 是否进入"参考题池"：种子题默认 1，LLM 生成题默认 0；阻断 LLM 幻觉在生成链路里循环放大
    is_verified = Column(Boolean, default=False)
    # 题目"易错点"：来自 prompt 的 easy_mistakes，存库与展示对齐
    easy_mistakes = Column(Text, default="")
    # 质量分（0-100）：种子题 100；LLM 生成题由答题正确率自动更新
    quality_score = Column(Integer, default=0)
    # 质量标记：normal / disputed / deprecated
    quality_flag = Column(String(32), default="normal")
    # 答题统计（冗余字段，避免每次 JOIN answer_record）
    answer_count = Column(Integer, default=0)
    correct_answer_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_q_sub_kp", "subject", "knowledge_point"),
        Index("idx_q_session", "session_id"),
        Index("idx_q_ctime", "create_time"),
        Index("idx_q_del", "is_deleted"),
        Index("idx_q_quality_score", "quality_score"),
        Index("idx_q_quality_flag", "quality_flag"),
    )

# -------------------------- 7. 用户收藏题目 FavoriteQuestion --------------------------
class FavoriteQuestion(Base):
    __tablename__ = "favorite_question"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uk_fav_uid_qid"),
        Index("idx_fav_uid", "user_id"),
        Index("idx_fav_del", "is_deleted"),
    )

# -------------------------- 8. 答题记录 AnswerRecord --------------------------
class AnswerRecord(Base):
    __tablename__ = "answer_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    user_answer = Column(String(128), default="")
    standard_answer = Column(String(128), default="")
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text, default="")
    mastery_feedback = Column(String(32), default="")
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ans_uid", "user_id"),
        Index("idx_ans_uid_ctime", "user_id", "create_time"),
        Index("idx_ans_sub_kp", "subject", "knowledge_point"),
        Index("idx_ans_del", "is_deleted"),
    )

# -------------------------- 9. 知识点掌握度 KnowledgeMastery --------------------------
class KnowledgeMastery(Base):
    __tablename__ = "knowledge_mastery"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    final_status = Column(String(32), default="未学")
    total_answer_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    unfamiliar_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)
    mastered_count = Column(Integer, default=0)
    ocr_mistake_count = Column(Integer, default=0)
    qa_count = Column(Integer, default=0)
    forum_count = Column(Integer, default=0)
    user_mark_status = Column(String(32), default="")
    weak_score = Column(Float, default=0.0)
    continuous_wrong_count = Column(Integer, default=0)
    last_answer_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "subject", "knowledge_point", name="uk_mastery_uid_sub_kp"),
        Index("idx_mastery_uid", "user_id"),
        Index("idx_mastery_weak", "weak_score"),
    )

# -------------------------- 10. 错题本 Mistake --------------------------
class Mistake(Base):
    __tablename__ = "mistake"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    answer_record_id = Column(Integer, ForeignKey("answer_record.id", ondelete="SET NULL"), nullable=True)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    error_type = Column(String(128), default="")
    error_reason = Column(Text, default="")
    suggestion = Column(Text, default="")
    mastery_status = Column(String(32), default="")
    input_type = Column(String(32), default="系统出题")
    status = Column(String(32), default="active")
    is_reviewed = Column(Boolean, default=False)
    review_time = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_mistake_uid", "user_id"),
        Index("idx_mistake_sub_kp", "subject", "knowledge_point"),
        Index("idx_mistake_review", "is_reviewed"),
        Index("idx_mistake_del", "is_deleted"),
    )

# -------------------------- 11. 用户记忆薄弱点 UserMemory --------------------------
class UserMemory(Base):
    __tablename__ = "user_memory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(32), default="weak_point")
    subject = Column(String(64))
    knowledge_point = Column(String(128))
    content = Column(Text, nullable=False)
    evidence = Column(Text, default="")
    status = Column(String(32), default="active")
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_memory_uid", "user_id"),
        Index("idx_memory_del", "is_deleted"),
    )

# -------------------------- 12. 问答会话 Conversation --------------------------
class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(128), default="408 问答")
    summary = Column(Text, default="")
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_conv_uid", "user_id"),
        Index("idx_conv_del", "is_deleted"),
    )

# -------------------------- 13. 会话消息 ConversationMessage --------------------------
class ConversationMessage(Base):
    __tablename__ = "conversation_message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_msg_conv", "conversation_id"),
        Index("idx_msg_conv_ctime", "conversation_id", "create_time"),
    )

# -------------------------- 14. 论坛分类 ForumCategory --------------------------
class ForumCategory(Base):
    __tablename__ = "forum_category"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_cat_del", "is_deleted"),
    )

# -------------------------- 15. 论坛主帖 ForumPost --------------------------
class ForumPost(Base):
    __tablename__ = "forum_post"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(64))
    subject = Column(String(64))
    knowledge_point = Column(String(128), default="")
    title = Column(String(180), nullable=False)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_top = Column(Boolean, default=False)
    status = Column(String(32), default="normal")
    is_deleted = Column(Boolean, default=False)
    create_ip = Column(String(64), default="")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_post_uid", "user_id"),
        Index("idx_post_cat", "category"),
        Index("idx_post_sub_kp", "subject", "knowledge_point"),
        Index("idx_post_top", "is_top"),
        Index("idx_post_del", "is_deleted"),
    )

# -------------------------- 16. 论坛评论 ForumComment --------------------------
class ForumComment(Base):
    __tablename__ = "forum_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("forum_post.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("forum_comment.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_comment_post", "post_id"),
        Index("idx_comment_parent", "parent_id"),
        Index("idx_comment_del", "is_deleted"),
    )

# -------------------------- 17. 论坛点赞 ForumLike --------------------------
class ForumLike(Base):
    __tablename__ = "forum_like"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(32), nullable=False)
    target_id = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uk_like_uid_target"),
        Index("idx_like_target", "target_type", "target_id"),
    )

# -------------------------- 18. 论坛收藏 ForumCollect --------------------------
class ForumCollect(Base):
    __tablename__ = "forum_collect"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("forum_post.id", ondelete="CASCADE"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uk_collect_uid_pid"),
        Index("idx_collect_uid", "user_id"),
        Index("idx_collect_del", "is_deleted"),
    )

# -------------------------- 19. 论坛签到 ForumCheckin --------------------------
class ForumCheckin(Base):
    __tablename__ = "forum_checkin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    checkin_date = Column(String(10), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="uk_checkin_uid_date"),
        Index("idx_checkin_uid", "user_id"),
    )

# -------------------------- 20. 视频资源 VideoResource --------------------------
class VideoResource(Base):
    __tablename__ = "video_resource"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(64), nullable=False)
    knowledge_point = Column(String(128), nullable=False)
    section = Column(String(128), default="")
    title = Column(String(180), nullable=False)
    platform = Column(String(64), default="Bilibili")
    url = Column(String(255), default="")
    cover_url = Column(String(255), default="")
    duration = Column(String(32), default="")
    reason = Column(Text, default="")
    description = Column(Text, default="")
    quality_score = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    author = Column(String(128), default="")
    crawl_source = Column(String(16), default="seed")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    last_verify_time = Column(DateTime, nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_video_sub_kp", "subject", "knowledge_point"),
        Index("idx_video_del", "is_deleted"),
        Index("idx_video_active", "is_active"),
        Index("idx_video_url", "url"),
    )

# -------------------------- 21. 视频爬取日志 VideoCrawlLog --------------------------
class VideoCrawlLog(Base):
    __tablename__ = "video_crawl_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(64), nullable=False)
    knowledge_point = Column(String(128), nullable=False)
    section = Column(String(128), default="")
    url = Column(String(255), nullable=True, unique=True)
    platform = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    crawl_time = Column(DateTime, default=datetime.utcnow)
    error_msg = Column(Text, default="")

    __table_args__ = (
        Index("idx_crawl_sub_kp", "subject", "knowledge_point", "section"),
    )

# -------------------------- 22. RAG知识库文档 KnowledgeDocument --------------------------
class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(64), nullable=False)
    parent_name = Column(String(128), nullable=False, default="")
    name = Column(String(128), nullable=False, default="")
    section = Column(String(128), nullable=False, default="")
    knowledge_point = Column(String(128), nullable=False)
    file_path = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_doc_sub_name_sec", "subject", "name", "section"),
        Index("idx_doc_sub_kp", "subject", "knowledge_point"),
        Index("idx_doc_del", "is_deleted"),
    )

# -------------------------- 23. 用户每日行为统计 UserDailyActivity --------------------------
class UserDailyActivity(Base):
    __tablename__ = "user_daily_activity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(10), nullable=False)
    answer_count = Column(Integer, default=0)
    forum_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uk_daily_uid_date"),
        Index("idx_daily_uid", "user_id"),
        Index("idx_daily_date", "date"),
    )

# -------------------------- 24. 个性化推荐待处理队列 UserPendingRecommendation --------------------------
class UserPendingRecommendation(Base):
    __tablename__ = "user_pending_recommendation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, default="")
    is_finish = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_rec_user", "user_id"),
        Index("idx_rec_finish", "is_finish"),
    )

# -------------------------- 25. 学习报告 Report --------------------------
class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(128), default="学习报告")
    report_type = Column(String(32), default="stage")
    start_date = Column(String(10), default="")
    end_date = Column(String(10), default="")
    summary = Column(Text, default="")
    weak_points = Column(Text, default="")
    main_error_type = Column(Text, default="")
    qa_focus = Column(Text, default="")
    forum_focus = Column(Text, default="")
    video_suggestion = Column(Text, default="")
    plan_json = Column(JSON, default=[])
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_report_uid", "user_id"),
        Index("idx_report_type", "report_type"),
        Index("idx_report_del", "is_deleted"),
    )

# -------------------------- 26. 视频点击日志 VideoViewLog --------------------------
class VideoViewLog(Base):
    """用户视频点击日志 - 用于个性化推荐加权"""
    __tablename__ = "video_view_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, nullable=True)  # 可能是本地或爬虫视频
    video_url = Column(String(255), default="")
    video_title = Column(String(255), default="")
    question_id = Column(Integer, nullable=True)
    subject = Column(String(64), default="")
    knowledge_point = Column(String(128), default="")
    author = Column(String(128), default="")
    click_position = Column(Integer, default=0)  # 在推荐列表中的位置
    match_level = Column(String(32), default="")  # exact/keyword/alias/subject
    source = Column(String(32), default="")  # local_seed/realtime_crawl
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_vvl_user", "user_id"),
        Index("idx_vvl_video", "video_id"),
        Index("idx_vvl_url", "video_url"),
        Index("idx_vvl_subject_kp", "subject", "knowledge_point"),
        Index("idx_vvl_ctime", "create_time"),
    )


# -------------------------- 27. 题目用户反馈 QuestionFeedback --------------------------
class QuestionFeedback(Base):
    """用户对题目质量的反馈，累 3 次 wrong_answer 自动触发质量分降级。"""
    __tablename__ = "question_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    feedback_type = Column(String(32), default="wrong_answer")  # wrong_answer / off_topic / typo / other
    content = Column(Text, default="")
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_qfb_qid", "question_id"),
        Index("idx_qfb_uid", "user_id"),
        Index("idx_qfb_del", "is_deleted"),
    )


# -------------------------- 28. 瀛︿範绗旇 Note --------------------------
class Note(Base):
    """用户绑定到章节/知识点的学习笔记。"""
    __tablename__ = "note"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="SET NULL"), nullable=True)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_point.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(64), default="")
    chapter = Column(String(128), default="")
    knowledge_point = Column(String(128), default="")
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_note_uid", "user_id"),
        Index("idx_note_kp_id", "knowledge_point_id"),
        Index("idx_note_scope", "subject", "chapter", "knowledge_point"),
        Index("idx_note_del", "is_deleted"),
    )


# -------------------------- 29. 绗旇鍒嗕韩 NoteShare --------------------------
class NoteShare(Base):
    """笔记分享卡片。"""
    __tablename__ = "note_share"
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("note.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    share_id = Column(String(64), nullable=False, unique=True)
    share_title = Column(String(100), default="")
    share_summary = Column(Text, default="")
    is_public = Column(Boolean, default=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_note_share_id", "share_id"),
        Index("idx_note_share_note", "note_id"),
        Index("idx_note_share_user", "user_id"),
    )

