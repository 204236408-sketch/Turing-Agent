-- 003: create question_generation_session, question, favorite_question, answer_record
-- depends_on: 001

CREATE TABLE IF NOT EXISTS `question_generation_session` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `generation_mode` VARCHAR(32) DEFAULT 'manual',
  `recommend_mode` VARCHAR(64) DEFAULT '',
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `difficulty` VARCHAR(32) DEFAULT '中等',
  `question_type` VARCHAR(32) DEFAULT '选择题',
  `question_count` INTEGER DEFAULT 3,
  `reason` TEXT,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_session_uid` ON `question_generation_session` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_session_sub_kp` ON `question_generation_session` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_session_del` ON `question_generation_session` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `question` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `session_id` INTEGER NULL REFERENCES `question_generation_session`(`id`) ON DELETE SET NULL,
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `difficulty` VARCHAR(32) DEFAULT '中等',
  `question_type` VARCHAR(32) DEFAULT '选择题',
  `variant_type` VARCHAR(32) DEFAULT 'choice',
  `question_text` TEXT NOT NULL,
  `options_json` TEXT DEFAULT '[]',
  `sub_questions_json` TEXT DEFAULT '[]',
  `standard_answer` VARCHAR(64) DEFAULT '',
  `explanation` TEXT DEFAULT '',
  `hints_json` TEXT DEFAULT '[]',
  `recommend_reason` TEXT DEFAULT '',
  `source` VARCHAR(32) DEFAULT 'agent_mock',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_q_sub_kp` ON `question` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_q_session` ON `question` (`session_id`);
CREATE INDEX IF NOT EXISTS `idx_q_ctime` ON `question` (`create_time`);
CREATE INDEX IF NOT EXISTS `idx_q_del` ON `question` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `favorite_question` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `question_id` INTEGER NOT NULL REFERENCES `question`(`id`) ON DELETE CASCADE,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`user_id`, `question_id`)
);

CREATE INDEX IF NOT EXISTS `idx_fav_uid` ON `favorite_question` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_fav_del` ON `favorite_question` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `answer_record` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `user_id` INTEGER NOT NULL REFERENCES `user`(`id`) ON DELETE CASCADE,
  `question_id` INTEGER NOT NULL REFERENCES `question`(`id`) ON DELETE CASCADE,
  `subject` VARCHAR(64),
  `knowledge_point` VARCHAR(128),
  `user_answer` VARCHAR(128) DEFAULT '',
  `standard_answer` VARCHAR(128) DEFAULT '',
  `is_correct` TINYINT(1) DEFAULT 0,
  `feedback` TEXT DEFAULT '',
  `mastery_feedback` VARCHAR(32) DEFAULT '',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_ans_uid` ON `answer_record` (`user_id`);
CREATE INDEX IF NOT EXISTS `idx_ans_uid_ctime` ON `answer_record` (`user_id`, `create_time`);
CREATE INDEX IF NOT EXISTS `idx_ans_sub_kp` ON `answer_record` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_ans_del` ON `answer_record` (`is_deleted`);
