-- 008_question_is_verified.sql
-- 题目质量门：增加 is_verified 字段，阻断 LLM 自噬链路
-- 背景：retrieve_question_context 原本会把 source='llm' 的题作为"参考示例"喂给下一轮 LLM，
--       如果这些题含幻觉/错误答案，会在生成链路里循环放大。
-- 方案：只允许 is_verified=1 的题进入参考池；种子题默认 1，LLM 生成题默认 0。

-- 1. 加字段（SQLite ADD COLUMN 不支持非常量 DEFAULT，使用 0 作为默认值）
ALTER TABLE question ADD COLUMN is_verified INTEGER DEFAULT 0;

-- 2. 加索引，方便按 (subject, knowledge_point, is_verified, is_deleted) 检索参考题
CREATE INDEX IF NOT EXISTS idx_q_sub_kp_verified ON question (subject, knowledge_point, is_verified, is_deleted);

-- 3. 清理历史 source='agent'（旧版本命名，与 agent_fallback 等价）
UPDATE question SET source = 'agent_fallback' WHERE source = 'agent';

-- 4. 种子题天然权威，自动置为已验证
UPDATE question SET is_verified = 1 WHERE source = 'seed';
