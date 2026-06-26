-- 001: create user & user_profile
-- depends_on: nil

CREATE TABLE IF NOT EXISTS `user` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `email` VARCHAR(128) NOT NULL UNIQUE,
  `username` VARCHAR(64) NOT NULL UNIQUE,
  `nickname` VARCHAR(64) NOT NULL DEFAULT '408 同学',
  `password_hash` VARCHAR(255) NOT NULL,
  `avatar_url` VARCHAR(255) DEFAULT '',
  `status` VARCHAR(32) DEFAULT 'active',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `delete_time` DATETIME NULL,
  `create_ip` VARCHAR(64) DEFAULT '',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_user_status` ON `user` (`status`);
CREATE INDEX IF NOT EXISTS `idx_user_isdel` ON `user` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `user_profile` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `target_exam` VARCHAR(64) DEFAULT '考研 408',
  `target_date` VARCHAR(32) DEFAULT '2026-12-19',
  `daily_minutes` INTEGER DEFAULT 90,
  `learning_stage` VARCHAR(32) DEFAULT '强化',
  `long_profile` TEXT DEFAULT '',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_user_profile_uid` ON `user_profile` (`user_id`);
