-- 004: create knowledge_mastery, mistake, user_memory
-- depends_on: 001, 003

CREATE TABLE IF NOT EXISTS `knowledge_mastery` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `final_status` VARCHAR(32) DEFAULT '未学',
  `total_answer_count` INTEGER DEFAULT 0,
  `correct_count` INTEGER DEFAULT 0,
  `wrong_count` INTEGER DEFAULT 0,
  `unfamiliar_count` INTEGER DEFAULT 0,
  `unknown_count` INTEGER DEFAULT 0,
  `mastered_count` INTEGER DEFAULT 0,
  `ocr_mistake_count` INTEGER DEFAULT 0,
  `qa_count` INTEGER DEFAULT 0,
  `forum_count` INTEGER DEFAULT 0,
  `user_mark_status` VARCHAR(32) DEFAULT '',
  `weak_score` FLOAT DEFAULT 0.0,
  `continuous_wrong_count` INTEGER DEFAULT 0,
  `last_answer_time` DATETIME NULL,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `subject`, `knowledge_point`)
);

CREATE INDEX IF NOT EXISTS `idx_mastery_uid` ON `knowledge_mastery` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_mastery_weak` ON `knowledge_mastery` (`weak_score`);

CREATE TABLE IF NOT EXISTS `mistake` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `answer_record_id` INTEGER NULL REFERENCES `answer_record`(`id`) ON DELETE SET NULL,
  `question_id` INTEGER NULL REFERENCES `question`(`id`) ON DELETE SET NULL,
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `error_type` VARCHAR(128) DEFAULT '',
  `error_reason` TEXT DEFAULT '',
  `suggestion` TEXT DEFAULT '',
  `mastery_status` VARCHAR(32) DEFAULT '',
  `input_type` VARCHAR(32) DEFAULT '系统出题',
  `status` VARCHAR(32) DEFAULT 'active',
  `is_reviewed` TINYINT(1) DEFAULT 0,
  `review_time` DATETIME NULL,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_mistake_uid` ON `mistake` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_mistake_sub_kp` ON `mistake` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_mistake_review` ON `mistake` (`is_reviewed`);
CREATE INDEX IF NOT EXISTS `idx_mistake_del` ON `mistake` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `user_memory` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `memory_type` VARCHAR(32) DEFAULT 'weak_point',
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `content` TEXT NOT NULL,
  `evidence` TEXT DEFAULT '',
  `status` VARCHAR(32) DEFAULT 'active',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_memory_uid` ON `user_memory` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_memory_del` ON `user_memory` (`is_deleted`);
