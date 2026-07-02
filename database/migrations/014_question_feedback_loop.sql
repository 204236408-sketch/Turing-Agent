-- 014_question_feedback_loop.sql
-- 出题质量反馈闭环：
-- 1) question 表新增 reported_count / reported_reason / last_reported_at
--    供前端展示反馈数徽标，并供 retrieve_question_context 过滤"被多用户标错"的题。
-- 2) answer_record 表新增 practice_only：loose 模式 / unverified 题的答题结果
--    仅作练习记录，不计入掌握度统计。

ALTER TABLE question ADD COLUMN reported_count INTEGER DEFAULT 0;
ALTER TABLE question ADD COLUMN reported_reason VARCHAR(255) DEFAULT '';
ALTER TABLE question ADD COLUMN last_reported_at DATETIME NULL;

ALTER TABLE answer_record ADD COLUMN practice_only TINYINT(1) DEFAULT 0;
