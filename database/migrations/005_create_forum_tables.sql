-- 005: create forum tables (category, post, comment, like, collect, checkin)
-- depends_on: 001

CREATE TABLE IF NOT EXISTS `forum_category` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(64) NOT NULL UNIQUE,
  `description` TEXT DEFAULT '',
  `sort_order` INTEGER DEFAULT 0,
  `is_deleted` TINYINT(1) DEFAULT 0
);

CREATE INDEX IF NOT EXISTS `idx_cat_del` ON `forum_category` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `forum_post` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `category` VARCHAR(64),
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128) DEFAULT '',
  `title` VARCHAR(180) NOT NULL,
  `content` TEXT NOT NULL,
  `like_count` INTEGER DEFAULT 0,
  `collect_count` INTEGER DEFAULT 0,
  `comment_count` INTEGER DEFAULT 0,
  `is_top` TINYINT(1) DEFAULT 0,
  `status` VARCHAR(32) DEFAULT 'normal',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_ip` VARCHAR(64) DEFAULT '',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_post_uid` ON `forum_post` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_post_cat` ON `forum_post` (`category`);
CREATE INDEX IF NOT EXISTS `idx_post_sub_kp` ON `forum_post` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_post_top` ON `forum_post` (`is_top`);
CREATE INDEX IF NOT EXISTS `idx_post_del` ON `forum_post` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `forum_comment` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `post_id` INTEGER NOT NULL REFERENCES `forum_post`(`id`) ON DELETE CASCADE,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `parent_id` INTEGER NULL REFERENCES `forum_comment`(`id`) ON DELETE SET NULL,
  `content` TEXT NOT NULL,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_comment_post` ON `forum_comment` (`post_id`);
CREATE INDEX IF NOT EXISTS `idx_comment_parent` ON `forum_comment` (`parent_id`);
CREATE INDEX IF NOT EXISTS `idx_comment_del` ON `forum_comment` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `forum_like` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `target_type` VARCHAR(32) NOT NULL,
  `target_id` INTEGER NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `target_type`, `target_id`)
);

CREATE INDEX IF NOT EXISTS `idx_like_target` ON `forum_like` (`target_type`, `target_id`);

CREATE TABLE IF NOT EXISTS `forum_collect` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `post_id` INTEGER NOT NULL REFERENCES `forum_post`(`id`) ON DELETE CASCADE,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `post_id`)
);

CREATE INDEX IF NOT EXISTS `idx_collect_uid` ON `forum_collect` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_collect_del` ON `forum_collect` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `forum_checkin` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `checkin_date` VARCHAR(10) NOT NULL,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `checkin_date`)
);

CREATE INDEX IF NOT EXISTS `idx_checkin_uid` ON `forum_checkin` (`user_id`);
