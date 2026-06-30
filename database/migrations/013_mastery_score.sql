-- 013_mastery_score.sql
-- 为 knowledge_mastery 增加 mastery_score（0~100 综合分），作为 final_status 的唯一判定源。
-- 配合 mastery_service 重构：综合分 = 唯一事实，状态由分数派生。
-- 同时增加 user_mark_at（标记时间戳）用于冷却判定。
-- 历史数据回填在 scripts/backfill_mastery_score.py 中执行。

ALTER TABLE knowledge_mastery ADD COLUMN mastery_score INTEGER DEFAULT 0;
ALTER TABLE knowledge_mastery ADD COLUMN user_mark_at DATETIME NULL;
ALTER TABLE knowledge_mastery ADD COLUMN recent_wrong_7d INTEGER DEFAULT 0;
ALTER TABLE knowledge_mastery ADD COLUMN recent_answer_7d INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_mastery_score ON knowledge_mastery (mastery_score);
