-- 012_video_kp_keywords.sql
-- 为视频-KP 语义匹配添加 LLM 离线关键词字段
-- 视频端字段：video_resource.keywords（TEXT，JSON 数组字符串）
-- 知识点端：knowledge_point.keywords 字段已存在，复用，存 JSON 数组字符串

ALTER TABLE video_resource ADD COLUMN keywords TEXT DEFAULT '';
