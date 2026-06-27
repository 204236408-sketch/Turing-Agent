-- 011_forum_ai_enhancement.sql
-- 论坛 AI 小助手完善（P2）所需的表结构
-- 包含：
--   1) forum_ai_answer       — AI 回答持久化与缓存
--   2) forum_ai_answer_like  — AI 回答点赞/采纳
--   3) forum_ai_followup     — AI 追问历史

-- 1. 论坛 AI 回答表（缓存 + 历史）
CREATE TABLE IF NOT EXISTS forum_ai_answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    subject VARCHAR(64) DEFAULT '',
    knowledge_point VARCHAR(128) DEFAULT '',
    structured_json TEXT NOT NULL,           -- 完整结构化 JSON
    analysis TEXT DEFAULT '',
    easy_trap TEXT DEFAULT '',
    extend_exercise TEXT DEFAULT '',
    review_plan TEXT DEFAULT '',
    recommend_questions TEXT DEFAULT '',
    recommend_video VARCHAR(512) DEFAULT '',
    memory_tip TEXT DEFAULT '',
    need_follow_up BOOLEAN DEFAULT 0,
    sources_json TEXT DEFAULT '[]',          -- 引用证据
    retrieval_confidence VARCHAR(32) DEFAULT 'unknown',
    agent_steps_json TEXT DEFAULT '[]',      -- Agent 思维链
    llm_used BOOLEAN DEFAULT 0,
    llm_error VARCHAR(512) DEFAULT '',
    is_active BOOLEAN DEFAULT 1,             -- 当前激活的版本（同一 post 多次请求会保留多版本，取最新）
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_ans_post ON forum_ai_answer(post_id);
CREATE INDEX IF NOT EXISTS idx_ai_ans_user ON forum_ai_answer(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_ans_sub_kp ON forum_ai_answer(subject, knowledge_point);
CREATE INDEX IF NOT EXISTS idx_ai_ans_active ON forum_ai_answer(is_active, post_id, create_time);
CREATE UNIQUE INDEX IF NOT EXISTS uk_ai_ans_post_active ON forum_ai_answer(post_id, is_active) WHERE is_active = 1;

-- 2. AI 回答点赞/采纳表
CREATE TABLE IF NOT EXISTS forum_ai_answer_like (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    answer_id INTEGER NOT NULL,
    is_helpful BOOLEAN NOT NULL,              -- 1=有用 0=不准确
    feedback VARCHAR(512) DEFAULT '',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, answer_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_like_ans ON forum_ai_answer_like(answer_id);
CREATE INDEX IF NOT EXISTS idx_ai_like_user ON forum_ai_answer_like(user_id);

-- 3. AI 追问历史表（用于上下文累积与多轮对话）
CREATE TABLE IF NOT EXISTS forum_ai_followup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    answer_id INTEGER DEFAULT NULL,           -- 关联的初始 AI 回答
    role VARCHAR(16) NOT NULL,                -- 'user' / 'assistant'
    content TEXT NOT NULL,
    structured_json TEXT DEFAULT '{}',
    parent_id INTEGER DEFAULT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_followup_post ON forum_ai_followup(post_id, create_time);
CREATE INDEX IF NOT EXISTS idx_followup_user ON forum_ai_followup(user_id);
CREATE INDEX IF NOT EXISTS idx_followup_ans ON forum_ai_followup(answer_id);
