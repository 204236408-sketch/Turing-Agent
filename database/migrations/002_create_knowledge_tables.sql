-- 002: create subject, knowledge_point, knowledge_document
-- depends_on: 001

CREATE TABLE IF NOT EXISTS `subject` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` VARCHAR(64) NOT NULL UNIQUE,
  `description` TEXT DEFAULT '',
  `sort_order` INTEGER DEFAULT 0,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_subject_del` ON `subject` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `knowledge_point` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `subject_id` INTEGER NOT NULL REFERENCES `subject`(`id`) ON DELETE RESTRICT,
  `subject` VARCHAR(64) NOT NULL,
  `parent_id` INTEGER NULL REFERENCES `knowledge_point`(`id`) ON DELETE SET NULL,
  `parent_name` VARCHAR(128) DEFAULT '',
  `name` VARCHAR(128) NOT NULL,
  `section` VARCHAR(128) NOT NULL DEFAULT '',
  `level` INTEGER DEFAULT 1,
  `content` TEXT,
  `common_mistakes` TEXT,
  `keywords` TEXT,
  `is_high_frequency` TINYINT(1) DEFAULT 0,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`subject`, `name`, `section`)
);

CREATE INDEX IF NOT EXISTS `idx_kp_subject_id` ON `knowledge_point` (`subject_id`);
CREATE INDEX IF NOT EXISTS `idx_kp_parent_id` ON `knowledge_point` (`parent_id`);
CREATE INDEX IF NOT EXISTS `idx_kp_highfreq` ON `knowledge_point` (`is_high_frequency`);
CREATE INDEX IF NOT EXISTS `idx_kp_del` ON `knowledge_point` (`is_deleted`);

CREATE TABLE IF NOT EXISTS `knowledge_document` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `parent_name` VARCHAR(128) NOT NULL DEFAULT '',
  `name` VARCHAR(128) NOT NULL DEFAULT '',
  `section` VARCHAR(128) NOT NULL DEFAULT '',
  `knowledge_point` VARCHAR(128) NOT NULL,
  `file_path` VARCHAR(255) NOT NULL,
  `content` TEXT NOT NULL,
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `idx_doc_sub_name_sec` ON `knowledge_document` (`subject`, `name`, `section`);
CREATE INDEX IF NOT EXISTS `idx_doc_sub_kp` ON `knowledge_document` (`subject`, `knowledge_point`);
CREATE INDEX IF NOT EXISTS `idx_doc_del` ON `knowledge_document` (`is_deleted`);
