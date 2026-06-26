-- 006: create report, user_daily_activity, video_resource, video_crawl_log, user_pending_recommendation
-- depends_on: 001, 002

CREATE TABLE IF NOT EXISTS `report` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `title` VARCHAR(128) DEFAULT '学习报告',
  `report_type` VARCHAR(32) DEFAULT 'stage',
  `start_date` VARCHAR(10) DEFAULT '',
  `end_date` VARCHAR(10) DEFAULT '',
  `summary` TEXT DEFAULT '',
  `weak_points` TEXT DEFAULT '',
  `main_error_type` TEXT DEFAULT '',
  `qa_focus` TEXT DEFAULT '',
  `forum_focus` TEXT DEFAULT '',
  `video_suggestion` TEXT DEFAULT '',
  `plan_json` TEXT DEFAULT '[]',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_report_uid` ON `report` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_report_type` ON `report` (`report_type`);
CREATE INDEX IF NOT EXISTS `idx_report_del` ON `report` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `user_daily_activity` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `date` VARCHAR(10) NOT NULL,
  `answer_count` INTEGER DEFAULT 0,
  `forum_count` INTEGER DEFAULT 0,
  `video_count` INTEGER DEFAULT 0,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `date`)
);

CREATE INDEX IF NOT EXISTS `idx_daily_uid` ON `user_daily_activity` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_daily_date` ON `user_daily_activity` (`date`);

CREATE TABLE IF NOT EXISTS `video_resource` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `section` VARCHAR(128) DEFAULT '',
  `title` VARCHAR(180) NOT NULL,
  `platform` VARCHAR(64) DEFAULT 'Bilibili',
  `url` VARCHAR(255) DEFAULT '',
  `cover_url` VARCHAR(255) DEFAULT '',
  `duration` VARCHAR(32) DEFAULT '',
  `reason` TEXT DEFAULT '',
  `quality_score` INTEGER DEFAULT 0,
  `author` VARCHAR(128) DEFAULT '',
  `crawl_source` VARCHAR(16) DEFAULT 'seed',
  `is_deleted` TINYINT(1) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS `idx_video_sub_kp` ON `video_resource` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_video_del` ON `video_resource` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `video_crawl_log` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `section` VARCHAR(128) DEFAULT '',
  `url` VARCHAR(255) NULL UNIQUE,
  `platform` VARCHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `crawl_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `error_msg` TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS `idx_crawl_sub_kp` ON `video_crawl_log` (`subject`, `knowledge_point`, `section`);

CREATE TABLE IF NOT EXISTS `user_pending_recommendation` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `knowledge_point_id` INTEGER NOT NULL REFERENCES `knowledge_point`(`id`) ON DELETE CASCADE,
  `reason` TEXT DEFAULT '',
  `is_finish` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_rec_user` ON `user_pending_recommendation` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_rec_finish` ON `user_pending_recommendation` (`is_finish`);
