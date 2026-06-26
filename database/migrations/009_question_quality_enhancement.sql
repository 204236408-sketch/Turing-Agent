-- 009_question_quality_enhancement.sql
-- 题目质量增强：新增字段 + 反馈表
-- 配合 P0-2（输出/存储对齐）、P2-8（质量分自动计算）、P2-10（反馈闭环）

-- 1. Question 表：题目"易错点"字段（对齐 prompt 输出的 easy_mistakes）
ALTER TABLE question ADD COLUMN easy_mistakes TEXT DEFAULT '';

-- 2. Question 表：质量分（0-100，由用户答题正确率自动更新）
ALTER TABLE question ADD COLUMN quality_score INTEGER DEFAULT 0;

-- 3. Question 表：质量标记
--    normal       - 正常
--    disputed     - 被用户反馈过"答案有误"
--    deprecated   - 已被自动下线（disputed 累计 >= 3 次）
ALTER TABLE question ADD COLUMN quality_flag VARCHAR(32) DEFAULT 'normal';

-- 4. Question 表：答题统计（参与 quality_score 计算，避免每次 JOIN 答卷表）
ALTER TABLE question ADD COLUMN answer_count INTEGER DEFAULT 0;
ALTER TABLE question ADD COLUMN correct_answer_count INTEGER DEFAULT 0;

-- 5. 索引：按 quality_score 排序拉参考题、按 quality_flag 筛选可疑题
CREATE INDEX IF NOT EXISTS idx_q_quality_score ON question (quality_score);
CREATE INDEX IF NOT EXISTS idx_q_quality_flag ON question (quality_flag);

-- 6. 用户反馈表：累积"答案有误"反馈，触发质量分降级
CREATE TABLE IF NOT EXISTS question_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    feedback_type VARCHAR(32) DEFAULT 'wrong_answer',  -- wrong_answer / off_topic / typo / other
    content TEXT DEFAULT '',
    is_deleted TINYINT(1) DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES question(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_qfb_qid ON question_feedback (question_id);
CREATE INDEX IF NOT EXISTS idx_qfb_uid ON question_feedback (user_id);
CREATE INDEX IF NOT EXISTS idx_qfb_del ON question_feedback (is_deleted);

-- 7. 用现有数据初始化 quality_score 和计数
--    规则：被答对过 = +20，答错过 = -5（封顶 0~100 区间）
UPDATE question
SET answer_count = COALESCE((
        SELECT COUNT(*) FROM answer_record
        WHERE answer_record.question_id = question.id
          AND answer_record.is_deleted = 0
    ), 0),
    correct_answer_count = COALESCE((
        SELECT COUNT(*) FROM answer_record
        WHERE answer_record.question_id = question.id
          AND answer_record.is_deleted = 0
          AND answer_record.is_correct = 1
    ), 0),
    quality_score = CASE
        WHEN source = 'seed' THEN 100  -- 种子题默认满分
        ELSE 0
    END;
