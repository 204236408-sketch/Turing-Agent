-- 007_video_recommendation_enhancement.sql
-- 视频推荐增强：VideoResource 字段 + VideoViewLog 表
-- 注意：SQLite 对 ALTER TABLE ADD COLUMN 不支持非常量 DEFAULT，使用空值默认值

-- VideoResource 增强字段（其他字段由之前的迁移添加，此处只补 create_time/update_time）
ALTER TABLE video_resource ADD COLUMN create_time DATETIME;
ALTER TABLE video_resource ADD COLUMN update_time DATETIME;

-- 索引增强
CREATE INDEX IF NOT EXISTS idx_video_active ON video_resource(is_active);
CREATE INDEX IF NOT EXISTS idx_video_url ON video_resource(url);

-- 视频点击日志表
CREATE TABLE IF NOT EXISTS video_view_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_id INTEGER,
    video_url VARCHAR(255) DEFAULT '',
    video_title VARCHAR(255) DEFAULT '',
    question_id INTEGER,
    subject VARCHAR(64) DEFAULT '',
    knowledge_point VARCHAR(128) DEFAULT '',
    author VARCHAR(128) DEFAULT '',
    click_position INTEGER DEFAULT 0,
    match_level VARCHAR(32) DEFAULT '',
    source VARCHAR(32) DEFAULT '',
    create_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vvl_user ON video_view_log(user_id);
CREATE INDEX IF NOT EXISTS idx_vvl_video ON video_view_log(video_id);
CREATE INDEX IF NOT EXISTS idx_vvl_url ON video_view_log(video_url);
CREATE INDEX IF NOT EXISTS idx_vvl_subject_kp ON video_view_log(subject, knowledge_point);
CREATE INDEX IF NOT EXISTS idx_vvl_ctime ON video_view_log(create_time);
