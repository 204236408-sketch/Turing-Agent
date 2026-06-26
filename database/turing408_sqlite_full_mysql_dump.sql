-- Full MySQL-compatible dump generated from backend/turing408.db
-- Generated at: 2026-06-26 19:47:13
-- Note: SQLite internal table sqlite_sequence is converted into ALTER TABLE AUTO_INCREMENT statements.
CREATE DATABASE IF NOT EXISTS `yantu408` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `yantu408`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";

-- Tables included: answer_record, conversation, conversation_message, favorite_question, forum_category, forum_checkin, forum_collect, forum_comment, forum_like, forum_post, knowledge_document, knowledge_mastery, knowledge_point, mistake, question, question_generation_session, report, schema_migrations, subject, user, user_daily_activity, user_memory, user_pending_recommendation, user_profile, video_crawl_log, video_resource

-- ------------------------------------------------------------
-- Table structure for `answer_record`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `answer_record`;
CREATE TABLE `answer_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `question_id` BIGINT NOT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `user_answer` VARCHAR(128) NOT NULL,
  `standard_answer` VARCHAR(128) NOT NULL,
  `is_correct` TINYINT(1) NOT NULL,
  `feedback` LONGTEXT NOT NULL,
  `mastery_feedback` VARCHAR(32) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  `update_time` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_answer_record_user_id` (`user_id`),
  KEY `ix_answer_record_subject` (`subject`),
  KEY `ix_answer_record_question_id` (`question_id`),
  KEY `ix_answer_record_knowledge_point` (`knowledge_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `conversation`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `conversation`;
CREATE TABLE `conversation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `title` VARCHAR(128) NOT NULL,
  `summary` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `update_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_conversation_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `conversation_message`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `conversation_message`;
CREATE TABLE `conversation_message` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `conversation_id` BIGINT NOT NULL,
  `role` VARCHAR(32) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_conversation_message_conversation_id` (`conversation_id`),
  KEY `idx_msg_conv_ctime` (`conversation_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `favorite_question`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `favorite_question`;
CREATE TABLE `favorite_question` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `question_id` BIGINT NOT NULL,
  `is_deleted` TINYINT(1) NULL,
  `create_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_fav_uid` (`user_id`),
  KEY `idx_fav_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_category`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_category`;
CREATE TABLE `forum_category` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `sort_order` BIGINT NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_checkin`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_checkin`;
CREATE TABLE `forum_checkin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `checkin_date` VARCHAR(10) NOT NULL,
  `create_time` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_forum_checkin_checkin_date` (`checkin_date`),
  KEY `ix_forum_checkin_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_collect`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_collect`;
CREATE TABLE `forum_collect` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `post_id` BIGINT NOT NULL,
  `is_deleted` TINYINT(1) NULL,
  `create_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_collect_del` (`is_deleted`),
  KEY `idx_collect_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_comment`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_comment`;
CREATE TABLE `forum_comment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `post_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `parent_id` BIGINT NULL,
  `content` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_forum_comment_post_id` (`post_id`),
  KEY `ix_forum_comment_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_like`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_like`;
CREATE TABLE `forum_like` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `target_type` VARCHAR(7) NOT NULL,
  `target_id` BIGINT NOT NULL,
  `create_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_like_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `forum_post`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `forum_post`;
CREATE TABLE `forum_post` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `category` VARCHAR(64) NOT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `title` VARCHAR(180) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `like_count` BIGINT NOT NULL,
  `collect_count` BIGINT NOT NULL,
  `comment_count` BIGINT NOT NULL,
  `is_top` TINYINT(1) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `update_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  `create_ip` VARCHAR(64) NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `ix_forum_post_category` (`category`),
  KEY `ix_forum_post_user_id` (`user_id`),
  KEY `ix_forum_post_subject` (`subject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `knowledge_document`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `knowledge_document`;
CREATE TABLE `knowledge_document` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `parent_name` VARCHAR(128) NOT NULL,
  `name` VARCHAR(128) NOT NULL,
  `section` VARCHAR(128) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `file_path` VARCHAR(255) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `is_deleted` TINYINT(1) NULL,
  `create_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_doc_sub_kp` (`subject`, `knowledge_point`),
  KEY `idx_doc_del` (`is_deleted`),
  KEY `idx_doc_sub_name_sec` (`subject`, `name`, `section`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `knowledge_mastery`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `knowledge_mastery`;
CREATE TABLE `knowledge_mastery` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `final_status` VARCHAR(32) NOT NULL,
  `total_answer_count` BIGINT NOT NULL,
  `correct_count` BIGINT NOT NULL,
  `wrong_count` BIGINT NOT NULL,
  `unfamiliar_count` BIGINT NOT NULL,
  `unknown_count` BIGINT NOT NULL,
  `ocr_mistake_count` BIGINT NOT NULL,
  `qa_count` BIGINT NOT NULL,
  `forum_count` BIGINT NOT NULL,
  `weak_score` DOUBLE NOT NULL,
  `update_time` DATETIME NOT NULL,
  `mastered_count` BIGINT NULL DEFAULT 0,
  `user_mark_status` VARCHAR(32) NULL DEFAULT '',
  `continuous_wrong_count` BIGINT NULL DEFAULT 0,
  `last_answer_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `ix_knowledge_mastery_knowledge_point` (`knowledge_point`),
  KEY `ix_knowledge_mastery_subject` (`subject`),
  KEY `ix_knowledge_mastery_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `knowledge_point`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `knowledge_point`;
CREATE TABLE `knowledge_point` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `name` VARCHAR(128) NOT NULL,
  `parent_name` VARCHAR(128) NOT NULL,
  `level` BIGINT NOT NULL,
  `content` LONGTEXT NOT NULL,
  `common_mistakes` LONGTEXT NOT NULL,
  `keywords` LONGTEXT NOT NULL,
  `is_high_frequency` TINYINT(1) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `update_time` DATETIME NOT NULL,
  `subject_id` BIGINT NULL,
  `parent_id` BIGINT NULL,
  `section` VARCHAR(128) NULL DEFAULT '',
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_knowledge_point_subject` (`subject`),
  KEY `ix_knowledge_point_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `mistake`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `mistake`;
CREATE TABLE `mistake` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `answer_record_id` BIGINT NULL,
  `question_id` BIGINT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `error_type` VARCHAR(128) NOT NULL,
  `error_reason` LONGTEXT NOT NULL,
  `suggestion` LONGTEXT NOT NULL,
  `input_type` VARCHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `mastery_status` VARCHAR(32) NULL DEFAULT '',
  `is_reviewed` TINYINT(1) NULL DEFAULT 0,
  `review_time` DATETIME NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_mistake_subject` (`subject`),
  KEY `ix_mistake_user_id` (`user_id`),
  KEY `ix_mistake_knowledge_point` (`knowledge_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `question`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `question`;
CREATE TABLE `question` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `session_id` BIGINT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `difficulty` VARCHAR(32) NOT NULL,
  `question_type` VARCHAR(32) NOT NULL,
  `question_text` LONGTEXT NOT NULL,
  `options_json` LONGTEXT NOT NULL,
  `standard_answer` VARCHAR(64) NOT NULL,
  `explanation` LONGTEXT NOT NULL,
  `hints_json` LONGTEXT NOT NULL,
  `recommend_reason` LONGTEXT NOT NULL,
  `source` VARCHAR(64) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `variant_type` VARCHAR(32) NULL DEFAULT 'choice',
  `sub_questions_json` LONGTEXT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_question_knowledge_point` (`knowledge_point`),
  KEY `ix_question_subject` (`subject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `question_generation_session`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `question_generation_session`;
CREATE TABLE `question_generation_session` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `generation_mode` VARCHAR(64) NOT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `difficulty` VARCHAR(32) NOT NULL,
  `question_type` VARCHAR(32) NOT NULL,
  `question_count` BIGINT NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `recommend_mode` VARCHAR(64) NULL DEFAULT '',
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_question_generation_session_user_id` (`user_id`),
  KEY `ix_question_generation_session_subject` (`subject`),
  KEY `ix_question_generation_session_knowledge_point` (`knowledge_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `report`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `report`;
CREATE TABLE `report` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `title` VARCHAR(128) NOT NULL,
  `summary` LONGTEXT NOT NULL,
  `weak_points` LONGTEXT NOT NULL,
  `main_error_type` LONGTEXT NOT NULL,
  `qa_focus` LONGTEXT NOT NULL,
  `forum_focus` LONGTEXT NOT NULL,
  `video_suggestion` LONGTEXT NOT NULL,
  `plan_json` LONGTEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `report_type` VARCHAR(7) NULL DEFAULT 'stage',
  `start_date` VARCHAR(10) NULL DEFAULT '',
  `end_date` VARCHAR(10) NULL DEFAULT '',
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_report_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `schema_migrations`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `schema_migrations`;
CREATE TABLE `schema_migrations` (
  `version` LONGTEXT NULL,
  `name` LONGTEXT NOT NULL,
  `checksum` LONGTEXT NOT NULL,
  `applied_at` LONGTEXT NOT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `subject`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `subject`;
CREATE TABLE `subject` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `sort_order` BIGINT NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  `create_time` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_subject_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `user`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(128) NOT NULL,
  `username` VARCHAR(64) NOT NULL,
  `nickname` VARCHAR(64) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `avatar_url` VARCHAR(255) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `update_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  `delete_time` DATETIME NULL,
  `create_ip` VARCHAR(64) NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_user_username` (`username`),
  UNIQUE KEY `ix_user_email` (`email`),
  KEY `ix_user_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `user_daily_activity`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user_daily_activity`;
CREATE TABLE `user_daily_activity` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `date` VARCHAR(10) NOT NULL,
  `answer_count` BIGINT NULL,
  `forum_count` BIGINT NULL,
  `video_count` BIGINT NULL,
  `update_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_daily_uid_date` (`user_id`, `date`),
  KEY `idx_daily_uid` (`user_id`),
  KEY `idx_daily_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `user_memory`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user_memory`;
CREATE TABLE `user_memory` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `memory_type` VARCHAR(64) NOT NULL,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `evidence` LONGTEXT NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `create_time` DATETIME NOT NULL,
  `update_time` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `ix_user_memory_knowledge_point` (`knowledge_point`),
  KEY `ix_user_memory_user_id` (`user_id`),
  KEY `ix_user_memory_subject` (`subject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `user_pending_recommendation`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user_pending_recommendation`;
CREATE TABLE `user_pending_recommendation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `knowledge_point_id` BIGINT NOT NULL,
  `reason` LONGTEXT NULL,
  `is_finish` TINYINT(1) NULL,
  `create_time` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_rec_user` (`user_id`),
  KEY `idx_rec_finish` (`is_finish`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `user_profile`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user_profile`;
CREATE TABLE `user_profile` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `target_exam` VARCHAR(64) NOT NULL,
  `target_date` VARCHAR(32) NOT NULL,
  `daily_minutes` BIGINT NOT NULL,
  `learning_stage` VARCHAR(64) NOT NULL,
  `long_profile` LONGTEXT NOT NULL,
  `update_time` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_user_profile_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `video_crawl_log`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `video_crawl_log`;
CREATE TABLE `video_crawl_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `section` VARCHAR(128) NULL DEFAULT "",
  `url` VARCHAR(255) NULL,
  `platform` VARCHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `crawl_time` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `error_msg` LONGTEXT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Table structure for `video_resource`
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `video_resource`;
CREATE TABLE `video_resource` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `subject` VARCHAR(64) NOT NULL,
  `knowledge_point` VARCHAR(128) NOT NULL,
  `title` VARCHAR(180) NOT NULL,
  `platform` VARCHAR(64) NOT NULL,
  `url` VARCHAR(255) NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `cover_url` VARCHAR(255) NULL DEFAULT '',
  `duration` VARCHAR(32) NULL DEFAULT '',
  `is_deleted` TINYINT(1) NULL DEFAULT 0,
  `quality_score` BIGINT NULL DEFAULT 0,
  `author` VARCHAR(128) NULL DEFAULT '',
  `crawl_source` VARCHAR(16) NULL DEFAULT 'seed',
  `section` VARCHAR(128) NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `ix_video_resource_subject` (`subject`),
  KEY `ix_video_resource_knowledge_point` (`knowledge_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Foreign key constraints
-- ------------------------------------------------------------
ALTER TABLE `answer_record` ADD CONSTRAINT `fk_answer_record_0_question` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `answer_record` ADD CONSTRAINT `fk_answer_record_1_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `conversation` ADD CONSTRAINT `fk_conversation_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `conversation_message` ADD CONSTRAINT `fk_conversation_message_0_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversation` (`id`);
ALTER TABLE `favorite_question` ADD CONSTRAINT `fk_favorite_question_0_question` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`) ON DELETE CASCADE;
ALTER TABLE `favorite_question` ADD CONSTRAINT `fk_favorite_question_1_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
ALTER TABLE `forum_checkin` ADD CONSTRAINT `fk_forum_checkin_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `forum_collect` ADD CONSTRAINT `fk_forum_collect_0_forum_post` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`) ON DELETE CASCADE;
ALTER TABLE `forum_collect` ADD CONSTRAINT `fk_forum_collect_1_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
ALTER TABLE `forum_comment` ADD CONSTRAINT `fk_forum_comment_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `forum_comment` ADD CONSTRAINT `fk_forum_comment_1_forum_post` FOREIGN KEY (`post_id`) REFERENCES `forum_post` (`id`);
ALTER TABLE `forum_like` ADD CONSTRAINT `fk_forum_like_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
ALTER TABLE `forum_post` ADD CONSTRAINT `fk_forum_post_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `knowledge_mastery` ADD CONSTRAINT `fk_knowledge_mastery_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `mistake` ADD CONSTRAINT `fk_mistake_0_question` FOREIGN KEY (`question_id`) REFERENCES `question` (`id`);
ALTER TABLE `mistake` ADD CONSTRAINT `fk_mistake_1_answer_record` FOREIGN KEY (`answer_record_id`) REFERENCES `answer_record` (`id`);
ALTER TABLE `mistake` ADD CONSTRAINT `fk_mistake_2_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `question` ADD CONSTRAINT `fk_question_0_question_generation_session` FOREIGN KEY (`session_id`) REFERENCES `question_generation_session` (`id`);
ALTER TABLE `question_generation_session` ADD CONSTRAINT `fk_question_generation_session_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `report` ADD CONSTRAINT `fk_report_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `user_daily_activity` ADD CONSTRAINT `fk_user_daily_activity_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
ALTER TABLE `user_memory` ADD CONSTRAINT `fk_user_memory_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
ALTER TABLE `user_pending_recommendation` ADD CONSTRAINT `fk_user_pending_recommendation_0_knowledge_point` FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_point` (`id`) ON DELETE CASCADE;
ALTER TABLE `user_pending_recommendation` ADD CONSTRAINT `fk_user_pending_recommendation_1_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
ALTER TABLE `user_profile` ADD CONSTRAINT `fk_user_profile_0_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

-- ------------------------------------------------------------
-- Data for `answer_record`
-- ------------------------------------------------------------
INSERT INTO `answer_record` (`id`, `user_id`, `question_id`, `subject`, `knowledge_point`, `user_answer`, `standard_answer`, `is_correct`, `feedback`, `mastery_feedback`, `create_time`, `is_deleted`, `update_time`) VALUES
  (1, 1, 5, '????', '??????', 'A', 'C', 0, '批改结果：回答错误。你的答案：A；标准答案：C。命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '', '2026-06-23 03:21:04.565644', 0, '2026-06-24 11:51:26'),
  (2, 1, 8, '操作系统', '页面置换算法', 'A', 'C', 0, '批改结果：回答错误。你的答案：A；标准答案：C。命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '掌握', '2026-06-23 03:21:29.073401', 0, '2026-06-24 11:51:26'),
  (3, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案是错误的。标准答案是A（循环冗余检验（CRC））。关键原因是循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效地检测数据传输中的错误。而海明码虽然可以用于差错检测和纠正，但在数据链路层中并不常用。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:01.503788', 0, '2026-06-24 11:51:26'),
  (4, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '正误：错误；标准答案：A. 循环冗余检验（CRC）；关键原因：循环冗余检验（CRC）是数据链路层广泛使用的差错检测机制，而海明码虽然可以用于差错检测和纠正，但在数据链路层中并不常用。；下一步建议：复习数据链路层的差错检测机制，重点理解CRC的工作原理及其在数据链路层中的应用。', '', '2026-06-23 13:35:02.190377', 0, '2026-06-24 11:51:26'),
  (5, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案不正确。标准答案是A，即循环冗余检验（CRC）。CRC是一种广泛用于数据链路层的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码（C）也是一种差错检测和纠正的机制，但它通常用于更高层次的错误处理，而不是数据链路层的主要机制。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:02.444717', 0, '2026-06-24 11:51:26'),
  (6, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案是错误的。标准答案是A（循环冗余检验（CRC））。循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码（C选项）也是一种差错检测和纠正的机制，但它通常用于更高层次的错误处理，而不是数据链路层的主要机制。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:03.180056', 0, '2026-06-24 11:51:26'),
  (7, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '正误：错误；标准答案：A. 循环冗余检验（CRC）；关键原因：循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效检测数据传输中的错误。虽然海明码也是一种差错检测和纠正的方法，但它更常用于更高层或特定场景，而非数据链路层的主要机制。；下一步建议：建议复习数据链路层的差错检测机制，特别是循环冗余检验（CRC）的原理和应用场景。同时，可以对比学习其他差错检测方法如奇偶校验、海明码和校验和，理解它们在不同层次和场景中的应用。', '', '2026-06-23 13:35:03.874066', 0, '2026-06-24 11:51:26'),
  (8, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案不正确。标准答案是A，即循环冗余检验（CRC）。CRC是一种广泛用于数据链路层的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码（C选项）也是一种差错检测和纠正的机制，但它更常用于更高层的协议或特定应用中，而不是数据链路层的主要机制。建议复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:04.074201', 0, '2026-06-24 11:51:26'),
  (9, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案是错误的。标准答案是A（循环冗余检验（CRC））。关键原因是循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码（C）也是一种差错检测和纠正的机制，但它更常用于更高层的协议或特定场景。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:13.649100', 0, '2026-06-24 11:51:26'),
  (10, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案是错误的。标准答案是A（循环冗余检验（CRC））。循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码（C）也是一种差错检测和纠正的机制，但它更常用于更高层的协议或存储系统中。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:14.204817', 0, '2026-06-24 11:51:26'),
  (11, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '正误：错误；标准答案：A. 循环冗余检验（CRC）；关键原因：循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，而海明码虽然可以用于差错检测和纠正，但在数据链路层中不如CRC常见。；下一步建议：复习数据链路层中常用的差错检测机制，特别是循环冗余检验（CRC）的原理和应用场景。', '', '2026-06-23 13:35:14.264518', 0, '2026-06-24 11:51:26'),
  (12, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '正误：错误；标准答案：A. 循环冗余检验（CRC）；关键原因：循环冗余检验（CRC）是数据链路层中广泛使用的差错检测机制，能够高效地检测数据传输中的错误。虽然海明码也是一种差错检测和纠正的机制，但它更常用于更高层的协议或特定场景，而不是数据链路层的标准机制。；下一步建议：建议复习数据链路层的差错检测机制，特别是循环冗余检验（CRC）的工作原理和应用场景。同时，可以对比学习其他差错检测和纠正机制，如奇偶校验、海明码和校验和，理解它们各自的优缺点和适用场景。', '', '2026-06-23 13:35:14.473503', 0, '2026-06-24 11:51:26'),
  (13, 1, 53, '计算机网络', '数据链路层', 'C', 'A', 0, '你的答案不正确。标准答案是A，即循环冗余检验（CRC）。在数据链路层中，CRC是一种高效的差错检测机制，能够检测数据传输中的错误。虽然海明码（C选项）也是一种差错检测和纠正的机制，但它更常用于更高层的协议或存储系统中，而不是数据链路层。建议你复习数据链路层的差错检测机制，特别是CRC的工作原理和应用场景。', '', '2026-06-23 13:35:15.588908', 0, '2026-06-24 11:51:26'),
  (14, 1, 54, '数据结构', '图', '队', 'A', 0, '正误：错误；标准答案：A；关键原因：广度优先遍历（BFS）使用队列来辅助实现，因为队列的先进先出（FIFO）特性保证了先访问的顶点其邻接顶点也会被先访问。用户答案中的''队''虽然指的是队列，但未选择正确的选项字母。；下一步建议：复习BFS的实现方式，确保理解队列在其中的作用。同时，注意在选择题中准确匹配选项和答案。', '', '2026-06-23 13:41:40.917777', 0, '2026-06-24 11:51:26'),
  (15, 1, 49, '数据结构', '图', '队列', '队列', 1, '你的答案是正确的。在图的广度优先遍历（BFS）中，确实使用队列来辅助实现。这是因为队列的先进先出（FIFO）特性能够确保按照层次顺序访问节点，符合BFS的需求。标准答案也是''队列''。', '', '2026-06-23 13:54:24.560832', 0, '2026-06-24 11:51:26'),
  (16, 1, 50, '数据结构', '查找', '满二叉树', '单支树', 0, '正误：错误；标准答案：单支树；关键原因：当二叉排序树退化为单支树时，树的高度达到最大，查找性能最差，此时查找过程等同于顺序查找。满二叉树的查找性能较好，因为其高度最小。；下一步建议：复习二叉排序树的形态对查找性能的影响，特别是单支树和平衡二叉树的区别。可以通过绘制不同形态的二叉排序树来加深理解。', '', '2026-06-23 13:55:44.396235', 0, '2026-06-24 11:51:26'),
  (17, 1, 51, '数据结构', '栈和队列', '栈', '栈和队列 的标准定义（根据教材）', 1, 'correctness：部分正确；standard_answer：栈和队列 的标准定义（根据教材）；key_reason：用户答案只回答了栈的定义，没有完整表述队列的定义。栈和队列是两种不同的数据结构，栈是后进先出（LIFO），队列是先进先出（FIFO）。；next_steps：建议复习栈和队列的基本定义和特性，确保能够完整表述两者的核心定义。', '', '2026-06-23 13:56:16.321523', 0, '2026-06-24 11:51:26'),
  (18, 1, 58, '操作系统', '页面置换算法', 'A', 'B', 0, '你的答案A是错误的，标准答案是B。关键原因在于LRU页面置换算法会根据最近最少使用的原则进行页面置换。在给定的页面访问序列中，共发生了7次页面置换。建议你仔细回顾LRU算法的执行过程，特别是每次页面置换时的选择依据。可以通过绘制页面访问和置换的详细表格来加深理解。', '', '2026-06-24 11:53:49.544999', 0, '2026-06-24 11:53:49.544999'),
  (19, 1, 61, '操作系统', '页面置换算法', 'A', 'B', 0, '你的答案A是错误的。标准答案是B。关键原因在于FIFO页面置换算法的置换次数计算有误。按照FIFO算法，页面置换过程如下：(1)1,2,3；(2)置换1，装入4→2,3,4；(3)1不在内存，置换2→3,4,1；(4)2不在内存，置换3→4,1,2；(5)5不在内存，置换4→1,2,5；(6)1已在内存；(7)2已在内存；(8)3不在内存，置换1→2,5,3；(9)4不在内存，置换2→5,3,4；(10)5已在内存。共发生7次置换。建议你仔细理解FIFO算法的置换规则，多做类似题目加深理解。', '', '2026-06-24 11:58:20.454139', 0, '2026-06-24 11:58:20.454139'),
  (20, 1, 70, '操作系统', '同步与互斥', 'A', 'B', 0, '你的答案错误。标准答案是 B。关键原因：同步与互斥的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。下一步建议：建议结合定义、关键步骤和边界条件深入理解同步与互斥，而不仅仅是记忆结论。', '', '2026-06-25 17:33:29.212894', 0, '2026-06-25 17:33:29.212894'),
  (21, 1, 71, '操作系统', '同步与互斥', 'A', 'B', 0, '你的答案错误。标准答案是 B。在 408 考试中，同步与互斥不仅需要记忆结论，还需要理解其定义、关键步骤和边界条件。建议你深入理解同步与互斥的原理和应用，而不仅仅是记忆结论。', '', '2026-06-25 17:35:56.569273', 0, '2026-06-25 17:35:56.569273'),
  (22, 1, 91, '计算机组成原理', '指令系统', 'B', 'A', 0, '正误：错误；标准答案：A；关键原因：立即寻址方式的操作数直接包含在指令中，不需要访问内存即可获得操作数。而直接寻址需要通过地址访问内存来获取操作数。；下一步建议：复习各种寻址方式的特点，重点理解立即寻址和直接寻址的区别。可以通过绘制寻址方式示意图来加深理解。', '', '2026-06-25 18:28:42.115796', 0, '2026-06-25 18:28:42.115796');

-- ------------------------------------------------------------
-- Data for `conversation`
-- ------------------------------------------------------------
INSERT INTO `conversation` (`id`, `user_id`, `title`, `summary`, `create_time`, `update_time`, `is_deleted`) VALUES
  (1, 1, 'LRU 和 FIFO 有什么区别？', '', '2026-06-23 03:25:38.332997', '2026-06-23 03:25:38.332997', 0),
  (2, 1, 'LRU 和 FIFO 有什么区别？', '', '2026-06-23 03:45:39.361221', '2026-06-23 03:45:39.361221', 0),
  (3, 1, '你是谁', '', '2026-06-23 03:49:03.104429', '2026-06-23 03:49:03.104429', 0),
  (4, 1, 'LRU 和 FIFO 页面置换算法有什么区别？', '', '2026-06-23 03:53:41.413434', '2026-06-23 03:53:41.413434', 0),
  (5, 1, 'LRU 和 FIFO 页面置换算法有什么区别？', '', '2026-06-23 03:55:51.767803', '2026-06-23 03:55:51.767803', 0),
  (6, 1, 'LRU 和 FIFO 页面置换算法有什么区别？', '', '2026-06-23 04:00:57.249897', '2026-06-23 04:00:57.249897', 0),
  (7, 1, 'LRU 和 FIFO 页面置换算法有什么区别？', '', '2026-06-23 06:39:49.258273', '2026-06-23 06:39:49.259835', 0),
  (8, 1, '那为什么 LRU 不一定最优？', '', '2026-06-23 06:41:52.595254', '2026-06-23 06:41:52.595254', 0),
  (9, 1, '栈是什么', '', '2026-06-23 13:10:50.858627', '2026-06-23 13:10:50.858627', 0),
  (10, 1, '栈是什么', '', '2026-06-24 03:09:27.089989', '2026-06-24 03:09:27.089989', 0),
  (11, 1, '什么是LRU页面置换算法？', '', '2026-06-25 17:18:45.012966', '2026-06-25 17:18:45.012966', 0),
  (12, 1, '什么是进程同步？什么是互斥？', '', '2026-06-25 17:32:32.237571', '2026-06-25 17:32:32.237571', 0),
  (13, 1, '什么是死锁？死锁的四个必要条件是什么？', '', '2026-06-25 17:54:43.883114', '2026-06-25 17:54:43.883114', 0);

-- ------------------------------------------------------------
-- Data for `conversation_message`
-- ------------------------------------------------------------
INSERT INTO `conversation_message` (`id`, `conversation_id`, `role`, `content`, `create_time`) VALUES
  (1, 1, 'user', 'LRU 和 FIFO 有什么区别？', '2026-06-23 03:25:38.343556'),
  (2, 1, 'assistant', '<b>定位：</b>数据结构 · 线性表。<br><b>解释：</b>线性表 是 数据结构 的核心复习单元，需要掌握定义、流程、计算题和常见陷阱。<br><b>结合你的画像：</b>?????? 反复出现 ????，复习时要先列规则再计算。<br>建议立刻做 1 道同知识点中等难度选择题，把理解转成可检验的结果。', '2026-06-23 03:25:38.343556'),
  (3, 2, 'user', 'LRU 和 FIFO 有什么区别？', '2026-06-23 03:46:24.360514'),
  (4, 2, 'assistant', '', '2026-06-23 03:46:24.360514'),
  (5, 3, 'user', '你是谁', '2026-06-23 03:49:47.947384'),
  (6, 3, 'assistant', '', '2026-06-23 03:49:47.947384'),
  (7, 4, 'user', 'LRU 和 FIFO 页面置换算法有什么区别？', '2026-06-23 03:54:07.831320'),
  (8, 4, 'assistant', '', '2026-06-23 03:54:07.831320'),
  (9, 5, 'user', 'LRU 和 FIFO 页面置换算法有什么区别？', '2026-06-23 03:56:47.752986'),
  (10, 5, 'assistant', '<b>定位：</b>操作系统 · 页面置换算法。<br><b>解释：</b>页面置换算法 是 操作系统 的核心复习单元，需要掌握定义、流程、计算题和常见陷阱。<br><b>结合你的画像：</b>?????? 反复出现 ????，复习时要先列规则再计算。<br>建议立刻做 1 道同知识点中等难度选择题，把理解转成可检验的结果。', '2026-06-23 03:56:47.752986'),
  (11, 6, 'user', 'LRU 和 FIFO 页面置换算法有什么区别？', '2026-06-23 04:00:57.253906'),
  (12, 6, 'assistant', '<b>科目定位：</b>操作系统 - 页面置换算法<br><br><br><br><b>结构化解释：</b><br><ol><br><li><b>FIFO</b>（先进先出）：置换最早进入内存的页面，维护一个队列记录页面加载顺序</li><br><li><b>LRU</b>（最近最少使用）：置换最久未被访问的页面，需维护访问时间戳或移动页面到栈顶</li><br></ol><br><br><b>核心区别：</b><br>FIFO只关注进入顺序，可能置换活跃页面；LRU基于局部性原理，更贴近程序实际访问特征。<br><br><br><br><b>个性化提醒：</b><br>根据记忆记录，您容易在<b>规则应用</b>上出错。建议：①先写下算法规则 ②明确数据结构（队列/栈）③分步标记页面状态。<br><br><br><br><b>训练建议：</b><br>1. 对比做3道含Belady现象的FIFO题<br><br>2. 用访问序列"1,2,3,4,1,2,5"手动模拟两种算法<br><br>3. 重点记录置换时刻的决策依据', '2026-06-23 04:01:08.604484'),
  (13, 7, 'user', 'LRU 和 FIFO 页面置换算法有什么区别？', '2026-06-23 06:39:49.262923'),
  (14, 7, 'assistant', '<b>科目定位：</b>操作系统 - 页面置换算法<br><br><br><br><b>结构化解释：</b><br><ol><br><li><b>FIFO</b>（先进先出）：置换最早进入内存的页面，维护一个队列记录页面进入顺序。</li><br><li><b>LRU</b>（最近最少使用）：置换最久未被访问的页面，需要记录页面访问时间戳或使用近似算法（如时钟算法）。</li><br></ol><br><b>核心区别：</b>FIFO仅关注进入顺序，LRU关注访问时序；LRU理论上更接近最优置换，但实现开销更大。<br><br><br><br><b>个性化提醒：</b>根据你的错题记录，注意<b>先列规则再计算</b>：<br><br>1. FIFO遇到相同"最早页面"时按队列顺序置换<br><br>2. LRU出现访问时间相同时可约定左侧优先<br><br><br><br><b>训练建议：</b><br>1. 用<u>相同页面序列</u>对比两种算法置换过程<br><br>2. 重点练习Belady异常（FIFO特有现象）的判定条件', '2026-06-23 06:40:00.454764'),
  (15, 8, 'user', '那为什么 LRU 不一定最优？', '2026-06-23 06:41:52.597007'),
  (16, 8, 'assistant', '<b>科目定位：</b>操作系统 - 页面置换算法<br><br><br><br><b>结构化解释：</b><ol><br><li><b>理论最优性：</b>LRU基于"最近最少使用"原则，是近似OPT算法的实现，但无法预知未来访问序列</li><br><li><b>反例存在：</b>特定访问序列下（如循环访问超过缓存大小的数据集），LRU会产生比FIFO更多的缺页</li><br><li><b>实现代价：</b>严格LRU需要维护时间戳或移动链表，实际系统中多用近似实现（如Clock算法）</li><br></ol><br><br><b>个性化提醒：</b>您曾因<b>规则理解不完整</b>导致错误，特别注意：<br><br>"最优"指理论上的OPT算法（需预知未来），而LRU是<b>基于历史的最优</b>，二者性质不同。<br><br><b>训练建议：</b><ol><br><li>对比LRU/OPT/FIFO的缺页计算差异</li><br><li>重点练习给出访问序列的手算过程</li><br></ol>', '2026-06-23 06:42:05.054816'),
  (17, 9, 'user', '栈是什么', '2026-06-23 13:10:50.863010'),
  (18, 9, 'assistant', '<b>科目与知识点定位</b><br><br>属于<b>数据结构</b>中的<b>栈和队列</b>核心考点（检索知识第2条）<br><br><b>结构化解释</b><ol><br><li><b>定义</b>：受限的线性表，仅允许在<b>表尾（栈顶）</b>进行插入（push）和删除（pop）</li><br><li><b>特性</b>：后进先出（LIFO），类比叠盘子</li><br><li><b>核心操作</b>：初始化、判空、进栈、出栈、读取栈顶（注意与队列区别）</li><br><li><b>实现方式</b>：顺序栈（数组）和链栈（链表）</li></ol><br><br><b>个性化提醒</b><br><br>您存在<b>概念混淆</b>风险（长期记忆第1条），建议：<br><br>1. 区分栈/队列操作术语（如栈用push/pop，队列用enqueue/dequeue）<br><br>2. 画图辅助理解进出栈序列（如选择题常考合法出栈顺序）<br><br><b>下一步建议</b><br><br>优先练习<b>栈的应用场景</b>（如表达式求值、递归调用栈），注意边界条件（如空栈pop操作）', '2026-06-23 13:11:06.057625'),
  (19, 10, 'user', '栈是什么', '2026-06-24 03:09:27.094675'),
  (20, 10, 'assistant', '<b>科目与知识点定位</b><br><br>数据结构 → 栈和队列（线性表的特殊形式）<br><br><b>结构化解释</b><br><br>栈是<b>后进先出（LIFO）</b>的线性表，核心操作：<br><ol><br>  <li><b>Push</b>：元素入栈（栈顶指针上移）</li><br>  <li><b>Pop</b>：元素出栈（栈顶指针下移）</li><br>  <li><b>Peek</b>：查看栈顶元素（不移动指针）</li><br></ol><br>应用场景：函数调用栈、表达式求值、括号匹配等。<br><br><b>个性化提醒</b><br><br>您近期在DMA计算中易混淆时间占用问题（见长期记忆ID6/7），需注意：<br><br>- 栈操作类似DMA的<b>批量处理</b>特性，但栈的指针移动是严格单向的<br>- 警惕<b>空栈弹出</b>和<b>栈满压入</b>的边界条件（类似存储周期计算漏判）<br><br><b>下一步建议</b><br><br>1. 对比栈与队列的进出顺序差异<br><br>2. 结合真题练习栈在<b>递归调用</b>中的应用<br><br>3. 强化空/满栈的判定条件（常与数组实现结合考查）', '2026-06-24 03:09:47.110980'),
  (21, 10, 'user', '队列为什么是先进先出呢', '2026-06-24 03:10:01.104639'),
  (22, 10, 'assistant', '<b>科目与知识点定位</b><br><br>数据结构 - 栈和队列（线性表的特殊形式）<br><br><b>结构化解释</b><br><br>队列的FIFO特性由两个核心操作保证：<br><br>1. <b>入队(enqueue)</b>：元素只能从<b>队尾(rear)</b>插入<br><br>2. <b>出队(dequeue)</b>：元素只能从<b>队头(front)</b>删除<br><br>这种限制性操作顺序天然形成先进先出的数据流，类比现实中的排队场景。<br><br><b>个性化提醒</b><br><br>您近期在DMA传输时间计算上存在混淆（长期记忆ID:6-8），需注意：<br><br>• 队列操作时间复杂度为O(1)，与DMA时间计算不同<br><br>• 队列是逻辑结构，DMA是硬件机制，勿将数据结构特性与硬件特性混淆<br><br><b>下一步建议</b><br><br>1. 对比栈(LIFO)与队列的出入规则差异<br><br>2. 通过循环队列实现练习强化边界条件处理<br><br>3. 区分数据结构特性与组成原理中的传输机制差异', '2026-06-24 03:10:18.001967'),
  (23, 11, 'user', '什么是LRU页面置换算法？', '2026-06-25 17:18:45.018284'),
  (24, 11, 'assistant', '科目：操作系统 | 知识点：页面置换算法<br><br><b>LRU算法核心要点：</b><br><ol><br><li>全称Least Recently Used，选择<b>最久未被访问</b>的页面置换</li><br><li>需维护访问时间戳或访问顺序栈，实现开销较大</li><br><li>属于堆栈类算法，具有Belady异常免疫特性</li><br></ol><br><br><b>针对性提醒：</b><br>您对缺页次数的计算存在误区——初始空载时所有页框均需加载（计为N次缺页），后续每次置换计1次缺页。重复访问已存在页面<b>不触发缺页</b>（与您记忆中的"1次初始缺页"有偏差）<br><br><b>训练建议：</b><br>专项练习LRU缺页计算题，重点区分：<br>1. 初始空载阶段缺页次数=页框数<br>2. 不同页面序列的置换时机判断<br>3. 对比FIFO算法的Belady异常现象', '2026-06-25 17:19:03.718938'),
  (25, 12, 'user', '什么是进程同步？什么是互斥？', '2026-06-25 17:32:32.239599'),
  (26, 12, 'assistant', '科目：操作系统 | 知识点：进程同步与互斥<br><br><br><b>概念定义：</b><br><br><ol><br><li><b>进程同步</b>：协调多个进程的执行顺序（如生产者-消费者问题），确保数据一致性</li><br><li><b>互斥</b>：保证同一时刻只有一个进程访问临界资源（如打印机）</li><br></ol><br><br><b>核心区别：</b><br><br>同步关注执行时序的协作关系，互斥关注资源的独占访问<br><br><br><b>记忆提醒：</b><br><br>您近期记忆的DMA传输时间公式（数据量×存储周期）与中断处理机制，可类比进程切换时的上下文保存开销<br><br><br><b>训练建议：</b><br><br>专项练习：<br><br>1. 用信号量实现读者-写者问题<br><br>2. 分析银行家算法与互斥锁的适用场景差异', '2026-06-25 17:32:42.822834'),
  (27, 13, 'user', '什么是死锁？死锁的四个必要条件是什么？', '2026-06-25 17:54:43.894261'),
  (28, 13, 'assistant', '科目：操作系统 | 知识点：死锁<br><br><b>死锁定义：</b>多个进程因循环等待资源而无法继续执行的状态<br><br><br><b>四个必要条件：</b><br><ol><br><li><b>互斥条件</b>：资源一次只能被一个进程占用</li><br><li><b>占有且等待</b>：进程持有资源同时申请新资源</li><br><li><b>不可剥夺</b>：已分配资源不能被强行收回</li><br><li><b>环路等待</b>：存在进程-资源的循环等待链</li><br></ol><br><br><b>记忆提醒：</b>您对LRU缺页次数的计算掌握较好，可类比记忆——死锁条件需<b>全部满足</b>（类似缺页必须严格按时间戳判断）<br><br><br><b>训练建议：</b><br>1. 专项练习：判断给定场景是否满足死锁条件<br>2. 知识点复习：对比死锁预防/避免/检测策略<br>3. 错题重做：银行家算法例题（避免策略）', '2026-06-25 17:54:57.043918');

-- ------------------------------------------------------------
-- Data for `favorite_question`
-- ------------------------------------------------------------
-- favorite_question: 0 rows

-- ------------------------------------------------------------
-- Data for `forum_category`
-- ------------------------------------------------------------
INSERT INTO `forum_category` (`id`, `name`, `description`, `sort_order`, `is_deleted`) VALUES
  (1, '全部', '全部 讨论区', 1, 0),
  (2, '数据结构', '数据结构 讨论区', 2, 0),
  (3, '组成原理', '组成原理 讨论区', 3, 0),
  (4, '操作系统', '操作系统 讨论区', 4, 0),
  (5, '计算机网络', '计算机网络 讨论区', 5, 0),
  (6, '经验分享', '经验分享 讨论区', 6, 0);

-- ------------------------------------------------------------
-- Data for `forum_checkin`
-- ------------------------------------------------------------
INSERT INTO `forum_checkin` (`id`, `user_id`, `checkin_date`, `create_time`) VALUES
  (1, 1, '2026-06-24', '2026-06-24 00:27:26.403075');

-- ------------------------------------------------------------
-- Data for `forum_collect`
-- ------------------------------------------------------------
-- forum_collect: 0 rows

-- ------------------------------------------------------------
-- Data for `forum_comment`
-- ------------------------------------------------------------
INSERT INTO `forum_comment` (`id`, `post_id`, `user_id`, `parent_id`, `content`, `create_time`, `is_deleted`) VALUES
  (1, 2, 1, NULL, '栈', '2026-06-24 00:33:01.298471', 0);

-- ------------------------------------------------------------
-- Data for `forum_like`
-- ------------------------------------------------------------
INSERT INTO `forum_like` (`id`, `user_id`, `target_type`, `target_id`, `create_time`) VALUES
  (1, 1, 'post', 2, '2026-06-25 17:58:08.440532'),
  (2, 1, 'post', 1, '2026-06-25 17:58:10.127262');

-- ------------------------------------------------------------
-- Data for `forum_post`
-- ------------------------------------------------------------
INSERT INTO `forum_post` (`id`, `user_id`, `category`, `subject`, `knowledge_point`, `title`, `content`, `like_count`, `collect_count`, `comment_count`, `is_top`, `status`, `create_time`, `update_time`, `is_deleted`, `create_ip`) VALUES
  (1, 1, '操作系统', '操作系统', '页面置换算法', 'LRU 页面置换到底什么时候更新访问顺序？', '命中后到底要不要移动最近使用位置？做题总漏。', 29, 0, 12, 0, 'normal', '2026-06-23 03:21:04.467595', '2026-06-25 17:58:10.130933', 0, ''),
  (2, 1, '数据结构', '数据结构', '', '栈', '什么是栈', 1, 0, 1, 0, 'normal', '2026-06-24 00:29:21.398862', '2026-06-25 17:58:08.454907', 0, '');

-- ------------------------------------------------------------
-- Data for `knowledge_document`
-- ------------------------------------------------------------
-- knowledge_document: 0 rows

-- ------------------------------------------------------------
-- Data for `knowledge_mastery`
-- ------------------------------------------------------------
INSERT INTO `knowledge_mastery` (`id`, `user_id`, `subject`, `knowledge_point`, `final_status`, `total_answer_count`, `correct_count`, `wrong_count`, `unfamiliar_count`, `unknown_count`, `ocr_mistake_count`, `qa_count`, `forum_count`, `weak_score`, `update_time`, `mastered_count`, `user_mark_status`, `continuous_wrong_count`, `last_answer_time`) VALUES
  (1, 1, '数据结构', '线性表', '不熟', 0, 0, 0, 0, 0, 0, 5, 0, 5.0, '2026-06-24 03:10:18.013644', 0, '', 0, NULL),
  (2, 1, '数据结构', '栈和队列', '不熟', 1, 1, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 16:38:47.938258', 0, '', 0, '2026-06-23 13:56:16.321523'),
  (3, 1, '数据结构', '树与二叉树', '不熟', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-24 00:55:00.129075', 0, '不熟', 0, NULL),
  (4, 1, '数据结构', '图', '不熟', 2, 1, 1, 0, 0, 0, 0, 0, 2.0, '2026-06-23 13:54:24.574403', 0, '', 0, '2026-06-23 13:54:24.560832'),
  (5, 1, '数据结构', '查找', '不会', 1, 0, 1, 0, 0, 0, 0, 0, 3.0, '2026-06-23 13:55:44.400188', 0, '', 1, '2026-06-23 13:55:44.396235'),
  (6, 1, '数据结构', '排序', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (7, 1, '计算机组成原理', '数据表示与运算', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 12:51:04.650039', 0, '', 0, NULL),
  (8, 1, '计算机组成原理', '存储系统', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (9, 1, '计算机组成原理', '指令系统', '不会', 1, 0, 1, 0, 0, 0, 0, 0, 3.0, '2026-06-25 18:28:42.138582', 0, '掌握', 1, '2026-06-25 18:28:42.115796'),
  (10, 1, '计算机组成原理', '中央处理器', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (11, 1, '计算机组成原理', '总线与 I/O', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (12, 1, '操作系统', '进程与线程', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 12:51:04.658603', 0, '', 0, NULL),
  (13, 1, '操作系统', '同步与互斥', '不会', 2, 0, 2, 0, 0, 0, 0, 0, 6.0, '2026-06-25 17:35:56.579046', 0, '', 2, '2026-06-25 17:35:56.569273'),
  (14, 1, '操作系统', '死锁', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (15, 1, '操作系统', '内存管理', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (16, 1, '操作系统', '页面置换算法', '薄弱点', 3, 0, 3, 0, 0, 3, 7, 1, 24.0, '2026-06-25 17:19:03.724831', 1, '掌握', 3, '2026-06-24 11:58:20.454139'),
  (17, 1, '操作系统', '文件系统', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (18, 1, '计算机网络', '体系结构', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 12:51:04.670868', 0, '', 0, NULL),
  (19, 1, '计算机网络', '数据链路层', '薄弱点', 11, 0, 11, 0, 0, 0, 0, 0, 33.0, '2026-06-23 13:35:15.596416', 0, '', 11, '2026-06-23 13:35:15.588908'),
  (20, 1, '计算机网络', '网络层', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (21, 1, '计算机网络', '传输层', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (22, 1, '计算机网络', '应用层', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-23 03:21:04.468962', 0, '', 0, NULL),
  (23, 1, '????', '??????', '不熟', 1, 0, 1, 0, 0, 0, 0, 0, 3.0, '2026-06-23 03:21:04.571178', 0, '', 0, NULL),
  (24, 1, '待生成', '待生成', '薄弱点', 0, 0, 0, 0, 0, 3, 0, 0, 9.0, '2026-06-23 16:13:01.242064', 0, '', 0, NULL),
  (25, 1, '计算机组成原理', '输入输出系统', '薄弱点', 0, 0, 0, 0, 0, 4, 0, 0, 14.0, '2026-06-25 17:47:19.895060', 0, '不会', 0, NULL),
  (26, 1, '计算机组成原理', 'DMA与中断方式的时间计算', '不会', 0, 0, 0, 0, 0, 1, 0, 0, 3.0, '2026-06-23 16:32:58.525172', 0, '不会', 0, NULL),
  (27, 1, '操作系统', '进程管理', '不熟', 0, 0, 0, 0, 0, 0, 2, 0, 2.0, '2026-06-25 17:54:57.052660', 0, '', 0, NULL),
  (28, 1, '数据结构', '绪论', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.850245', 0, '', 0, NULL),
  (29, 1, '数据结构', '栈、队列和数组', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.856836', 0, '', 0, NULL),
  (30, 1, '数据结构', '串', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.861055', 0, '', 0, NULL),
  (31, 1, '计算机组成原理', '计算机系统概述', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.876604', 0, '', 0, NULL),
  (32, 1, '计算机组成原理', '数据的表示和运算', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.880648', 0, '', 0, NULL),
  (33, 1, '计算机组成原理', '总线', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.889492', 0, '', 0, NULL),
  (34, 1, '操作系统', '计算机系统概述', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.899101', 0, '', 0, NULL),
  (35, 1, '操作系统', '文件管理', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.908490', 0, '', 0, NULL),
  (36, 1, '操作系统', '输入输出管理', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.911522', 0, '', 0, NULL),
  (37, 1, '计算机网络', '计算机网络体系结构', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.914563', 0, '', 0, NULL),
  (38, 1, '计算机网络', '物理层', '未学', 0, 0, 0, 0, 0, 0, 0, 0, 0.0, '2026-06-25 17:47:19.917597', 0, '', 0, NULL);

-- ------------------------------------------------------------
-- Data for `knowledge_point`
-- ------------------------------------------------------------
INSERT INTO `knowledge_point` (`id`, `subject`, `name`, `parent_name`, `level`, `content`, `common_mistakes`, `keywords`, `is_high_frequency`, `create_time`, `update_time`, `subject_id`, `parent_id`, `section`, `is_deleted`) VALUES
  (1, '数据结构', '绪论', '数据结构', 3, '数据是所有能输入计算机并被计算机处理的符号集合；数据元素是数据的基本处理单位，一个数据元素可包含多个数据项；数据项是不可分割的最小标识单位；数据对象是性质相同的数据元素的集合，是数据的子集。', '混淆数据、数据元素、数据项三者从属层级；认为数据项可独立作为运算单元。', '数据,数据元素,数据项,数据对象,基本单位,最小标识单位', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数据结构的基本概念', 0),
  (2, '数据结构', '绪论', '数据结构', 3, '数据结构是相互之间存在一种或多种特定关系的数据元素集合，分为逻辑结构和存储结构两层；逻辑结构描述元素间抽象关系，存储结构描述数据在内存中的物理存放方式。', '把存储结构当成逻辑结构；认为逻辑结构和物理存储一一对应。', '数据结构,逻辑结构,存储结构,数据元素关系', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数据结构的基本概念', 0),
  (3, '数据结构', '绪论', '数据结构', 3, '逻辑结构分为线性结构与非线性结构；线性结构一对一，包含线性表；非线性分为一对多的树、多对多的图、无固定关系的集合。', '集合归类为线性结构；树属于多对多关系。', '线性结构,非线性结构,线性表,树,图,集合', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数据结构的基本概念', 0),
  (4, '数据结构', '绪论', '数据结构', 3, '四种存储结构：顺序存储、链式存储、索引存储、散列存储；顺序连续分配空间；链式依靠指针离散分配；索引附加索引表；散列通过哈希函数映射地址。', '散列存储需要遍历查找；索引存储无额外空间开销。', '顺序存储,链式存储,索引存储,散列存储,哈希函数', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数据结构的基本概念', 0),
  (5, '数据结构', '绪论', '数据结构', 3, '数据结构三要素：逻辑结构、存储结构、数据运算；运算定义仅依赖逻辑结构，运算实现由存储结构决定；运算包含查找、插入、删除、修改、排序五类基础操作。', '数据运算实现只和逻辑结构相关；遗漏修改运算。', '数据结构三要素,数据运算,增删改查排序,运算定义与实现', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数据结构三要素', 0),
  (6, '数据结构', '绪论', '数据结构', 3, '算法是对特定问题求解步骤的有限指令序列，具备五大特性：有穷性、确定性、可行性、输入、输出；程序不满足有穷性，可无限循环。', '算法等价于程序；忽略有穷性判定条件。', '算法五大特性,有穷性,确定性,可行性,算法与程序区别', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '算法和算法评价', 0),
  (7, '数据结构', '绪论', '数据结构', 3, '算法设计目标：正确性、可读性、健壮性、高效率、低存储；健壮性指非法输入可合理处理，不会崩溃；可读性是工程优先指标。', '健壮性等于正确性；只追求效率忽略可读性。', '算法设计目标,健壮性,可读性,高效率,低存储', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '算法和算法评价', 0),
  (8, '数据结构', '绪论', '数据结构', 3, '时间复杂度采用渐进分析，只保留最高阶项，忽略常数、低次项；分为最好、平均、最坏时间复杂度，408考试以最坏复杂度为主要考察对象。', '计算复杂度保留系数；混淆最好与最坏复杂度场景。', '时间复杂度,渐进分析,最坏复杂度,平均复杂度,最高阶项', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '算法和算法评价', 0),
  (9, '数据结构', '绪论', '数据结构', 3, '空间复杂度统计算法额外辅助空间，输入数据占用空间不计入；原地算法辅助空间O(1)；递归空间复杂度等于递归深度。', '把输入数组计入辅助空间；递归忽略栈空间开销。', '空间复杂度,辅助空间,原地算法,递归栈深度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '算法和算法评价', 0),
  (10, '数据结构', '线性表', '数据结构', 3, '线性表是零个或多个同类型数据元素的有序线性序列；第一个元素无前驱，最后一个无后继，其余元素唯一前驱唯一后继；空线性表长度为0。', '空线性表不存在；线性表可存储不同类型数据。', '线性表,有序序列,前驱后继,空线性表', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '线性表的定义和基本操作', 0),
  (11, '数据结构', '线性表', '数据结构', 3, '线性表标准操作：初始化、销毁、清空、判空、求长度、按位查找GetElem、按值查找LocateElem、插入、删除、遍历；按位查找随机存取，按值只能顺序遍历。', '混淆按位、按值查找；清空等价于销毁。', '线性表十大操作,按位查找,按值查找,插入删除遍历', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '线性表的定义和基本操作', 0),
  (12, '数据结构', '线性表', '数据结构', 3, '顺序表采用连续一维数组存储，结构体包含data数组、当前长度length、最大容量MaxSize；分为静态分配数组、动态堆分配数组两种实现。', '静态顺序表可自由扩容；length等于MaxSize。', '顺序表,静态分配,动态分配,MaxSize,length', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序表示', 0),
  (13, '数据结构', '线性表', '数据结构', 3, '顺序表插入操作：从尾部向前移动元素腾出空位，平均移动n/2个元素，复杂度O(n)；插入位置越靠前移动元素越多。', '插入从头部向后移动；插入下标无边界校验。', '顺序表插入,元素移动,平均移动次数,O(n)', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序表示', 0),
  (14, '数据结构', '线性表', '数据结构', 3, '顺序表删除操作：被删元素后续全部向前覆盖，平均移动(n-1)/2个元素；删除后length自减一。', '删除后不更新length；尾部删除仍大量移动元素。', '顺序表删除,元素覆盖,长度更新', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序表示', 0),
  (15, '数据结构', '线性表', '数据结构', 3, '单链表节点由数据域data、后继指针next组成；分为带头结点、不带头结点；头结点统一空表操作逻辑，不存储有效数据。', '头结点存储业务数据；无头链表空表判断简单。', '单链表,数据域,指针域,头结点,头指针', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (16, '数据结构', '线性表', '数据结构', 3, '单链表头插法：新节点指向原表头，更新头指针；生成链表逆序，无需遍历尾部，插入O(1)。', '头插生成正序链表；插入顺序颠倒指针赋值。', '头插法,单链表逆序,O(1)插入', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (17, '数据结构', '线性表', '数据结构', 3, '单链表尾插法：维护尾指针直接在尾部新增节点，链表顺序与输入一致；无尾指针需要遍历全表至尾部，复杂度O(n)。', '尾插无需维护尾指针；丢失尾节点造成断链。', '尾插法,尾指针,有序链表,遍历尾部', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (18, '数据结构', '线性表', '数据结构', 3, '双向链表节点增加前驱指针prior；可直接访问前驱节点，查找前驱O(1)；插入删除需要同时修改前后双向指针。', '双链表插入仅修改单侧指针；尾部prior不为空越界。', '双向链表,prior前驱,next后继,双向指针修改', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (19, '数据结构', '线性表', '数据结构', 3, '循环单链表尾节点next指向头结点；仅保存尾指针可同时快速获取头、尾节点，适合频繁访问首尾场景。', '循环链表终止条件判断NULL；尾指针无法取表头。', '循环单链表,尾指针优化,首尾快速访问', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (20, '数据结构', '线性表', '数据结构', 3, '静态链表使用数组模拟链表，游标cur替代指针；设置备用链表管理空闲数组单元，适用于无指针编程语言。', '静态链表支持随机下标存取；忘记维护备用链表头。', '静态链表,游标数组,备用链表,无指针实现', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '链式表示', 0),
  (21, '数据结构', '线性表', '数据结构', 3, '随机存取优先选顺序表；频繁中间插入删除选链表；顺序存储密度为1，链表额外指针降低存储密度；顺序存在容量上限，链表动态无上限。', '链表存储密度更高；链表插入删除无需查找前驱。', '顺序链表对比,存储密度,随机存取,动态扩容', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序表与链表的比较', 0),
  (22, '数据结构', '栈、队列和数组', '数据结构', 3, '栈是限定仅在表一端插入删除的受限线性表；允许操作端为栈顶，封闭端为栈底，遵循后进先出LIFO规则。', '栈两端均可增删；栈先进先出。', '栈,LIFO,栈顶,栈底,受限线性表', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈', 0),
  (23, '数据结构', '栈、队列和数组', '数据结构', 3, '顺序栈结构体包含数组data、栈顶指针top；空栈top=-1，栈满top=MaxSize-1；Push先自增top存入元素，Pop先取值再自减top。', '空栈top=0；出栈先减top丢失数据。', '顺序栈,top栈顶指针,栈满栈空判定,Push Pop操作', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈', 0),
  (24, '数据结构', '栈、队列和数组', '数据结构', 3, '共享栈同一数组两端分别作为两个栈栈底，top0从左向右，top1从右向左；两top相遇代表栈满，节省数组空间。', '共享栈两个top同向增长；栈满判定条件写错。', '共享栈,双向栈,双栈顶,空间复用', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈', 0),
  (25, '数据结构', '栈、队列和数组', '数据结构', 3, '链栈采用单链表实现，头结点作为栈顶，头插法入栈O(1)；无容量上限，不存在栈满溢出；空栈head->next==NULL。', '链栈尾作栈顶效率低；链栈存在栈满。', '链栈,头插入栈,无容量限制,单链表实现', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈', 0),
  (26, '数据结构', '栈、队列和数组', '数据结构', 3, '队列受限线性表，队尾rear入队，队头front出队，先进先出FIFO；普通顺序队列存在假溢出，数组尾部满前端空闲无法复用。', '队列两端可增删；顺序队列无假溢出。', '队列,FIFO,队头front,队尾rear,假溢出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '队列', 0),
  (27, '数据结构', '栈、队列和数组', '数据结构', 3, '循环队列通过取模(rear+1)%MaxSize解决假溢出；牺牲一个空位区分栈满栈空：栈满条件(rear+1)%MaxSize == front。', '循环队列rear==front代表栈满；取模运算括号遗漏。', '循环队列,取模运算,牺牲空位,栈满判定', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '队列', 0),
  (28, '数据结构', '栈、队列和数组', '数据结构', 3, '循环队列第二种实现：增加size字段记录元素个数，size==0空，size==MaxSize满，无需牺牲数组单元。', 'size方案仍需要空位置；入队忘记size自增。', '循环队列size标记,元素计数,无牺牲单元', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '队列', 0),
  (29, '数据结构', '栈、队列和数组', '数据结构', 3, '链队列保存front头指针、rear尾指针；入队尾插，出队头删；空队列front==rear==NULL，无需遍历找尾部。', '链队列仅保留头指针；出队后不更新rear。', '链队列,头尾双指针,尾插入队,无溢出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '队列', 0),
  (30, '数据结构', '栈、队列和数组', '数据结构', 3, '栈应用1：括号匹配；左括号入栈，右括号弹出栈顶匹配，遍历结束栈必须为空才合法。', '右括号无栈顶直接合法；遍历完忽略剩余左括号。', '括号匹配,栈匹配,嵌套校验', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈和队列的应用', 0),
  (31, '数据结构', '栈、队列和数组', '数据结构', 3, '栈应用2：中缀表达式转后缀逆波兰；运算符栈比较优先级，高优先级先出栈输出。', '括号不提升优先级；运算符出栈顺序颠倒。', '中缀转后缀,逆波兰,运算符栈,优先级比较', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈和队列的应用', 0),
  (32, '数据结构', '栈、队列和数组', '数据结构', 3, '栈应用3：递归模拟；系统栈保存每层局部变量与返回地址，递归深度过大栈溢出，迭代手动栈规避溢出。', '递归无空间开销；迭代无需保存现场。', '递归系统栈,栈溢出,递归转迭代', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈和队列的应用', 0),
  (33, '数据结构', '栈、队列和数组', '数据结构', 3, '队列核心应用：广度优先BFS层序遍历树、图；逐层入队出队，保证按层次顺序访问。', '层序遍历使用栈；无法区分每层边界。', 'BFS层序遍历,队列分层,树图遍历', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '栈和队列的应用', 0),
  (34, '数据结构', '栈、队列和数组', '数据结构', 3, '多维数组逻辑多维、物理一维连续存储；C语言默认行优先存储，先存完一行再下一行。', '多维数组物理多维排布；混淆行列优先。', '二维数组,行优先,物理连续存储', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数组和特殊矩阵', 0),
  (35, '数据结构', '栈、队列和数组', '数据结构', 3, '对称矩阵仅存储下三角，a[i][j]=a[j][i]，压缩一维数组映射下标，节省一半空间。', '对称矩阵完整存储全部元素；下标换算公式错误。', '对称矩阵,压缩存储,下三角映射', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数组和特殊矩阵', 0),
  (36, '数据结构', '栈、队列和数组', '数据结构', 3, '稀疏矩阵零元素占绝大多数，采用三元组(行,列,值)顺序表存储，节省大量空白空间。', '三元组支持O(1)随机存取；转置不重排三元组。', '稀疏矩阵,三元组表,矩阵转置', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '数组和特殊矩阵', 0),
  (37, '数据结构', '串', '数据结构', 3, '串是零个或多个字符组成有限序列；空串长度为0，不含任何字符；空白串仅包含空格，与空串完全不同。', '空白串等于空串；空串长度记为1。', '串,空串,空白串,字符序列', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '串的定义和实现', 0),
  (38, '数据结构', '串', '数据结构', 3, '子串是串中连续字符片段；子序列字符可不连续；截取子串SubString操作需要判定起止下标边界。', '子串等同于子序列；截取下标越界不处理。', '子串,子序列,SubString截取', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '串的定义和实现', 0),
  (39, '数据结构', '串', '数据结构', 3, '朴素BF暴力匹配双重循环，主串i、模式串j；匹配失败i=i-j+1，j归零，最坏复杂度O(n*m)。', '匹配失败i直接自增1；j不重置从头比较。', 'BF暴力匹配,双重循环,最坏复杂度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '串的模式匹配', 0),
  (40, '数据结构', '串', '数据结构', 3, 'KMP算法预处理next数组，记录模式串最长相等前后缀；匹配失败j=next[j]，主串i不回退，线性O(n+m)。', 'KMP主指针后退；next数组存储后缀长度。', 'KMP,next数组,最长相等前后缀,无回退匹配', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '串的模式匹配', 0),
  (41, '数据结构', '串', '数据结构', 3, 'nextval优化数组消除无效跳转；若pattern[j]==pattern[next[j]]，令nextval[j]=nextval[next[j]]，减少匹配次数。', 'nextval直接复制next；相同字符不递归修正。', 'nextval数组,KMP优化,无效跳转消除', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '串的模式匹配', 0),
  (42, '数据结构', '树与二叉树', '数据结构', 3, '树递归定义：n≥0节点有限集合，n=0为空树；唯一根节点，各子树互不相交。', '空树存在根；子树允许相交重叠。', '树,空树,根节点,互不相交子树', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树的基本概念', 0),
  (43, '数据结构', '树与二叉树', '数据结构', 3, '节点度为子节点数量；叶子节点度0；树度为全部节点最大度数；握手定理：总度数=节点数-1。', '总度数等于节点数；叶子存在子节点。', '节点度,叶子节点,树度,握手定理', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树的基本概念', 0),
  (44, '数据结构', '树与二叉树', '数据结构', 3, '二叉树是度≤2的有序树，严格区分左、右孩子；五种基础形态：空、单根、仅左、仅右、左右双全。', '二叉树度固定为2；左右子树无顺序。', '二叉树,有序树,左孩子右孩子,五种形态', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的概念', 0),
  (45, '数据结构', '树与二叉树', '数据结构', 3, '满二叉树每一层节点全部填满；完全二叉树从上到下、从左到右连续填充，无空缺；完全二叉树叶子仅出现在最下层、次下层。', '完全二叉树中间可空缺；满二叉树存在单层缺失。', '满二叉树,完全二叉树,连续填充', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的概念', 0),
  (46, '数据结构', '树与二叉树', '数据结构', 3, '二叉树核心性质：叶子节点数n0 = 度为2节点数n2 + 1；任意高度h二叉树最少h个节点，最多2^h -1。', 'n0=n2；高度h最多h节点。', 'n0=n2+1,二叉树节点性质,最大最小节点数', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的概念', 0),
  (47, '数据结构', '树与二叉树', '数据结构', 3, '前序遍历：根→左→右；中序遍历：左→根→右；后序遍历：左→右→根；三种递归遍历逻辑清晰。', '后序先访问根；遍历顺序颠倒。', '前序,中序,后序,递归遍历', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的遍历', 0),
  (48, '数据结构', '树与二叉树', '数据结构', 3, '非递归栈实现中序遍历；先一路入栈左分支，出栈访问，再处理右子树，无需递归调用。', '非递归先访问根再入栈；栈操作顺序混乱。', '中序非递归,辅助栈,左分支入栈', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的遍历', 0),
  (49, '数据结构', '树与二叉树', '数据结构', 3, '层序遍历依靠队列；根入队，循环出队访问，依次将左右孩子入队，实现按层次从上到下、从左到右输出。', '层序使用栈；无法区分每层节点。', '层序遍历,队列,BFS,分层输出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '二叉树的遍历', 0),
  (50, '数据结构', '树与二叉树', '数据结构', 3, '线索二叉树利用叶子空指针存储遍历前驱、后继；ltag=0代表左孩子，1代表前驱线索；rtag=0右孩子，1后继线索。', '线索覆盖有效孩子指针；tag标记含义记反。', '线索二叉树,ltag,rtag,前驱后继线索', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '线索二叉树', 0),
  (51, '数据结构', '树与二叉树', '数据结构', 3, '树采用孩子兄弟表示法转二叉树：左指针存第一个子节点，右指针存右侧兄弟节点。', '左兄弟右孩子；转换指针分配颠倒。', '左孩子右兄弟,树转二叉树', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树、森林', 0),
  (52, '数据结构', '树与二叉树', '数据结构', 3, '多棵森林转二叉树：每棵树根作为前一棵树的右子树，整体合并为单棵二叉树。', '各树根作为左子树；丢失多棵树连接关系。', '森林转二叉树,根节点右链', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树、森林', 0),
  (53, '数据结构', '树与二叉树', '数据结构', 3, '哈夫曼树构造：每次选取两个权值最小节点合并生成新父节点，父权值等于两子权之和。', '一次选三个节点合并；哈夫曼存在度2叶子。', '哈夫曼树,最小权合并,WPL带权路径长度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树与二叉树的应用', 0),
  (54, '数据结构', '树与二叉树', '数据结构', 3, '并查集用于判断连通分量；Find查找根节点，路径压缩优化；Union合并集合，按秩合并控制树高度。', 'Find不做路径压缩；合并直接覆盖根。', '并查集,Find,Union,路径压缩,按秩合并', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树与二叉树的应用', 0),
  (55, '数据结构', '图', '数据结构', 3, '图G=(V,E)，V顶点集，E边集；无向边(u,v)双向等价，有向边<u,v>单向不可反向。', '有向边无方向；无向图边有序。', '图,顶点集,边集,无向边,有向边', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的基本概念', 0),
  (56, '数据结构', '图', '数据结构', 3, '握手定理：无向图总度数等于边数两倍；有向图总入度+总出度=2|E|。', '有向图总度数等于边数；忽略入度出度分开统计。', '握手定理,入度,出度,总度数', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的基本概念', 0),
  (57, '数据结构', '图', '数据结构', 3, '邻接矩阵n阶方阵，稠密图最优；判定两点边O(1)，空间复杂度O(n²)。', '邻接矩阵适合稀疏图；无向矩阵不对称。', '邻接矩阵,稠密图,常数查询', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的存储及基本操作', 0),
  (58, '数据结构', '图', '数据结构', 3, '邻接表顶点数组搭配单链表；稀疏图节省空间；无向图每条边存储两次，有向仅存出边。', '有向邻接表可快速查入度；无向边只存一份。', '邻接表,稀疏图,出边链表', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的存储及基本操作', 0),
  (59, '数据结构', '图', '数据结构', 3, 'BFS广度优先队列实现，逐层扩散，可求解无权图两点最短路径。', 'BFS用于加权最短路径；遍历不标记visited。', 'BFS,无权最短路径,队列遍历', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的遍历', 0),
  (60, '数据结构', '图', '数据结构', 3, 'DFS深度优先递归遍历，一路走到最深叶子再回溯，可检测图中环路。', 'DFS逐层扩展；环路判定无递归栈标记。', 'DFS,深度优先,环路检测,递归回溯', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的遍历', 0),
  (61, '数据结构', '图', '数据结构', 3, '最小生成树MST：无向连通加权图，Prim稠密图、Kruskal稀疏并查集实现，总权值最小无环。', '有向图存在MST；Kruskal按顶点扩展。', '最小生成树,Prim,Kruskal,并查集', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的应用', 0),
  (62, '数据结构', '图', '数据结构', 3, 'Dijkstra单源最短路径，禁止负权边；每次选取当前距离最小未访问顶点松弛更新。', 'Dijkstra处理负权；松弛操作顺序颠倒。', 'Dijkstra,单源最短路径,负权禁止,松弛', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的应用', 0),
  (63, '数据结构', '图', '数据结构', 3, 'Floyd多源最短路径动态规划，允许负权，不可存在负环；三层循环k中间节点、i起点、j终点。', '循环顺序i,j,k；负环下结果有效。', 'Floyd,多源DP,负权无负环', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的应用', 0),
  (64, '数据结构', '图', '数据结构', 3, '拓扑排序AOV网，入度零顶点入队；有环图无合法拓扑序列，用于判断活动先后约束。', '有环图存在拓扑；边代表活动顶点代表约束。', '拓扑排序,AOV网,入度队列,环路判定', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的应用', 0),
  (65, '数据结构', '图', '数据结构', 3, 'AOE网关键路径，ve事件最早、vl事件最迟；ee活动最早、el活动最迟，ee==el为关键活动。', 'AOV与AOE混淆；ve、vl计算顺序颠倒。', 'AOE,关键路径,ve vl ee el,总工期', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '图的应用', 0),
  (66, '数据结构', '查找', '数据结构', 3, '静态查找表运行过程数据不增删；动态查找表支持插入删除操作；平均查找长度AS衡量查找效率。', '静态表可动态插入；AS只计算成功查找。', '静态查找,动态查找,ASL平均查找长度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '查找的基本概念', 0),
  (67, '数据结构', '查找', '数据结构', 3, '顺序查找适配无序、有序表、链表；成功ASL=(n+1)/2，失败ASL=n+1；哨兵优化省去边界判断。', '有序表失败可提前终止计算ASL错误。', '顺序查找,哨兵,成功失败ASL', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序查找和折半查找', 0),
  (68, '数据结构', '查找', '数据结构', 3, '折半二分查找仅有序连续顺序表可用；mid=(low+high)//2，判定树平衡二叉树，失败落在叶子外侧。', '链表支持二分；mid溢出不处理。', '二分查找,有序顺序表,判定树', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '顺序查找和折半查找', 0),
  (69, '数据结构', '查找', '数据结构', 3, '二叉搜索树BST：左子全部关键字<根，右子全部>根；中序遍历升序有序。', '左右大小规则颠倒；中序降序。', 'BST二叉搜索树,中序升序', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树型查找', 0),
  (70, '数据结构', '查找', '数据结构', 3, 'AVL平衡二叉树，左右子树高度差绝对值≤1；LL、LR、RL、RR四种旋转平衡。', '旋转后不更新高度；平衡因子绝对值大于1仍合法。', 'AVL,平衡因子,四种旋转', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '树型查找', 0),
  (71, '数据结构', '查找', '数据结构', 3, '哈希函数映射关键字到数组下标；装填因子α=记录数/表长，α越大冲突越多。', '哈希无冲突；α越大查找越快。', '散列表,哈希函数,装填因子,冲突', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '散列查找', 0),
  (72, '数据结构', '查找', '数据结构', 3, '冲突解决两种主流方案：开放寻址法（线性探测、二次探测）、链地址法（同哈希值挂链表）。', '开放寻址直接删除节点；链地址装填因子无上限。', '开放寻址,线性探测,链地址法', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '散列查找', 0),
  (73, '数据结构', '排序', '数据结构', 3, '稳定排序相等元素相对位置不变；不稳定会交换相等元素位置；内部排序全部数据载入内存，外部排序依赖磁盘。', '稳定排序效率一定更高；海量数据用内排序。', '稳定排序,内部排序,外部排序', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '排序的基本概念', 0),
  (74, '数据结构', '排序', '数据结构', 3, '简单排序：直接插入、冒泡、简单选择，最坏O(n²)；插入、冒泡稳定，简单选择不稳定。', '简单选择稳定；冒泡有序不优化循环。', '插入排序,冒泡,简单选择,O(n²)', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '内部排序', 0),
  (75, '数据结构', '排序', '数据结构', 3, '高效排序：希尔、快速、堆、归并，平均O(nlogn)；归并稳定，快排、堆排、希尔不稳定。', '快速排序稳定；归并原地无辅助数组。', '快速排序,归并排序,堆排序,希尔,nlogn', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '内部排序', 0),
  (76, '数据结构', '排序', '数据结构', 3, '海量数据分块生成归并段；多路平衡归并减少磁盘IO；败者树优化多路选取最小值。', '外部排序一次性读入全部数据；多路无需败者树。', '多路归并,归并段,败者树,磁盘IO优化', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 1, NULL, '外部排序', 0),
  (77, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '计算机发展按照核心硬件划分为四代：电子管、晶体管、中小规模集成电路、超大规模集成电路；软件同步伴随硬件迭代发展，从机器语言逐步演进至高级语言、系统软件。本节带*标记，统考大纲已删除，仅拓展学习。', '混淆四代计算机核心元器件；认为软件发展独立于硬件迭代。', '计算机四代发展,电子管,晶体管,集成电路,软硬件发展历程', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机发展历程', 0),
  (78, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '完整计算机系统分为硬件与软件两大组成部分；硬件是底层物理载体，软件分为系统软件、应用软件；软硬件存在逻辑等价性，同一功能可由硬件或软件实现。', '系统软件等同于应用软件；认为软硬件功能完全不可互相替代。', '计算机系统组成,硬件,系统软件,应用软件,软硬件等价性', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机系统层次结构', 0),
  (79, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '计算机硬件五大核心部件：运算器、控制器、存储器、输入设备、输出设备；运算器+控制器整合为CPU，主机包含CPU+主存，外设为IO设备。', 'CPU包含存储器；主机包含外部IO外设。', '五大硬件部件,CPU,运算器,控制器,主机,外设', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机系统层次结构', 0),
  (80, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '软件分层：机器语言、汇编语言、操作系统、高级语言、应用程序；层次自上而下逐层封装，上层屏蔽底层硬件细节。', '汇编语言运行无需翻译；高级语言可直接在裸机运行。', '软件层次,机器语言,汇编,操作系统,高级语言,分层封装', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机系统层次结构', 0),
  (81, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '计算机系统分为普通用户、系统程序员、机器语言程序员、硬件设计者四类用户，不同用户看到的计算机抽象层次完全不同。', '所有用户视角的计算机结构完全一致；混淆程序员与硬件设计者层级。', '计算机不同用户,用户分层,硬件抽象视角', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机系统层次结构', 0),
  (82, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '计算机整机工作原理：取指周期、执行周期循环往复；CPU从主存读取指令，译码后控制运算器、存储器、IO协同完成运算与数据交互。', '指令直接存放在CPU寄存器永久保存；取指与执行阶段无固定循环流程。', '计算机工作原理,取指周期,执行周期,指令循环执行', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机系统层次结构', 0),
  (83, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '计算机核心性能指标：字长、主频、CPI、CPU执行时间、MIPS、FLOPS、存储容量；字长决定单次运算数据宽度，主频代表时钟脉冲频率。', '主频越高计算机性能一定更强；混淆CPI、MIPS计算公式。', '性能指标,字长,主频,CPI,MIPS,FLOPS,执行时间', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机的性能指标', 0),
  (84, '计算机组成原理', '计算机系统概述', '计算机组成原理', 3, '存储容量单位换算：1B=8bit，1KB=2^10B，1MB=2^20B，1GB=2^30B；厂商十进制1KB=1000B，计算机二进制标准二者区分。', '存储容量全部按十进制1000换算；bit与Byte单位混用。', '存储单位换算,二进制容量,bit字节,KB MB GB', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '计算机的性能指标', 0),
  (85, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '进位计数制包含二进制、八进制、十进制、十六进制；进制转换规则：任意进制转十进制按权展开，十进制转R进制除基取余/乘基取整，二八十六进制直接分组映射。', '小数进制转换误用除基取余；二进制转十六进制分组方向颠倒。', '进制转换,按权展开,除基取余,二八十六进制互转', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数制与编码', 0),
  (86, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '定点数分为定点整数、定点小数；四种编码：原码、反码、补码、移码；补码是计算机实际存储运算编码，解决正负0二义性问题。', '原码适合加减运算；移码符号位规则与补码混淆。', '定点数,原码,反码,补码,移码,正负零编码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数制与编码', 0),
  (87, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '整数编码规则：n位二进制，原码表示范围-(2^{n-1}-1)~2^{n-1}-1；补码表示范围-2^{n-1}~2^{n-1}-1，多一个负数极小值。', '补码与原码数值表示范围完全相同；n位补码最大值计算错误。', '整数补码范围,原码范围,二进制位数表示极限', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数制与编码', 0),
  (88, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, 'C语言整数类型char(8bit)、short(16bit)、int(32bit)、long long(64bit)；有符号/无符号类型转换时高位扩展规则不同，存在溢出风险。', '无符号数负数赋值自动截断无溢出；符号扩展零扩展规则混用。', 'C语言整数类型,有符号无符号转换,符号扩展,数据溢出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数制与编码', 0),
  (89, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '基本运算部件为ALU算术逻辑单元，核心由全加器组成；一位全加器包含本位和、进位输出，多位ALU分为串行进位、并行进位（先行进位）两种结构。', '串行进位运算速度快于先行进位；ALU仅支持算术运算。', 'ALU运算部件,全加器,串行进位,先行进位,算术逻辑运算', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '运算方法和运算电路', 0),
  (90, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '定点数移位运算：算术移位、逻辑移位、循环移位；正数算术移位补0，负数原码补0、反码补1、补码符号不变数值补1。', '负数补码算术右移高位补0；逻辑移位区分正负符号。', '算术移位,逻辑移位,循环移位,负数补码移位规则', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '运算方法和运算电路', 0),
  (91, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '定点加减法采用补码运算，符号位一同参与运算；双符号位法、单符号位法检测溢出，最高位进位与符号进位不同则溢出。', '原码直接做加减运算；溢出判定只看数值位进位。', '补码加减运算,溢出检测,双符号位,进位溢出判断', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '运算方法和运算电路', 0),
  (92, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '定点乘除运算：原码一位乘、补码Booth乘法；原码恢复余数除法、不恢复余数除法；乘法右移累加，除法左移减除数。', 'Booth乘法不处理负乘数；除法减法判断余数符号逻辑颠倒。', 'Booth补码乘法,原码一位乘,恢复余数除法,不恢复余数除法', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '运算方法和运算电路', 0),
  (93, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, 'IEEE754浮点标准分为符号位S、阶码E、尾数M；单精度32位(1+8+23)，双精度64位(1+11+52)；阶码采用移码偏移存储，尾数隐含整数1。', '浮点尾数开头需要显式写1；阶码直接用补码不偏移。', 'IEEE754,单精度浮点数,双精度,阶码偏移,隐含尾数1', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '浮点数的表示与运算', 0),
  (94, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '浮点加减运算五步：对阶、尾数加减、规格化、舍入、溢出判断；对阶小阶向大阶看齐，尾数右移；规格化保证尾数最高位为1。', '对阶大阶向小阶移位；规格化左移右移场景混淆。', '浮点加减五步,对阶,规格化,舍入操作,浮点溢出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '浮点数的表示与运算', 0),
  (95, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, 'C语言float对应单精度IEEE754，double对应双精度；float转double无精度丢失，double转float截断尾数产生精度损失。', '浮点类型互相转换无精度损耗；float阶码偏移量计算错误。', 'float double类型,浮点类型转换,精度丢失,阶码偏移值', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '浮点数的表示与运算', 0),
  (96, '计算机组成原理', '数据的表示和运算', '计算机组成原理', 3, '数据宽度指数据二进制位数，存储大小对齐规则：基本数据类型按自身宽度对齐，结构体补齐空白字节保证访问效率。', '内存存储无需对齐；结构体填充字节不占用存储空间。', '数据宽度,内存对齐,结构体填充,存储对齐规则', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '浮点数的表示与运算', 0),
  (97, '计算机组成原理', '存储系统', '计算机组成原理', 3, '存储器分类：按存储介质半导体/磁介质；按读写特性RAM随机读写、ROM只读；按层次高速缓存Cache、主存、辅存三级存储层次。', 'ROM可随机写入修改；Cache属于外部辅存。', '存储器分类,RAM ROM,三级存储层次,半导体磁存储器', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '存储器概述', 0),
  (98, '计算机组成原理', '存储系统', '计算机组成原理', 3, '主存由存储体、地址译码器、读写驱动电路、控制电路组成；基础操作：读操作根据地址取数据，写操作将数据存入指定存储单元。', '地址译码器用于数据传输；读写操作共用单向数据线。', '主存组成,存储体,地址译码,主存读写操作', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '存储器概述', 0),
  (99, '计算机组成原理', '存储系统', '计算机组成原理', 3, '存储器层次化结构：CPU寄存器→Cache→主存→本地磁盘→远程存储；速度逐级递减、容量逐级增大、单位成本逐级降低，依靠局部性原理维系效率。', '大容量存储速度更快；存储层次无局部性支撑。', '存储层次结构,速度容量成本权衡,局部性原理铺垫', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '存储器概述', 0),
  (100, '计算机组成原理', '存储系统', '计算机组成原理', 3, '存储器核心性能指标：存储容量、存取周期、存取速度、带宽；存取周期是连续两次读写最小间隔，大于单次访问时间。', '存取周期等于单次访问延迟；带宽与存取周期无关联。', '存储器性能指标,存取周期,存储带宽,容量速度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '存储器概述', 0);
INSERT INTO `knowledge_point` (`id`, `subject`, `name`, `parent_name`, `level`, `content`, `common_mistakes`, `keywords`, `is_high_frequency`, `create_time`, `update_time`, `subject_id`, `parent_id`, `section`, `is_deleted`) VALUES
  (101, '计算机组成原理', '存储系统', '计算机组成原理', 3, '半导体随机存取存储器RAM分为SRAM静态、DRAM动态；SRAM无需刷新、速度快用于Cache；DRAM电容存储电荷，定期刷新，成本低做主存。', 'DRAM无需刷新；SRAM大容量做主存。', 'SRAM DRAM,静态动态RAM,刷新操作,存储介质用途', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '主存储器', 0),
  (102, '计算机组成原理', '存储系统', '计算机组成原理', 3, '非易失性存储器ROM：掩膜ROM、PROM、EPROM、EEPROM、Flash闪存；断电数据不丢失，用于固件、BIOS、固态硬盘。', '普通RAM断电数据保留；Flash不可多次擦写。', 'ROM分类,Flash闪存,非易失存储,断电持久保存', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '主存储器', 0),
  (103, '计算机组成原理', '存储系统', '计算机组成原理', 3, '多模块存储器：单体多字、多体并行交叉存储器；多体分时并行存取，提升主存带宽，解决CPU与主存速度不匹配问题。', '单体多字并行访问效率高于多体交叉；多体模块无地址交叉规则。', '多体并行存储器,单体多字,交叉编址,主存带宽提升', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '主存储器', 0),
  (104, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'CPU与主存连接三大总线：地址总线单向传输地址、数据总线双向传输读写数据、控制总线传输读写/刷新/片选控制信号。', '地址总线双向传输；控制总线仅单一控制信号。', 'CPU主存连接,地址总线,数据总线,控制总线,片选信号', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '主存储器与CPU的连接', 0),
  (105, '计算机组成原理', '存储系统', '计算机组成原理', 3, '主存容量扩展分为位扩展、字扩展、字位同时扩展；位扩展增加存储字长，字扩展增加存储单元数量，依靠片选译码区分存储芯片。', '位扩展增加存储单元个数；字扩展增加单字bit宽度。', '主存容量扩展,位扩展,字扩展,字位扩展,片选译码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '主存储器与CPU的连接', 0),
  (106, '计算机组成原理', '存储系统', '计算机组成原理', 3, '磁盘存储器硬件组成：盘片、磁头、盘轴、读写控制；磁道、扇区、柱面寻址；磁盘存取时间=寻道时间+旋转延迟+传输时间。', '柱面为同一盘面磁道；存取时间仅计算数据传输耗时。', '磁盘存储器,磁道扇区柱面,寻道时间,旋转延迟,磁盘带宽', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '外部存储器', 0),
  (107, '计算机组成原理', '存储系统', '计算机组成原理', 3, '固态硬盘SSD基于NAND Flash闪存，无机械磁头，随机读写速度远高于磁盘；按页擦写，块为最小擦除单位，存在磨损均衡机制。', 'SSD存在寻道旋转延迟；闪存可单字节擦除。', 'SSD固态硬盘,NAND Flash,页块擦写,磨损均衡,无机械延迟', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '外部存储器', 0),
  (108, '计算机组成原理', '存储系统', '计算机组成原理', 3, '程序局部性原理分为时间局部性、空间局部性；时间局部性近期访问指令数据短期内重复访问；空间局部性相邻地址数据会连续访问，是Cache存在理论基础。', 'Cache无局部性也可提升速度；混淆时间/空间局部性场景。', '局部性原理,时间局部性,空间局部性,Cache理论依据', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (109, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache工作原理：CPU访问数据先查Cache，命中直接读取；未命中访问主存并将对应主存块调入Cache块；Cache块与主存块大小完全相等。', 'Cache块大小可自由设置与主存块无关；缺失时不加载完整主存块。', 'Cache基本原理,命中缺失,主存块Cache块,块调入机制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (110, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache与主存三种映射方式：直接映射、全相联映射、组相联映射；直接映射硬件简单冲突高；全相联无冲突成本高；组相联折中方案统考重点。', '直接映射主存块可存入任意Cache块；组相联分组规则颠倒。', 'Cache映射方式,直接映射,全相联,组相联,标记索引块内偏移', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (111, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache块替换算法：随机替换、先进先出FIFO、最近最少使用LRU；LRU淘汰最长时间未访问块，命中率最优，组相联Cache标配算法。', 'FIFO不会产生Belady异常；LRU按访问先后直接淘汰最早块。', 'Cache替换算法,LRU,FIFO,Belady异常,随机替换', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (112, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache一致性问题：多核CPU多Cache副本数据不一致；解决方案：写直达、写回、标记修改、无效化协议，区分单核对多核场景。', '单核CPU存在Cache一致性问题；写回无需修改主存。', 'Cache一致性,写直达,写回法,多核缓存副本,无效协议', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (113, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache容量计算题拆分地址位：主存总标记位、组索引位、块内偏移位；计算Cache行数、每组块数、命中率、平均访问时间。', '地址三段位分配计算混淆；平均访问时间忽略缺失惩罚延迟。', 'Cache容量计算,地址分段,命中率,平均访问时间推导', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (114, '计算机组成原理', '存储系统', '计算机组成原理', 3, 'Cache多级分层：L1私有Cache、L2私有、L3共享Cache；多级Cache全局命中率逐级提升，访问延迟逐级增大。', '多级Cache总命中率低于单级；L3延迟低于L1。', '多级Cache,L1 L2 L3缓存,私有共享缓存,全局命中率', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '高速缓冲存储器', 0),
  (115, '计算机组成原理', '存储系统', '计算机组成原理', 3, '虚拟存储器依靠操作系统+主存+辅存，为程序提供超大逻辑地址空间；逻辑地址与物理地址隔离，缺页时从磁盘调入主存页面。', '虚拟地址直接对应磁盘物理地址；无操作系统也可实现虚拟存储。', '虚拟存储器,逻辑地址,物理地址,缺页中断,磁盘页面调入', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '虚拟存储器', 0),
  (116, '计算机组成原理', '存储系统', '计算机组成原理', 3, '页式虚拟存储器：逻辑地址拆分为虚拟页号+页内偏移；页表存储虚拟页到物理页映射，存在页表高速缓存TLB快表加速地址转换。', '页内偏移参与页表索引；TLB存放完整页表全部条目。', '页式虚拟存储,页表,TLB快表,虚拟页物理页,地址转换', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '虚拟存储器', 0),
  (117, '计算机组成原理', '存储系统', '计算机组成原理', 3, '段式虚拟存储器按程序逻辑段划分地址空间，段表存放段基址、段限长；分段便于程序共享、保护，存在外部碎片。', '段内地址无长度限制；分段无内存碎片问题。', '段式虚拟存储,段表,段基址,段限长,外部碎片,程序共享', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '虚拟存储器', 0),
  (118, '计算机组成原理', '存储系统', '计算机组成原理', 3, '段页式虚拟存储先分段、段内分页；结合分段共享保护、分页无外部碎片优势；两级页表结构，地址转换流程更长。', '段页式只有一级地址映射；分页存在外部碎片。', '段页式虚拟存储,两级地址转换,分段分页结合,内部碎片', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '虚拟存储器', 0),
  (119, '计算机组成原理', '存储系统', '计算机组成原理', 3, '虚拟存储器与Cache对比：Cache硬件自动管理，虚拟存储操作系统软件管理；Cache缺失访问主存，虚拟缺页访问低速磁盘，缺失代价差距极大。', 'Cache与虚拟存储管理层级一致；二者缺失延迟代价相近。', '虚拟存储Cache对比,软硬件管理,缺失代价,主存磁盘速度差', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '虚拟存储器', 0),
  (120, '计算机组成原理', '指令系统', '计算机组成原理', 3, '指令集体系结构ISA定义程序员可见硬件抽象，包含寄存器、指令格式、寻址方式、数据类型；分为CISC复杂指令集、RISC精简指令集两大体系。', 'ISA包含CPU内部ALU微电路细节；RISC指令数量更多。', 'ISA指令集体系,程序员抽象层,CISC RISC分类', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令集体系结构', 0),
  (121, '计算机组成原理', '指令系统', '计算机组成原理', 3, '指令由操作码OP、地址码A组成；操作码标识运算功能，地址码存放操作数/操作数地址；指令长度分为定长指令、变长扩展指令。', '地址码只能存放数据本身；操作码长度不可扩展。', '指令基本格式,操作码OP,地址码A,指令长度分类', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令集体系结构', 0),
  (122, '计算机组成原理', '指令系统', '计算机组成原理', 3, '定长操作码所有指令OP位数完全一致，译码简单、指令数量上限固定；硬件实现简单，RISC架构主流采用。', '定长操作码可无限扩展指令种类；译码流程复杂。', '定长操作码,固定OP位数,RISC指令格式,硬件快速译码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令集体系结构', 0),
  (123, '计算机组成原理', '指令系统', '计算机组成原理', 3, '扩展操作码（变长OP）短指令OP短，长指令复用高位拓展操作码，指令数量灵活；译码多级拆分，CISC架构广泛使用。', '扩展操作码短指令高位不可复用；所有指令OP长度相同。', '扩展操作码,变长OP,CISC指令,指令数量灵活扩展', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令集体系结构', 0),
  (124, '计算机组成原理', '指令系统', '计算机组成原理', 3, '指令按功能划分：数据传送、算术运算、逻辑运算、移位、转移、IO、停机指令；转移指令改变PC程序计数器顺序执行流程。', '算术指令不修改程序计数器；IO指令直接访问外设无需接口。', '指令功能分类,转移指令,PC程序计数器,数据传送指令', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令集体系结构', 0),
  (125, '计算机组成原理', '指令系统', '计算机组成原理', 3, '寻址分为指令寻址、数据寻址；指令寻址修改PC实现顺序/跳跃执行；数据寻址获取运算操作数真实物理地址。', '两种寻址逻辑完全一致；指令寻址无需修改PC。', '指令寻址,数据寻址,PC程序计数器,操作数地址解析', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '寻址方式', 0),
  (126, '计算机组成原理', '指令系统', '计算机组成原理', 3, '常见数据寻址方式：立即寻址、直接寻址、间接寻址、寄存器寻址、寄存器间接、相对寻址、基址、变址、堆栈寻址；不同寻址有效地址EA计算公式不同。', '间接寻址EA等于指令地址码；相对寻址偏移量无符号限制。', '九种寻址方式,有效地址EA,寄存器寻址,相对基址变址', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '寻址方式', 0),
  (127, '计算机组成原理', '指令系统', '计算机组成原理', 3, '汇编基础指令：数据mov传送、add/sub算术、and/or/xor逻辑、jmp/jz跳转、call/ret过程调用；寄存器直接作为操作数，访存指令带括号地址。', '汇编mov指令两个操作数不可同时为内存；跳转指令修改通用寄存器。', '汇编基础指令,mov加减逻辑指令,跳转调用返回指令', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '程序的机器级代码表示', 0),
  (128, '计算机组成原理', '指令系统', '计算机组成原理', 3, 'if选择语句机器级依靠条件跳转指令实现；比较cmp设置状态标志位，根据ZF/SF/CF判断分支走向。', '分支判断直接比较数据不设置标志位；条件跳转修改数据寄存器。', '选择语句机器码,cmp比较指令,状态标志位,条件跳转', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '程序的机器级代码表示', 0),
  (129, '计算机组成原理', '指令系统', '计算机组成原理', 3, '循环语句机器级两种实现：先判断后执行、先执行后判断；依靠跳转指令循环回跳，循环终止条件检测标志位。', '循环指令无状态标志判断；回跳地址计算错误。', '循环机器代码,循环回跳,终止条件标志位', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '程序的机器级代码表示', 0),
  (130, '计算机组成原理', '指令系统', '计算机组成原理', 3, '过程调用call指令保存返回地址入栈，修改PC跳转子程序；ret弹出栈中返回地址恢复PC；栈帧存放局部变量、参数、保存寄存器。', 'call不保存返回地址；栈帧分配无栈指针调整。', '过程调用call ret,栈帧结构,返回地址堆栈保存', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '程序的机器级代码表示', 0),
  (131, '计算机组成原理', '指令系统', '计算机组成原理', 3, 'CISC复杂指令集：指令数量多、变长指令、多种寻址、微程序控制器，单指令完成复杂功能，代表x86架构。', 'CISC指令定长；硬件硬布线控制CISC。', 'CISC复杂指令集,x86,变长操作码,微程序控制器,多寻址', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'CISC和RISC的基本概念', 0),
  (132, '计算机组成原理', '指令系统', '计算机组成原理', 3, 'RISC精简指令集：指令数量少、定长指令、寻址方式简单、硬布线控制器，单指令功能单一，依靠流水线提升性能，代表ARM、MIPS。', 'RISC指令功能复杂；变长操作码适配RISC。', 'RISC精简指令集,MIPS ARM,定长指令,硬布线控制,流水线优化', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'CISC和RISC的基本概念', 0),
  (133, '计算机组成原理', '指令系统', '计算机组成原理', 3, 'CISC与RISC核心对比：指令长度、操作码、寻址、控制器、流水线、指令数量、单指令复杂度七大维度，是选择题高频辨析考点。', '混淆二者控制器类型、指令长度规则。', 'CISC RISC对比表,架构辨析,流水线适配差异', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'CISC和RISC的基本概念', 0),
  (134, '计算机组成原理', '中央处理器', '计算机组成原理', 3, 'CPU四大核心功能：取指令、指令译码、执行运算、控制IO与中断；整机运算与控制核心，分为运算器ALU、控制器CU两大部件。', '存储器属于CPU内部部件；IO控制不属于CPU功能。', 'CPU四大功能,运算器ALU,控制器CU,取指执行控制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'CPU的功能和基本结构', 0),
  (135, '计算机组成原理', '中央处理器', '计算机组成原理', 3, 'CPU内部寄存器分类：用户可见通用寄存器、程序计数器PC、指令寄存器IR、程序状态字PSW、MAR存储器地址寄存器、MDR存储器数据寄存器。', 'IR存放操作数；PC存放当前执行指令。', 'CPU寄存器分类,PC IR PSW MAR MDR,通用寄存器', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'CPU的功能和基本结构', 0),
  (136, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '指令执行通用两大阶段：取指周期、执行周期；取指公共流程固定，执行周期随指令操作码不同逻辑不同。', '每条指令取指流程完全不同；执行周期不访问主存。', '指令执行两阶段,取指周期,执行周期,公共取指流程', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令执行过程', 0),
  (137, '计算机组成原理', '中央处理器', '计算机组成原理', 3, 'CPU时序控制：时钟脉冲节拍、机器周期、指令周期；一个指令周期包含若干机器周期，一个机器周期包含多个时钟节拍。', '指令周期等于机器周期；时钟节拍独立无同步约束。', '时序控制,时钟节拍,机器周期,指令周期分层', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令执行过程', 0),
  (138, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '处理器指令执行模型分为单周期CPU、多周期CPU；单周期全指令同一时钟周期完成，硬件冗余；多周期拆分机器周期节省硬件资源。', '单周期CPU时钟周期更短；多周期每条指令周期数量固定。', '单周期多周期CPU,指令执行模型,机器周期拆分', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令执行过程', 0),
  (139, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '数据通路功能：传输运算数据、连接寄存器与ALU；控制器发送控制信号选通通路，决定数据传输方向与运算操作。', '数据通路产生控制信号；ALU独立于数据通路。', '数据通路功能,ALU运算通路,控制信号选通传输', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数据通路的功能和基本结构', 0),
  (140, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '数据通路硬件组成：通用寄存器、MAR/MDR、PC、IR、ALU、多路选择器、内部总线；全部寄存器共享通路完成数据交互。', '程序计数器PC不属于数据通路部件；多路选择器无选通控制。', '数据通路组成,内部总线,多路选择器,寄存器阵列', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数据通路的功能和基本结构', 0),
  (141, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '数据通路分为单总线结构、专用分离通路；单总线所有寄存器分时共享一条内部总线，硬件简单传输冲突；专用通路并行传输速度快硬件成本高。', '单总线同一周期多组数据并行传输；专用通路存在总线竞争。', '单总线数据通路,专用通路,总线竞争,并行传输', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '数据通路的功能和基本结构', 0),
  (142, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '控制器CU核心功能：取指令、译码生成微操作控制信号、同步时序节拍、处理中断异常；整机所有硬件操作由控制器统一调度。', '运算器自主生成控制信号；时序节拍不由控制器产生。', '控制器CU功能,微操作控制信号,时序同步,指令译码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '控制器的功能和工作原理', 0),
  (143, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '硬布线控制器（组合逻辑控制器）：操作码直接组合逻辑生成控制信号；速度快、复杂指令修改困难，适配RISC定长指令集。', '硬布线依靠微存储单元；修改指令无需重设计逻辑电路。', '硬布线控制器,组合逻辑电路,RISC适配,高速控制信号', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '控制器的功能和工作原理', 0),
  (144, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '微程序控制器：控制信号存储为微指令，微地址形成微程序；修改指令仅改写微代码，硬件逻辑简单，适配CISC变长指令。', '微程序控制器无控制存储器CM；每条机器指令对应一条微指令。', '微程序控制器,控制存储器CM,微指令微程序,CISC适配', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '控制器的功能和工作原理', 0),
  (145, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '异常由CPU内部指令触发（溢出、缺页、非法指令）；中断由外部IO设备硬件触发；二者均打断当前程序流程，保存现场跳转服务程序。', '中断属于CPU内部事件；异常来自外部设备信号。', '异常,中断,内部故障,外部IO信号,程序流程打断', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '异常和中断机制', 0),
  (146, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '中断/异常分类：同步异常（指令同步触发）、异步中断（设备异步信号）；可屏蔽中断、不可屏蔽中断；故障、陷阱、终止三类异常细分。', '所有中断均可屏蔽；陷阱异常会重新执行触发指令。', '中断异常分类,同步异步,可屏蔽不可屏蔽,故障陷阱终止', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '异常和中断机制', 0),
  (147, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '中断响应完整流程：关中断、保存PC/PSW现场、跳转中断服务程序；返回时恢复现场开中断；中断向量存放服务程序入口地址。', '响应中断时不关闭中断；中断向量存放完整服务代码。', '中断响应过程,现场保存恢复,中断向量,关开中断', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '异常和中断机制', 0),
  (148, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '流水线核心思路：将指令拆分为取指、译码、执行、访存、写回多段，多指令并行重叠执行，提升CPU吞吐率，单周期时钟为最慢段延迟。', '流水线单条指令执行时间缩短；吞吐率不受段延迟限制。', '五级流水线,指令重叠,吞吐率,流水线时钟周期', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令流水线', 0),
  (149, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '流水线三大冒险：结构冒险硬件资源冲突；数据冒险读写数据依赖；控制冒险分支跳转不确定。', '分支指令不存在控制冒险；数据冒险无阻塞方案。', '结构冒险,数据冒险,控制冒险,流水线冲突', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令流水线', 0),
  (150, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '数据冒险解决方案：插入气泡阻塞、数据转发旁路Forwarding；控制冒险方案：分支预测、延迟槽、提前计算跳转目标。', '旁路可完全消除所有数据阻塞；延迟槽指令一定会执行。', '旁路转发,气泡阻塞,分支预测,延迟槽', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令流水线', 0),
  (151, '计算机组成原理', '中央处理器', '计算机组成原理', 3, '流水线吞吐率、加速比、效率计算公式；n条指令理想流水线吞吐率=n/(k+n-1)，k为流水段数。', '加速比等于段数；存在冒险时不增加气泡周期。', '流水线吞吐率,加速比,效率计算题,气泡周期', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '指令流水线', 0),
  (152, '计算机组成原理', '总线', '计算机组成原理', 3, '总线是多个部件共享传输线束，分时复用；分类方式：连接层次、传输信号、时序控制三类划分标准。', '总线同一时刻多组数据并行传输；独占线路属于总线。', '共享总线,分时复用,总线分类标准', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线概述', 0),
  (153, '计算机组成原理', '总线', '计算机组成原理', 3, '按层次划分：片内总线、系统总线、通信总线；系统总线分为地址、数据、控制三类子总线。', '片内总线连接CPU与主存；通信总线属于主机内部。', '片内总线,系统总线,通信总线,三种子总线', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线概述', 0),
  (154, '计算机组成原理', '总线', '计算机组成原理', 3, '按信号区分：并行总线多位同时传输、串行总线逐位传输；并行短距离高速，串行长距离抗干扰。', '并行总线传输距离更长；串行带宽一定更低。', '并行总线,串行总线,传输距离,抗干扰', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线概述', 0),
  (155, '计算机组成原理', '总线', '计算机组成原理', 3, '多个主设备竞争总线使用权，仲裁分配三类：链式查询、计数器定时查询、独立请求。', '从设备参与总线仲裁；链式查询优先级均匀。', '总线仲裁,链式查询,定时查询,独立请求', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线仲裁', 0),
  (156, '计算机组成原理', '总线', '计算机组成原理', 3, '链式查询离总线控制器越近设备优先级越高，硬件最简单；独立请求每个设备独立信号线，优先级灵活，硬件成本最高。', '链式远端设备优先级高；独立请求查询耗时更长。', '仲裁优先级,硬件复杂度,三类仲裁对比', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线仲裁', 0),
  (157, '计算机组成原理', '总线', '计算机组成原理', 3, '总线事务：一次完整总线读写传输；分为读事务、写事务；总线定时同步、异步两种方案。', '单次总线传输多组无关数据；同步无需时钟。', '总线事务,读事务,写事务,同步异步定时', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线操作和定时', 0),
  (158, '计算机组成原理', '总线', '计算机组成原理', 3, '同步定时统一全局时钟，所有设备节拍对齐；异步定时依靠握手应答信号，适配不同速度外设。', '异步传输使用全局统一时钟；同步适配速率差异设备。', '全局时钟,握手信号,同步异步适用场景', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线操作和定时', 0),
  (159, '计算机组成原理', '总线', '计算机组成原理', 3, '异步四握手流程：主发请求→从应答→主撤销请求→从撤销应答，完整四次信号交互。', '握手流程三步完成；请求应答同时撤销。', '异步四握手,总线应答流程', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线操作和定时', 0),
  (160, '计算机组成原理', '总线', '计算机组成原理', 3, '系统总线标准ISA、PCI、PCIe；通信总线USB、RS232；标准规定机械、电气、时序、传输协议。', 'PCIe并行传输；ISA高速现代总线。', 'PCIe,USB,总线标准规范,串行高速总线', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '总线标准', 0),
  (161, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'I/O系统组成：外设、接口、主机总线；主机与外设速度差距极大，接口负责缓冲、电平转换、握手。', '外设直接连CPU无接口；接口仅传输数据。', 'I/O外设,I/O接口,速度缓冲,电平转换', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O系统概述', 0),
  (162, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'I/O接口内部寄存器：数据缓冲DR、状态SR、控制CR；主机读写寄存器完成交互，端口即寄存器地址。', '接口无状态寄存器；端口对应外设整体。', 'DR SR CR,I/O端口,接口寄存器', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O系统概述', 0),
  (163, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '端口编址两种：统一编址（占用主存地址）、独立编址专用IO读写指令。', '独立编址使用普通load/store；统一编址无专用IO指令。', '统一编址,独立编址,IO专用指令', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O系统概述', 0),
  (164, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '外设分类：人机交互（键盘显示器）、存储（磁盘SSD）、通信网卡；输入设备转外部信号为二进制，输出反向转换。', '磁盘属于交互外设；显示器输入设备。', '三类外设,输入输出信号转换', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '外部设备', 0),
  (165, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '显示器刷新频率、分辨率、灰度；光栅扫描逐行刷新，显存存储一帧完整像素。', '显存仅存当前扫描行；刷新无闪烁无需高频。', '光栅显示器,显存,分辨率,刷新频率', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '外部设备', 0),
  (166, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '四种IO控制：程序查询、中断、DMA、通道；CPU参与程度逐步降低，效率逐步升高。', '通道CPU参与最多；DMA全程需要CPU搬运。', '四种IO控制,CPU开销对比', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O控制方式', 0),
  (167, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '程序查询CPU循环轮询外设状态，全程占用CPU，低速简单设备使用。', '查询期间CPU并行运算；轮询无性能损耗。', '程序查询,轮询循环,CPU独占', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O控制方式', 0),
  (168, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '中断方式外设就绪主动发中断，CPU切换上下文仅少量搬运，字符设备主流。', '中断大批量数据CPU逐字搬运。', '中断IO,上下文切换,字符设备', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O控制方式', 0),
  (169, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'DMA控制器批量内存外设直传，仅初始化与结束中断，块设备高速传输。', 'DMA传输每个字节触发中断。', 'DMA,块传输,内存外设直连', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O控制方式', 0),
  (170, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '通道独立专用处理器，多通道分时管理多外设，大型服务器架构。', '普通PC标配通道；通道依赖CPU每块传输。', 'IO通道,专用处理器,多外设分时', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'I/O控制方式', 0),
  (171, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'IO中断完整流程：外设发请求→CPU响应→保存现场→中断服务→恢复返回；屏蔽字控制中断优先级。', '中断服务中不屏蔽同级中断。', 'IO中断流程,中断屏蔽,现场保存', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '中断机制', 0),
  (172, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '多重中断高优先级打断低优先级，服务期间开中断；单重中断执行时屏蔽所有中断。', '单重中断允许高优先级抢占。', '多重中断,单重中断,优先级抢占', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '中断机制', 0),
  (173, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'DMA四大寄存器：主存地址MAR、外设地址、传输长度、控制寄存器；初始化写入参数后启动批量传输。', '每传输一字节更新DMA地址寄存器触发中断。', 'DMA四大寄存器,批量初始化', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'DMA方式', 0),
  (174, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'DMA传输三个阶段：预处理、数据直传、后处理中断；仅首尾CPU介入，中间硬件独立搬运。', '传输阶段CPU持续参与数据复制。', 'DMA三阶段,预处理后处理', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, 'DMA方式', 0),
  (175, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '通道类型：字节多路、数组多路、选择；字节适配低速字符设备，数组高速块设备。', '选择通道分时多外设。', '三类通道,块设备字符设备适配', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 2, NULL, '通道方式', 0),
  (176, '操作系统', '计算机系统概述', '操作系统', 3, '操作系统是管理计算机软硬件资源、控制程序执行、改善人机交互、为应用程序提供支撑的系统软件，运行在裸机之上，是硬件与用户程序中间层。核心定位为资源管理者与服务提供者。', '混淆操作系统、驱动程序、应用软件；误认为操作系统属于计算机硬件设备；忽略操作系统屏蔽硬件差异的核心作用。', '操作系统,系统软件,裸机,软硬件资源管理,人机接口,中间层', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的基本概念', 0),
  (177, '操作系统', '计算机系统概述', '操作系统', 3, '操作系统四大核心功能：进程管理、内存管理、文件管理、输入输出设备管理。设计目标：提高资源利用率、方便用户使用、系统可扩展、安全稳定。', '遗漏IO设备管理模块；混淆系统设计目标与系统功能；将吞吐率错误归为操作系统功能。', '进程管理,内存管理,文件管理,IO管理,资源利用率,易用性', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的基本概念', 0),
  (178, '操作系统', '计算机系统概述', '操作系统', 3, '操作系统四大核心特征：并发、共享、虚拟、异步。并发宏观同时运行微观交替；共享分为互斥共享、同时共享；虚拟依托时分/空分复用；异步进程走走停停、推进速度不可预测。', '并发等同于多核并行；异步理解为同步执行；虚拟技术等同于物理硬件扩容。', '并发,共享,虚拟,异步,时分复用,空分复用,临界资源', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的基本概念', 0),
  (179, '操作系统', '计算机系统概述', '操作系统', 3, '手工操作阶段无操作系统，人工装卸纸带、开关控制计算机，CPU与外设串行等待，资源利用率极低，无中断、无自动调度机制。', '误认为手工阶段存在简单监督调度程序；混淆手工阶段与单道批处理运行模式。', '手工操作阶段,纸带输入,串行执行,低CPU利用率,无中断', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (180, '操作系统', '计算机系统概述', '操作系统', 3, '单道批处理系统依靠磁带批量存放作业，监督程序自动加载执行，同一时刻内存仅一道程序，CPU等待IO时全程空闲，缓解人工操作损耗但资源浪费严重。', '认为单道批处理可以多程序并发；不清楚监督程序是早期操作系统雏形。', '单道批处理,监督程序,磁带作业,CPU空闲,串行运行', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (181, '操作系统', '计算机系统概述', '操作系统', 3, '多道批处理系统内存同时驻留多道独立作业，进程IO阻塞时调度其他就绪进程运行，大幅提升CPU、内存、外设利用率，无交互式操作、无响应时间保障。', '多道并发等同于多核并行；混淆多道批处理与分时系统交互能力。', '多道批处理,多道程序并发,IO调度,资源高利用率,无交互', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (182, '操作系统', '计算机系统概述', '操作系统', 3, '分时操作系统采用时间片轮转调度，多终端用户同时联机交互，CPU快速切换分配时间片，宏观同时使用，核心指标为响应时间，兼顾公平与人机交互。', '分时系统核心目标是高吞吐；混淆分时、实时系统优先级策略。', '分时系统,时间片轮转,联机交互,多终端,响应时间,公平调度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (183, '操作系统', '计算机系统概述', '操作系统', 3, '实时操作系统分为硬实时、软实时。硬实时截止时间绝对不可违背，用于工业控制、自动驾驶；软实时轻微延迟可接受，适用于音视频播放，核心是可预测、高优先级抢占。', '实时系统追求高吞吐量；分不清软硬实时任务截止约束强度。', '实时系统,硬实时,软实时,截止时间,优先级抢占,可预测性', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (184, '操作系统', '计算机系统概述', '操作系统', 3, '微机个人操作系统面向单用户桌面、移动端，侧重图形界面、多媒体兼容，简化批处理调度逻辑，Windows、Linux桌面、安卓均属于此类。', '微机系统不支持多道并发；认为个人系统无内核态、用户态区分。', '微机操作系统,图形界面,单用户,桌面系统,安卓,Windows', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (185, '操作系统', '计算机系统概述', '操作系统', 3, '网络操作系统依托局域网连接多台独立主机，各主机资源本地管理，仅共享文件、外设；分布式系统将多节点硬件统一抽象为全局资源，支持跨节点任务调度。', '分布式系统等同于普通局域网网络操作系统；混淆资源调度范围。', '网络操作系统,分布式系统,跨节点调度,局域网资源共享', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统发展历程', 0),
  (186, '操作系统', '计算机系统概述', '操作系统', 3, '操作系统内核分为单内核、微内核、混合内核。单内核全部功能运行内核态，调用高效；微内核仅调度、通信在内核，驱动用户态，稳定性强；混合内核融合两者优势。', '微内核运行性能优于单内核；混淆三类内核运行态划分规则。', '单内核,微内核,混合内核,内核态,进程通信,设备驱动', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的运行环境', 0),
  (187, '操作系统', '计算机系统概述', '操作系统', 3, 'CPU双重运行模式：用户态、内核态。用户态仅可执行普通指令，禁止硬件操作；内核态拥有全部特权指令，可访问硬件、修改页表，通过中断、系统调用完成模式切换。', '应用程序可直接执行硬件IO特权指令；分不清两种模式切换触发条件。', '内核态,用户态,特权指令,模式切换,中断,系统调用', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的运行环境', 0),
  (188, '操作系统', '计算机系统概述', '操作系统', 3, '中断为外部硬件异步触发事件（时钟、键盘、磁盘）；异常为CPU指令执行内部同步故障（除零、缺页、非法地址访问），二者均会触发CPU切至内核处理。', '异常属于外部硬件事件；中断同步、异常异步概念记反。', '中断,异常,硬件中断,同步故障,缺页中断,时钟中断', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的运行环境', 0),
  (189, '操作系统', '计算机系统概述', '操作系统', 3, '系统调用是用户态程序请求内核服务唯一接口，分为进程控制、文件操作、设备管理、信息维护、进程通信五类，依靠陷阱指令实现用户态切入内核态。', '库函数等同于系统调用；用户程序可绕过系统调用直接操作硬件。', '系统调用,陷阱指令,用户态内核切换,库函数,进程通信', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统的运行环境', 0),
  (190, '操作系统', '计算机系统概述', '操作系统', 3, '四种主流操作系统架构：简单单体结构、分层式结构、模块化结构、微内核结构。分层结构单向依赖，便于调试；模块化高内聚低耦合。', '分层结构允许高层调用底层模块；混淆模块化与微内核设计思路。', '单体结构,分层结构,模块化,微内核,单向依赖,模块解耦', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统结构', 0),
  (191, '操作系统', '计算机系统概述', '操作系统', 3, '开机引导完整流程：BIOS/UEFI上电自检→读取MBR主引导记录→Bootloader加载内核镜像→内核初始化硬件、创建init一号用户进程，完成系统启动。', '内核最先加载运行；混淆BIOS自检与Bootloader职责。', 'BIOS,UEFI,MBR,Bootloader,内核初始化,init进程', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '操作系统引导', 0),
  (192, '操作系统', '计算机系统概述', '操作系统', 3, '虚拟化层VMM隔离物理硬件，实现多台逻辑虚拟机，分为全虚拟化、半虚拟化、硬件辅助虚拟化；容器属于操作系统级轻量化虚拟化，无需独立内核。', '虚拟机直接访问物理硬件；容器等同于硬件虚拟机。', 'VMM,全虚拟化,半虚拟化,硬件辅助虚拟化,容器,轻量化', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟机', 0),
  (193, '操作系统', '计算机系统概述', '操作系统', 3, '本章核心易混淆概念辨析：并发vs并行、分时vs实时、中断vs异常、系统调用vs库函数、单内核vs微内核，梳理操作系统完整演进脉络。', '跨概念边界区分模糊，答题概念混淆丢分。', '绪论概念辨析,并发并行,分时实时,中断异常,内核架构对比', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '本章疑难点', 0),
  (194, '操作系统', '进程与线程', '操作系统', 3, '进程是具有独立资源、独立调度权的程序运行实例，具备动态性、并发性、独立性、异步性四大特征；程序是静态代码文件，一个程序可生成多个进程。', '程序与进程完全等同；认为进程不拥有独立内存资源。', '进程,程序,动态实例,并发性,独立地址空间,异步执行', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (195, '操作系统', '进程与线程', '操作系统', 3, '进程三大组成：程序段（只读执行代码）、数据段（全局变量常量）、PCB进程控制块，PCB是操作系统感知、调度进程唯一标识。', 'PCB存储在用户进程内存；程序段运行时可修改写入数据。', 'PCB进程控制块,程序段,数据段,PID,进程标识,只读代码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (196, '操作系统', '进程与线程', '操作系统', 3, '进程逻辑地址空间分区：代码段、全局初始化数据、BSS未初始化段、堆、栈；堆向上动态分配，栈向下存放局部变量，进程间地址空间完全隔离。', '多进程共享堆内存；混淆堆、栈增长方向与生命周期。', '进程内存映像,代码段,BSS段,堆,栈,逻辑地址隔离', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (197, '操作系统', '进程与线程', '操作系统', 3, '进程五状态模型：创建态、就绪态、运行态、阻塞态、终止态；运行进程等待IO进入阻塞，IO完成回到就绪，中断抢占运行退回就绪。', '阻塞进程可直接调度进入运行态；就绪进程主动转为阻塞态。', '进程五状态,就绪,运行,阻塞,状态转换,IO等待,进程调度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (198, '操作系统', '进程与线程', '操作系统', 3, 'PCB存储完整进程信息：PID标识符、进程状态、CPU寄存器现场、内存地址空间、文件描述符、调度优先级、父子进程指针。', 'PCB存放用户局部变量；进程切换不保存通用寄存器现场。', 'PCB,PID,CPU现场快照,内存地址,调度优先级,文件句柄', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (199, '操作系统', '进程与线程', '操作系统', 3, '进程间通信IPC分类：共享存储（共享内存、内存映射）、消息传递（管道、命名管道、消息队列）、信号量、套接字Socket跨主机通信。', '管道支持双向读写；共享内存自带同步机制无需信号量。', 'IPC进程通信,管道,共享内存,消息队列,Socket,同步互斥', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (200, '操作系统', '进程与线程', '操作系统', 3, '线程是进程内部轻量级调度单元，共享进程全部资源，私有栈与寄存器；进程切换刷新页表开销巨大，线程切换仅保存私有寄存器。', '线程拥有独立虚拟地址空间；进程切换开销小于线程切换。', '线程,轻量级进程,共享资源,私有栈,上下文切换开销,调度单元', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0);
INSERT INTO `knowledge_point` (`id`, `subject`, `name`, `parent_name`, `level`, `content`, `common_mistakes`, `keywords`, `is_high_frequency`, `create_time`, `update_time`, `subject_id`, `parent_id`, `section`, `is_deleted`) VALUES
  (201, '操作系统', '进程与线程', '操作系统', 3, '三类线程模型：用户级线程、内核级线程、多对多映射。用户级线程内核无感知，单线程阻塞整进程；内核级线程独立调度。', '用户线程阻塞仅自身；混淆三类线程调度主体。', '用户级线程,内核级线程,多对多模型,线程阻塞,内核感知', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '进程与线程简介', 0),
  (202, '操作系统', '进程与线程', '操作系统', 3, 'CPU三级调度：长程作业调度（外存调入内存）、中程挂起调度（内存进程换出磁盘）、短程进程调度（就绪分配CPU）。', '分时系统频繁执行长程调度；中程调度直接分配CPU运行进程。', '长程调度,中程调度,短程调度,作业调入,进程挂起,就绪队列', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'CPU调度', 0),
  (203, '操作系统', '进程与线程', '操作系统', 3, '调度五大评价指标：CPU利用率、系统吞吐率、周转时间、带权周转时间、响应时间；批处理看重吞吐，分时看重响应时间。', '带权周转时间分母为总运行时长；吞吐率单位为时间。', '周转时间,带权周转时间,响应时间,CPU利用率,吞吐率', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'CPU调度', 0),
  (204, '操作系统', '进程与线程', '操作系统', 3, '进程切换完整流程：中断保存现场→更新PCB状态→调度算法选新进程→加载寄存器现场→恢复地址空间继续执行。', '线程切换需要刷新页表；进程切换不修改PCB状态。', '进程切换,上下文保存,寄存器现场,PCB更新,页表刷新', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'CPU调度', 0),
  (205, '操作系统', '进程与线程', '操作系统', 3, '经典CPU调度算法：FCFS先来先服务、抢占/非抢占SJF、高响应比HRRN、时间片轮转RR、多级反馈队列，掌握各类算法周转时间计算。', 'HRRN响应比不随等待时间增大；多级队列高优先级时间片更大。', 'FCFS,SJF,HRRN,时间片轮转,多级反馈队列,抢占调度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'CPU调度', 0),
  (206, '操作系统', '进程与线程', '操作系统', 3, '多处理机调度：SMP对称多处理所有CPU平等；非对称主从架构主CPU负责调度，支持CPU亲和性、负载均衡策略。', 'SMP存在专属调度核心；CPU亲和性可随意切换核心。', 'SMP对称多处理,CPU亲和性,负载均衡,主从架构', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'CPU调度', 0),
  (207, '操作系统', '进程与线程', '操作系统', 3, '互斥：多进程排他访问临界资源；同步：进程按固定先后次序执行；临界区四条准则：空闲让进、忙则等待、有限等待、让权等待。', '同步等同于互斥；临界区无需满足让权等待。', '同步,互斥,临界区,临界资源,四条准则,忙等', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '同步与互斥', 0),
  (208, '操作系统', '进程与线程', '操作系统', 3, '临界区实现方案：软件Dekker、Peterson算法；硬件关中断、TestAndSet、Swap原子指令，硬件方案无忙等缺陷。', 'Peterson算法存在忙等；关中断适用于多核并发场景。', 'Peterson,TestAndSet,Swap,关中断,原子指令,临界区互斥', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '同步与互斥', 0),
  (209, '操作系统', '进程与线程', '操作系统', 3, '记录型信号量包含value与阻塞队列；P操作减一阻塞，V操作加一唤醒；互斥信号量初值为1，同步信号量初值为0或资源总数。', 'PV操作书写顺序颠倒；互斥信号量初值设置大于1。', '信号量,PV操作,阻塞队列,互斥初值1,同步信号量', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '同步与互斥', 0),
  (210, '操作系统', '进程与线程', '操作系统', 3, '三大经典同步问题：生产者消费者（同步+互斥双重约束）、读者写者、哲学家就餐，全部使用PV信号量完成标准实现。', '生产者消费者仅设置互斥信号量，缺少空缓冲、满缓冲同步量。', '生产者消费者,读者写者,哲学家就餐,缓冲池,PV同步', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '同步与互斥', 0),
  (211, '操作系统', '进程与线程', '操作系统', 3, '管程封装共享数据、操作过程、条件变量，同一时刻仅一个进程进入管程自动实现互斥；条件变量wait阻塞、signal唤醒完成同步。', '多进程可同时进入管程；signal后进程立即获得CPU执行。', '管程,条件变量,自动互斥,wait阻塞,signal唤醒,共享数据封装', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '同步与互斥', 0),
  (212, '操作系统', '进程与线程', '操作系统', 3, '死锁四大必要条件：互斥、占有并等待、非剥夺、循环等待；四个条件同时满足才会触发死锁，破坏任意一条即可预防。', '单一条件满足就会产生死锁；循环等待可单独规避死锁。', '死锁四大条件,互斥,占有并等待,非剥夺,循环等待,死锁预防', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '死锁', 0),
  (213, '操作系统', '进程与线程', '操作系统', 3, '死锁四种处理策略：预防、避免、检测、解除；银行家算法属于动态死锁避免，依靠安全序列判断资源分配是否安全。', '死锁避免等同于死锁预防；银行家算法属于静态预防手段。', '死锁预防,死锁避免,银行家算法,安全序列,死锁检测,资源抢占', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '死锁', 0),
  (214, '操作系统', '内存管理', '操作系统', 3, '内存管理五大目标：内存分配、地址重定位、内存保护、内存共享、虚拟内存；重定位分为静态装入、动态运行时装入。', '静态重定位支持运行时内存移动；内存保护仅限制用户访问内核。', '逻辑地址,物理地址,地址重定位,内存分配,内存保护', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '内存管理概念', 0),
  (215, '操作系统', '内存管理', '操作系统', 3, '连续分配方案：单一连续、固定分区、动态可变分区；固定分区产生内部碎片，动态分区产生外部碎片，分配算法有首次、最佳、最坏适应。', '动态分区存在内部碎片；最佳适应碎片数量最少。', '连续分配,固定分区,动态分区,外部碎片,内部碎片,分配算法', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '内存管理概念', 0),
  (216, '操作系统', '内存管理', '操作系统', 3, '基本分页存储：内存划等大页框，程序划页面；逻辑地址分为页号+页内偏移，仅存在页面内部碎片，无外部碎片，单次数据访问需要两次内存读取。', '分页存在外部碎片；逻辑地址包含段号字段。', '分页,页框,页表,页内偏移,两次访存,内部碎片', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '内存管理概念', 0),
  (217, '操作系统', '内存管理', '操作系统', 3, '基本分段存储：程序按逻辑模块分段，段长度可变；逻辑地址段号+段内偏移，无内部碎片，频繁分配产生外部碎片，支持代码共享。', '分段页面尺寸固定；分段存在内部碎片。', '分段,段表,段基址,段限长,外部碎片,代码共享', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '内存管理概念', 0),
  (218, '操作系统', '内存管理', '操作系统', 3, '段页式存储管理：先分段、段内分页；逻辑地址三层段号+页号+页内偏移，地址转换需要三次内存访问，融合分段共享、分页无外部碎片优势。', '段页式仅两次访存；段页式存在大量外部碎片。', '段页式,三级地址,段表,页表,三次内存访问', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '内存管理概念', 0),
  (219, '操作系统', '内存管理', '操作系统', 3, '虚拟内存依托时间、空间局部性原理，逻辑地址空间远大于物理内存，仅加载运行所需页面，缺页中断触发页面换入。', '虚拟内存扩容物理内存条；无局部性程序无法实现虚拟存储。', '虚拟内存,时间局部性,空间局部性,缺页中断,页面换入换出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (220, '操作系统', '内存管理', '操作系统', 3, '请求分页页表新增字段：有效位、访问位、修改位、外存块号；有效位为0触发缺页中断，修改位标记页面是否需要写回磁盘。', '基础分页页表包含修改位；缺页中断不切换内核态。', '请求分页,有效位,修改位,访问位,磁盘交换区,缺页中断', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (221, '操作系统', '内存管理', '操作系统', 3, '页框分配分为静态、动态；页面置换分为全局置换（所有进程共享页框）、局部置换（仅置换本进程页面）。', '静态分配运行可增加页框；局部置换抢占其他进程内存。', '静态分配,动态分配,全局置换,局部置换,页框池', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (222, '操作系统', '内存管理', '操作系统', 3, '四大页面置换算法：OPT最优（理论最优不可实现）、FIFO存在Belady异常、LRU最近最少使用、Clock时钟近似LRU，熟练计算缺页次数。', 'OPT可在操作系统落地；FIFO无Belady异常。', 'OPT,FIFO,LRU,Clock,Belady异常,缺页次数计算', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (223, '操作系统', '内存管理', '操作系统', 3, '抖动：页框分配过少，页面频繁换入换出，CPU利用率暴跌；工作集模型，分配页框≥进程工作集可消除抖动。', '抖动由磁盘故障引发；分配更多页框一定消除抖动。', '抖动,工作集模型,页面频繁置换,CPU利用率下降', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (224, '操作系统', '内存管理', '操作系统', 3, 'TLB快表缓存高频页表项，TLB命中仅1次内存访问；TLB失效先查页表再访问数据，总两次访存，大幅降低分页开销。', 'TLB存储完整页表；TLB失效增加磁盘IO。', 'TLB快表,页表缓存,TLB命中,地址转换加速', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (225, '操作系统', '内存管理', '操作系统', 3, '多级页表拆分页表，仅为进程使用区间分配物理内存，64位系统采用四级页表，大幅节约页表内存占用。', '多级页表减少地址访存次数；单级页表适配超大地址空间。', '二级页表,多级页表,页目录,节省内存,64位操作系统', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '虚拟内存管理', 0),
  (226, '操作系统', '文件管理', '操作系统', 3, '文件是外存带命名数据集合；逻辑结构分为无结构流式文件、有结构记录式文件；用途分为系统文件、用户文件、库文件。', '文件仅存储业务数据；默认文件为定长记录式。', '文件,流式文件,记录式文件,系统文件,外存数据集合', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '文件系统基础', 0),
  (227, '操作系统', '文件管理', '操作系统', 3, 'FCB文件控制块存储文件名、权限、磁盘块；inode剥离文件名，目录仅存放文件名+inode，节省磁盘存储空间。', 'inode存储文件名；FCB仅保存磁盘块地址。', 'FCB,inode,文件元数据,目录项,磁盘块指针', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '目录与文件', 0),
  (228, '操作系统', '文件管理', '操作系统', 3, '四类目录：单级、两级、树形、图状目录；树形目录支持绝对/相对路径，图目录依靠硬链接实现文件共享。', '树形目录硬链接可跨分区；单级目录允许同名文件。', '树形目录,两级目录,硬链接,绝对路径,相对路径', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '目录与文件', 0),
  (229, '操作系统', '文件管理', '操作系统', 3, '四种磁盘物理分配：连续、隐式链接、FAT显式链接、单/多级索引；连续读取快，索引随机读写高效。', '链接分配支持高速随机访问；连续分配无碎片。', '连续分配,FAT,多级索引,磁盘块,随机读写性能', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '目录与文件', 0),
  (230, '操作系统', '文件管理', '操作系统', 3, '硬链接指向同一inode，引用计数累加，不可跨分区；软链接存储文件路径，独立inode，原文件删除链接失效。', '硬链接可跨磁盘分区；软链接增加inode引用计数。', '硬链接,软链接,inode引用计数,跨分区限制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '目录与文件', 0),
  (231, '操作系统', '文件管理', '操作系统', 3, '磁盘空闲块管理：空闲表、空闲链表、位示图、成组链接法；Linux主流采用成组链接，查询分配高效。', '空闲链表分配速度优于位示图；成组链接无分组栈结构。', '位示图,成组链接,空闲链表,磁盘空闲块分配', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '文件系统', 0),
  (232, '操作系统', '输入输出管理', '操作系统', 3, 'I/O设备分为块设备（磁盘）、字符设备（键盘鼠标）；设备控制器包含数据、状态、控制三组寄存器，实现软硬件信号转换。', '字符设备按块批量读写；CPU直接操作外设无控制器。', '块设备,字符设备,设备控制器,控制寄存器,数据缓冲', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'I/O管理概述', 0),
  (233, '操作系统', '输入输出管理', '操作系统', 3, '四类I/O控制：轮询查询、中断驱动、DMA、I/O通道；DMA批量搬运数据，通道拥有独立处理单元。', 'DMA传输全程占用CPU；通道无独立硬件处理器。', '轮询,中断I/O,DMA,I/O通道,批量数据传输', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, 'I/O管理概述', 0),
  (234, '操作系统', '输入输出管理', '操作系统', 3, '缓冲技术：单缓冲CPU与设备串行；双缓冲实现并行；缓冲池多进程共享缓冲区，减少低速磁盘访问。', '单缓冲实现CPU与外设并行；缓冲池缓冲区不可复用。', '单缓冲,双缓冲,缓冲池,CPU设备并行,磁盘IO加速', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '设备独立性软件', 0),
  (235, '操作系统', '输入输出管理', '操作系统', 3, 'SPOOLing假脱机利用磁盘输入井、输出井，将打印机等独占设备虚拟为共享设备，多进程可并发提交打印任务。', 'SPOOLing使用内存缓冲区；适用于磁盘块设备。', 'SPOOLing,假脱机,输入井,输出井,独占设备虚拟化', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '设备独立性软件', 0),
  (236, '操作系统', '输入输出管理', '操作系统', 3, '磁盘访问耗时=寻道时间+旋转延迟+传输时间；四大寻道算法FCFS、SSTF、SCAN、C-SCAN，熟练计算总寻道磁道长度。', 'SSTF无饥饿问题；SCAN遍历全部磁道再折返。', '寻道时间,旋转延迟,SSTF,SCAN,C-SCAN,磁盘调度', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 3, NULL, '磁盘和固态硬盘', 0),
  (237, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '计算机网络是若干台独立自治计算机，通过传输介质与协议连接，实现资源共享与数据交换的系统；自治代表计算机可脱离网络独立运行。', '多终端共享主机终端系统属于计算机网络；主机必须依赖网络才能工作。', '计算机网络概念,自治计算机,资源共享,数据交换', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (238, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '计算机网络两大组成：硬件系统（主机、传输介质、交换机路由器）、软件系统（网络协议、应用程序、驱动）；核心组成单元为主机与通信子网。', '通信子网仅包含终端设备；资源子网负责转发分组。', '网络组成,资源子网,通信子网,硬件软件构成', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (239, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '计算机网络核心功能：数据通信、资源共享（硬件/软件/数据）、分布式处理、负载均衡、提高可靠性；数据通信是最基础底层功能。', '分布式处理等同于负载均衡；可靠性不属于网络核心功能。', '网络五大功能,数据通信,资源共享,分布式处理', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (240, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '三类交换技术：电路交换建立专用物理通路，无存储转发；报文交换完整报文存储转发；分组交换拆分短分组存储转发，分为数据报、虚电路两类。', '电路交换存在分组存储转发；报文交换拆分小包传输。', '电路交换,报文交换,分组交换,存储转发,虚电路数据报', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (241, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '网络分类标准：覆盖范围（LAN局域网、MAN城域网、WAN广域网、PAN个人区域网）；传输技术（广播式网络、点对点网络）；使用者（公用网、专用网）。', '广域网采用广播传输；局域网使用点对点链路为主。', 'LAN MAN WAN PAN,广播网络,点对点网络,公用专用网', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (242, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '网络核心性能指标：带宽（最高数据传输速率）、时延（发送/传播/处理/排队时延）、时延带宽积、往返时间RTT、吞吐量、利用率；带宽单位bit/s。', '带宽单位Byte/s；传播时延与分组长度相关；发送时延和距离有关。', '带宽,四类时延,RTT往返时间,吞吐量,信道利用率,时延带宽积', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络概述', 0),
  (243, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '分层结构核心思想：解耦、复用、便于维护；下层为上层提供服务，上层屏蔽底层实现细节；每层仅和相邻层交互。', '上层可直接调用底层跨层交互；分层会增加传输开销，无任何优势。', '网络分层思想,上下层服务关系,分层优势', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络体系结构与参考模型', 0),
  (244, '计算机网络', '计算机网络体系结构', '计算机网络', 3, '协议：对等层实体通信规则集合，三要素语法、语义、时序；服务：下层向上层提供的能力；接口SAP是层间交互访问点。', '协议作用于上下层；服务是对等实体之间规则。', '网络三要素协议,服务,接口SAP,对等实体', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络体系结构与参考模型', 0),
  (245, '计算机网络', '计算机网络体系结构', '计算机网络', 3, 'OSI七层模型自上而下：应用层、表示层、会话层、传输层、网络层、数据链路层、物理层；TCP/IP四层：应用层、传输层、网际层、网络接口层。', 'TCP/IP包含表示会话层；OSI网络接口层合并物理链路层。', 'OSI七层,TCP/IP四层,分层对应关系,各层核心功能', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '计算机网络体系结构与参考模型', 0),
  (246, '计算机网络', '物理层', '计算机网络', 3, '通信基础概念：模拟信号连续取值，数字信号离散；信道单向/半双工/全双工；码元是承载离散信号基本单元，码元速率单位波特Baud。', '波特率等于比特率；模拟信道只能传输模拟信号。', '模拟数字信号,三种通信方式,码元,波特率比特率', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '通信基础', 0),
  (247, '计算机网络', '物理层', '计算机网络', 3, '信道极限容量两大公式：奈奎斯特准则无噪声信道极限码元速率；香农公式有噪声信道极限比特速率，带宽、信噪比决定上限。', '奈奎斯特计算实际传输比特；香农公式不限制码元种类。', '奈奎斯特准则,香农公式,信噪比,信道极限容量计算题', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '通信基础', 0),
  (248, '计算机网络', '物理层', '计算机网络', 3, '编码：数字→数字（曼彻斯特、差分曼彻斯特、NRZ）；调制：数字→模拟（ASK、FSK、PSK、QAM）；模拟转数字为PCM采样量化编码。', '调制处理数字基带信号；曼彻斯特无自同步能力。', '数字编码,四种调制方式,PCM脉冲编码,曼彻斯特编码', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '通信基础', 0),
  (249, '计算机网络', '物理层', '计算机网络', 3, '有线介质：双绞线屏蔽/非屏蔽，低成本短距离；同轴电缆抗干扰优于双绞线；光纤单模长距离高速、多模短距离。无线介质：无线电、微波、红外。', '多模光纤传输距离远于单模；双绞线无屏蔽抗干扰强。', '双绞线,同轴电缆,单模多模光纤,无线传输介质', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '传输介质', 0),
  (250, '计算机网络', '物理层', '计算机网络', 3, '物理层接口四大特性：机械特性、电气特性、功能特性、规程特性；规定插头尺寸、电平、引脚功能、时序流程。', '接口特性包含上层协议逻辑；电气特性定义引脚用途。', '物理层四大接口特性,机械电气功能规程', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '传输介质', 0),
  (251, '计算机网络', '物理层', '计算机网络', 3, '中继器再生放大数字信号，消除衰减；仅工作物理层，无隔离冲突域，所有端口同一冲突域。', '中继器隔离冲突域；可识别MAC地址转发。', '中继器,信号再生放大,共享冲突域,物理层设备', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '物理层设备', 0),
  (252, '计算机网络', '物理层', '计算机网络', 3, '集线器HUB多端口中继器，共享总线型拓扑；同一时刻仅一台设备发送，所有端口同冲突域、同广播域。', '集线器每个端口独立冲突域；基于MAC转发帧。', '集线器HUB,共享总线,单冲突域,广播域全覆盖', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '物理层设备', 0),
  (253, '计算机网络', '数据链路层', '计算机网络', 3, '数据链路层介于物理层与网络层之间，屏蔽底层物理介质差异，为网络层提供透明帧传输服务。', '数据链路层负责端到端传输；直接处理IP分组路由。', '数据链路层位置,上下层交互,透明传输帧', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层的功能', 0),
  (254, '计算机网络', '数据链路层', '计算机网络', 3, '链路管理：建立、维持、释放数据链路连接，面向连接链路专用流程。', '无连接链路仍需要链路建立释放流程。', '链路管理,连接建立维持释放,面向连接链路', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层的功能', 0),
  (255, '计算机网络', '数据链路层', '计算机网络', 3, '封装成帧：给网络层分组增加帧头帧尾标识帧边界；透明传输处理数据中与帧分界符相同的比特/字符，避免误判帧结束。', '透明传输直接丢弃分界字符；帧封装仅增加头部无尾部。', '封装成帧,帧头帧尾,透明传输,分界符冲突处理', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层的功能', 0),
  (256, '计算机网络', '数据链路层', '计算机网络', 3, '流量控制：接收方缓冲区满时通知发送方降低发送速率，防止溢出；局限点对点链路层面，区别传输层端到端流量控制。', '链路层流量控制控制全网主机速率；等同于TCP流量控制。', '链路层流量控制,点对点缓冲,区别传输层流量控制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层的功能', 0),
  (257, '计算机网络', '数据链路层', '计算机网络', 3, '差错检测：校验码识别传输比特错误；可靠传输重传出错丢失帧，仅部分链路协议实现可靠传输，以太网默认不可靠。', '所有数据链路层协议均提供可靠传输；检错等同于纠错。', '差错检测,可靠传输,帧重传,以太网不可靠传输', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层的功能', 0),
  (258, '计算机网络', '数据链路层', '计算机网络', 3, '字符计数法帧头记录帧长度；缺陷：计数字段出错则整段帧全部失步，极少使用。', '字符计数法容错性强；无需额外处理透明传输。', '字符计数法,帧长度字段,失步缺陷', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '组帧', 0),
  (259, '计算机网络', '数据链路层', '计算机网络', 3, '字节填充法（字符填充）：特殊分界字符前后增加转义字符，接收方删除填充恢复原始数据，面向字符链路PPP早期方案。', '转义字符无需二次填充；分界符直接丢弃。', '字节填充,转义字符,面向字符帧,PPP字符模式', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '组帧', 0),
  (260, '计算机网络', '数据链路层', '计算机网络', 3, '零比特填充法HDLC标准：帧首尾01111110；数据连续5个1自动填充0，接收方5个1后删除填充0，面向比特主流方案。', '连续5个1填充1；首尾标志字段不统一。', '零比特填充,HDLC,5个1填充0,面向比特透明传输', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '组帧', 0),
  (261, '计算机网络', '数据链路层', '计算机网络', 3, '违规编码法曼彻斯特编码利用不存在电平组合作为帧边界，无需填充，局域网早期使用，依赖物理层编码。', '违规编码可用于任意物理层信号；需要字节/比特填充。', '违规编码法,曼彻斯特编码,无填充组帧,局域网旧方案', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '组帧', 0),
  (262, '计算机网络', '数据链路层', '计算机网络', 3, '检错编码：奇偶校验（简单低容错）、CRC循环冗余校验；CRC可检出全部单双比特错、大部分突发错，无法纠错。', 'CRC可以纠正比特错误；奇偶校验能识别多比特错。', '奇偶校验,CRC循环冗余校验,检错编码,突发差错检测', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '差错控制', 0),
  (263, '计算机网络', '数据链路层', '计算机网络', 3, '纠错编码海明码；插入校验位，可定位并纠正单比特错误，计算校验位位数、错码位置是核心计算考点。', '海明码只能检错不能纠错；校验位数量计算公式记错。', '海明码,纠错编码,单比特纠错,校验位位数计算', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '差错控制', 0),
  (264, '计算机网络', '数据链路层', '计算机网络', 3, '停等协议：发送一帧等待ACK再发下一帧；窗口大小固定为1，信道利用率极低，长距离链路性能差。', '停等可连续发送多帧；超时重传无需计时器。', '停等协议,窗口=1,超时重传,低信道利用率', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '流量控制与可靠传输机制', 0),
  (265, '计算机网络', '数据链路层', '计算机网络', 3, '后退N帧GBN滑动窗口：发送窗口>1，失序帧全部丢弃回退重传；接收窗口固定1，缓存开销小，带宽浪费大。', 'GBN接收缓存乱序帧；仅重传出错单帧。', '后退N帧GBN,滑动窗口,接收窗口1,整段重传', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '流量控制与可靠传输机制', 0),
  (266, '计算机网络', '数据链路层', '计算机网络', 3, '选择重传SR滑动窗口：发送接收窗口均大于1，仅重传出错丢失帧，乱序帧缓存等待，信道利用率最优，缓存硬件开销大。', 'SR丢弃失序帧；接收窗口无需缓存乱序分组。', '选择重传SR,独立重传错帧,双滑动窗口,乱序缓存', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '流量控制与可靠传输机制', 0),
  (267, '计算机网络', '数据链路层', '计算机网络', 3, '信道划分MAC：频分FDMA、时分TDMA、波分WDMA、码分CDMA；静态分配无冲突，信道资源闲置时浪费带宽。', '信道划分属于随机访问；空闲链路自动释放资源给其他主机。', '静态信道划分,FDMA TDMA WDMA CDMA,无冲突固定分配', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '介质访问控制', 0),
  (268, '计算机网络', '数据链路层', '计算机网络', 3, '随机访问MAC：ALOHA纯/时隙ALOHA、CSMA、CSMA/CD以太网、CSMA/CA无线802.11；竞争信道，存在冲突，负载轻效率高。', 'CSMA/CA用于有线以太网；时隙ALOHA冲突窗口更长。', '随机访问,ALOHA,CSMA/CD,CSMA/CA,冲突检测避免', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '介质访问控制', 0),
  (269, '计算机网络', '数据链路层', '计算机网络', 3, '轮询访问令牌传递Token Ring；令牌循环传递，持有令牌方可发送，无冲突，高负载稳定，硬件复杂。', '令牌环随机竞争信道；无令牌也可发送数据。', '令牌传递协议,轮询访问,无冲突环形拓扑', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '介质访问控制', 0),
  (270, '计算机网络', '数据链路层', '计算机网络', 3, '局域网LAN短距离广播网络；体系结构两层：MAC子层、LLC逻辑链路控制子层；共享广播信道，传输速率高延迟低。', '局域网三层完整OSI分层；点对点链路为主。', '局域网基本概念,MAC LLC子层,广播信道,短距离高速', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '局域网', 0),
  (271, '计算机网络', '数据链路层', '计算机网络', 3, '以太网IEEE 802.3标准；CSMA/CD介质访问，48位MAC硬件地址；帧结构包含前导码、目的源MAC、类型字段、FCS校验；无可靠重传机制。', '以太网提供可靠传输；MAC地址32位IPv4格式。', '以太网,IEEE802.3,CSMA/CD,48位MAC帧,FCS CRC校验', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '局域网', 0),
  (272, '计算机网络', '数据链路层', '计算机网络', 3, '无线局域网IEEE 802.11 WiFi；CSMA/CA避免冲突，无线无法边发边检测冲突；帧增加管理、控制、数据多类帧格式。', 'WiFi使用CSMA/CD冲突检测；无线帧结构与以太网完全一致。', '802.11无线局域网,CSMA/CA,WiFi帧结构,无线冲突避免', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '局域网', 0),
  (273, '计算机网络', '数据链路层', '计算机网络', 3, 'VLAN虚拟局域网；逻辑划分广播域，同一物理交换机拆分多广播域；基于端口/MAC/IP划分，Trunk干道承载多VLAN标签帧。', 'VLAN分割冲突域；Access端口携带多VLAN标签。', 'VLAN虚拟局域网,广播域隔离,Trunk干道,VLAN标签802.1Q', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '局域网', 0),
  (274, '计算机网络', '数据链路层', '计算机网络', 3, '广域网WAN跨长距离大范围网络；点对点链路为主，依靠路由器连接异构局域网；链路层协议PPP为主。', '广域网采用广播信道；交换机作为核心转发设备。', '广域网基本概念,点对点链路,路由器互联异构LAN', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '广域网', 0),
  (275, '计算机网络', '数据链路层', '计算机网络', 3, '点对点协议PPP：广域网标准链路层协议；零比特填充透明传输，CRC差错检测，支持认证PAP/CHAP；分为链路、网络、认证阶段。', 'PPP提供可靠帧重传；采用字节计数组帧方式。', 'PPP协议,点对点广域网,零比特填充,PAP CHAP认证', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '广域网', 0),
  (276, '计算机网络', '数据链路层', '计算机网络', 3, '网桥二层设备，基于MAC地址转发；隔离冲突域，同一广播域；存储完整帧查表转发，不修改三层IP信息。', '网桥隔离广播域；读取IP地址路由转发。', '网桥,二层设备,MAC转发表,分割冲突域,全域广播', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层设备', 0),
  (277, '计算机网络', '数据链路层', '计算机网络', 3, '以太网交换机多端口高性能网桥；每个端口独立冲突域，所有端口同广播域；自学习算法动态构建MAC地址表。', '交换机分割广播域；端口共享同一冲突域如集线器。', '以太网交换机,独立端口冲突域,MAC自学习,单广播域', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层设备', 0),
  (278, '计算机网络', '数据链路层', '计算机网络', 3, '共享式以太网集线器组网；全部端口单一冲突域、单一广播域；物理层设备，无MAC查表转发，广播全部端口。', '共享式以太网交换机隔离冲突域；集线器二层转发。', '共享式以太网,集线器组网,单冲突域广播域', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '数据链路层设备', 0),
  (279, '计算机网络', '网络层', '计算机网络', 3, '异构网络互连：屏蔽二层链路帧格式差异，统一IP分组实现不同局域网互通；路由器核心完成跨网段互连。', '交换机实现异构网络互通；二层帧可直接跨不同局域网传输。', '异构网络互连,路由器,IP统一分组,屏蔽二层差异', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层的功能', 0),
  (280, '计算机网络', '网络层', '计算机网络', 3, '路由与转发：路由算法生成全局路由表；转发根据目的IP匹配路由表，将分组输出至对应出接口；路由控制平面，转发数据平面。', '转发生成路由表；路由仅本地单跳转发决策。', '路由算法,分组转发,控制平面数据平面,路由表匹配', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层的功能', 0),
  (281, '计算机网络', '网络层', '计算机网络', 3, '网络层两类服务：无连接数据报服务（IP原生，独立路由，故障分组单独丢弃）；面向连接虚电路服务（全程固定路径，分组共享虚电路号）。', 'IP是面向连接虚电路；数据报全程预留带宽资源。', '数据报服务,虚电路服务,无连接面向连接网络层', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层的功能', 0),
  (282, '计算机网络', '网络层', '计算机网络', 3, 'SDN软件定义网络：控制平面与数据平面完全解耦；集中控制器统一计算下发路由流表，交换机仅执行转发。', '传统路由器控制数据平面分离；SDN交换机本地运行路由算法。', 'SDN基本概念,控转分离,集中控制器,流表转发', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层的功能', 0),
  (283, '计算机网络', '网络层', '计算机网络', 3, '拥塞控制：全局网络负载过高时限制分组注入速率，防止路由器缓冲区溢出；区别传输层端到端流量控制，作用全网链路。', '拥塞控制仅管控单条TCP连接；等同于点对点流量控制。', '网络层拥塞控制,全局负载,路由器缓冲溢出,区分端到端流量控制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层的功能', 0),
  (284, '计算机网络', '网络层', '计算机网络', 3, 'IPv4分组首部固定20字节+可选变长选项字段；版本4、首部长度、服务类型、总长度、标识、标志片偏移、TTL、协议、校验和、源目的IP。', 'IPv4首部固定长度可变；TTL代表传输总跳数上限。', 'IPv4分组首部,分片标志片偏移,TTL生存时间,首部校验和', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (285, '计算机网络', '网络层', '计算机网络', 3, '32位IPv4地址分类：A类0开头大型网络、B类10开头中型、C类110开头小型、D类1110多播、E类保留；子网划分借用主机位划分子网，子网掩码区分网络主机位。', 'A类首字节范围1~128；子网掩码主机位置1。', 'ABCDE类IPv4地址,子网划分,子网掩码,网络位主机位', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (286, '计算机网络', '网络层', '计算机网络', 3, 'NAT网络地址转换：内网私有IP访问公网时转换为公网IP+端口；节约公网IPv4地址，屏蔽内网主机拓扑，分为静态、动态、PAT端口多路复用。', 'NAT对外网主动发起内网连接；私有IP可直接公网路由转发。', 'NAT,PAT端口复用,私有公网地址转换,IPv4地址节约', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (287, '计算机网络', '网络层', '计算机网络', 3, '分组转发流程：路由器提取目的IP，与各接口子网掩码匹配最长前缀；匹配出接口转发；无匹配丢弃返回ICMP差错报文。', '匹配最短前缀转发；转发修改源目的IP地址。', 'IP分组转发,最长前缀匹配,子网掩码逐位与运算', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (288, '计算机网络', '网络层', '计算机网络', 3, 'ARP地址解析协议：已知目的IP广播请求对应MAC；ARP缓存存储IP-MAC映射；仅局域网段有效，不可跨路由器转发ARP广播。', 'ARP报文可路由跨网段；单播ARP请求全网泛洪。', 'ARP协议,IP转MAC,ARP缓存,局域网广播请求', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (289, '计算机网络', '网络层', '计算机网络', 3, 'DHCP动态主机配置协议：客户端广播请求，服务器分配IP、子网掩码、网关、DNS；基于UDP 67/68端口，自动配置终端网络参数。', 'DHCP单播分配地址；分配永久静态IP无租约过期。', 'DHCP,动态IP分配,租约机制,UDP 67 68端口', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (290, '计算机网络', '网络层', '计算机网络', 3, 'ICMP网际控制报文协议：差错报告、查询报文；差错报文不可转发分片、ICMP、广播报文；ping、traceroute基于ICMP实现。', 'ICMP差错报文响应广播分组；ping使用TCP传输探测报文。', 'ICMP,差错查询报文,ping traceroute,禁止响应广播差错', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv4', 0),
  (291, '计算机网络', '网络层', '计算机网络', 3, 'IPv6改进特点：128位超大地址空间，取消分片路由器处理，首部简化无校验和，内置IPSec安全，多播强化，无广播地址。', 'IPv6保留广播地址；路由器分片重组IP分组。', 'IPv6六大特点,128位地址,简化首部,取消首部校验和', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv6', 0),
  (292, '计算机网络', '网络层', '计算机网络', 3, 'IPv6基础首部固定40字节，无变长选项；版本6、流量类型、流标签、有效载荷长度、下一首部、跳限制、源128位、目的128位。', 'IPv6首部可变长；保留标识/片偏移分片字段。', 'IPv6固定40字节首部,流标签,跳限制,无分片字段', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv6', 0),
  (293, '计算机网络', '网络层', '计算机网络', 3, 'IPv6地址类型：单播、多播、任播；地址简写规则前导零省略、连续全零段双冒号替换，仅允许一处双冒号压缩。', 'IPv6存在广播地址；多处双冒号压缩简写。', 'IPv6单播多播任播,地址简写压缩规则,128位十六进制', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv6', 0),
  (294, '计算机网络', '网络层', '计算机网络', 3, 'IPv4向IPv6过渡技术：双栈主机同时支持两套协议；隧道技术IPv6分组封装进IPv4传输；网络地址转换NAT64实现跨版本互通。', '单栈主机可同时访问IPv4 IPv6网络；隧道修改内层IP地址。', '双栈,隧道技术,NAT64,IPv4 IPv6过渡方案', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IPv6', 0),
  (295, '计算机网络', '网络层', '计算机网络', 3, '路由算法分类：静态路由手动配置；动态路由自动交换路由信息更新表；距离矢量DV、链路状态LS两大主流动态算法。', '静态路由自动适应拓扑变化；LS算法仅传递邻居距离向量。', '静态动态路由,距离矢量DV,链路状态LS,路由算法分类', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '路由算法与路由协议', 0),
  (296, '计算机网络', '网络层', '计算机网络', 3, '分层次路由：自治系统AS内部IGP；自治系统间EGP；隔离全网路由计算范围，减小路由表规模，提升收敛速度。', 'IGP跨自治系统交换路由；EGP计算AS内部网段路由。', '自治系统AS,IGP内部网关,EGP外部网关,分层路由', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '路由算法与路由协议', 0),
  (297, '计算机网络', '网络层', '计算机网络', 3, 'RIP路由信息协议IGP距离矢量DV；跳数为度量，最大有效跳数15，16不可达；30秒周期广播完整路由表，易产生计数到无穷问题。', 'RIP链路状态协议；跳数上限255，16可达网段。', 'RIP,距离矢量DV,跳数度量,30秒更新,计数到无穷', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '路由算法与路由协议', 0),
  (298, '计算机网络', '网络层', '计算机网络', 3, 'OSPF开放最短路径优先IGP链路状态LS；度量代价综合带宽延迟；仅泛洪链路状态LSA，不传递完整路由表；支持区域分层，无计数无穷缺陷。', 'OSPF距离矢量协议；周期性广播全部路由条目。', 'OSPF,链路状态LSA,代价度量,区域划分,无计数无穷', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '路由算法与路由协议', 0),
  (299, '计算机网络', '网络层', '计算机网络', 3, 'BGP边界网关协议EGP自治系统间路由；路径矢量算法，传递AS路径序列；解决跨AS路由可达性，不计算最短跳数。', 'BGP计算全网最短路径；IGP跨自治系统传递路由。', 'BGP,外部网关EGP,路径矢量,AS路径属性,域间路由', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '路由算法与路由协议', 0),
  (300, '计算机网络', '网络层', '计算机网络', 3, 'IP多播单份分组发送至一组接收主机；D类IPv4多播地址224.0.0.0~239.255.255.255；区别单播一对一、广播全体主机。', '多播等同于广播；A/B/C类地址用于多播通信。', 'IP多播概念,D类多播地址,一对多传输,区分单播广播', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IP多播', 0);
INSERT INTO `knowledge_point` (`id`, `subject`, `name`, `parent_name`, `level`, `content`, `common_mistakes`, `keywords`, `is_high_frequency`, `create_time`, `update_time`, `subject_id`, `parent_id`, `section`, `is_deleted`) VALUES
  (301, '计算机网络', '网络层', '计算机网络', 3, '局域网硬件多播：IPv4多播地址低23bit映射以太网MAC多播；网卡匹配对应多播MAC接收分组，过滤无关多播流量。', '完整32位多播IP映射48位MAC；网卡接收全部多播帧无过滤。', '硬件多播,IP转MAC多播映射,低23bit映射规则', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IP多播', 0),
  (302, '计算机网络', '网络层', '计算机网络', 3, 'IGMP互联网组管理协议：主机与本地路由器交互，声明加入/退出多播组；组播路由协议PIM跨路由器转发多播分组。', 'IGMP跨广域网转发多播；PIM仅局域网本地管理组。', 'IGMP本地组管理,PIM组播路由,多播组加入退出', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'IP多播', 0),
  (303, '计算机网络', '网络层', '计算机网络', 3, '移动IP：主机切换接入网段仍保持固定永久家乡IP；家乡代理HA、外地代理FA转发隧道封装分组，实现无缝漫游。', '主机切换网段修改IP地址；外地代理直接转发明文IP分组。', '移动IP概念,家乡代理HA,外地代理FA,隧道封装漫游', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '移动IP', 0),
  (304, '计算机网络', '网络层', '计算机网络', 3, '移动IP通信流程：通信节点发分组至家乡IP；HA截获封装隧道发往FA转交移动主机；回程分组直接路由不经过家乡代理。', '往返流量均经过家乡代理隧道封装；移动主机本地通信无需注册FA。', '移动IP完整通信流程,隧道封装单向绕行,回程直路由', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '移动IP', 0),
  (305, '计算机网络', '网络层', '计算机网络', 3, '冲突域：同一共享链路并发发送产生冲突；广播域：广播帧泛洪覆盖全部端口；路由器隔离广播域；交换机隔离冲突域不隔离广播域。', '交换机分割广播域；路由器同一接口多主机共享冲突域。', '冲突域广播域定义,二层三层设备隔离差异', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层设备', 0),
  (306, '计算机网络', '网络层', '计算机网络', 3, '路由器三层网络层设备；硬件组成CPU、路由表存储、交换矩阵、端口接口；核心功能IP分组路由转发，隔离广播域，终结二层帧。', '路由器基于MAC地址转发；转发修改源目的MAC二层地址。', '路由器组成功能,三层路由转发,隔离广播域,帧重封装', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层设备', 0),
  (307, '计算机网络', '网络层', '计算机网络', 3, '路由表核心字段：目的网络地址、子网掩码、下一跳IP、出接口、度量开销；最长前缀匹配优先选择掩码更长路由条目。', '路由表存储单台主机IP；匹配最短子网掩码路由。', '路由表字段,最长前缀匹配,下一跳出接口开销', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络层设备', 0),
  (308, '计算机网络', '传输层', '计算机网络', 3, '传输层端到端进程间通信；屏蔽底层网络异构，为应用层提供统一数据传输服务；仅主机终端存在传输层，路由器无传输层逻辑。', '路由器处理传输层端口；网络层实现进程到进程通信。', '传输层功能,端到端进程通信,路由器无传输层', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '传输层提供的服务', 0),
  (309, '计算机网络', '传输层', '计算机网络', 3, '端口寻址16位0~65535；熟知端口0~1023固定分配标准服务；注册端口1024~49151；动态私有端口49152~65535；IP+端口唯一标识通信套接字Socket。', '端口标识主机设备；熟知端口大于1024。', '16位端口,熟知端口,套接字Socket,IP端口二元标识进程', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '传输层提供的服务', 0),
  (310, '计算机网络', '传输层', '计算机网络', 3, '无连接UDP：无需建立连接，开销小，不可靠；面向连接TCP：三次握手建立、四次挥手释放，可靠有序流量拥塞控制。', 'UDP提供可靠重传；TCP无需断开连接直接释放。', 'UDP无连接,TCP面向连接,可靠有序传输,连接建立释放', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '传输层提供的服务', 0),
  (311, '计算机网络', '传输层', '计算机网络', 3, 'UDP数据报首部固定8字节：源端口、目的端口、报文长度、校验和；无连接无状态，发送即交付，不缓存报文无重传。', 'UDP首部20字节可变；校验和仅校验首部不含数据。', 'UDP 8字节首部,无连接无状态,报文校验和', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'UDP', 0),
  (312, '计算机网络', '传输层', '计算机网络', 3, 'UDP校验计算：伪首部（源目的IP、协议17、UDP长度）+UDP完整报文；校验出错直接丢弃报文无差错反馈。', 'UDP校验不包含伪首部；校验错误返回ICMP差错报文。', 'UDP伪首部,校验和计算,协议号17,丢弃出错报文', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'UDP', 0),
  (313, '计算机网络', '传输层', '计算机网络', 3, 'TCP核心特性：面向连接、可靠交付、字节流有序、流量控制、拥塞控制、全双工；无广播多播，一对一通信。', 'TCP报文独立数据报无序传输；支持一对多多播连接。', 'TCP六大核心特点,字节流有序,全双工可靠连接', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (314, '计算机网络', '传输层', '计算机网络', 3, 'TCP报文首部固定20字节+选项；源目的端口、序号seq、确认ack、首部长度、6位标志URG/ACK/PSH/RST/SYN/FIN、窗口、校验、紧急指针。', 'TCP首部长度固定无变长选项；标志位仅ACK SYN有效。', 'TCP报文首部,序号确认号,六位标志位,滑动窗口字段', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (315, '计算机网络', '传输层', '计算机网络', 3, 'TCP连接管理：三次握手建立（SYN同步）；四次挥手释放（FIN结束）；半关闭状态、TIME-WAIT等待2MSL防止残留报文干扰新连接。', '连接释放三次报文；握手携带业务数据载荷。', '三次握手建立,四次挥手断开,2MSL TIME-WAIT,半关闭', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (316, '计算机网络', '传输层', '计算机网络', 3, 'TCP可靠传输：累计确认、超时重传、冗余ACK快速重传；滑动窗口缓存乱序字节，按序号向上交付应用层，丢失分组自动重传恢复。', '单报文独立确认；乱序分组直接丢弃不缓存等待。', '可靠传输机制,累计确认,超时重传,快速重传,滑动窗口缓存', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (317, '计算机网络', '传输层', '计算机网络', 3, 'TCP流量控制接收方通告窗口rwnd；防止发送方溢出接收缓冲区；基于接收剩余缓存动态调整发送速率，端到端点对点控制。', '流量控制管控全网路由器负载；窗口由发送方单方面固定。', '流量控制,接收通告窗口rwnd,缓冲区防溢出,端到端点对点', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (318, '计算机网络', '传输层', '计算机网络', 3, 'TCP拥塞控制：慢启动、拥塞避免、快重传、快恢复；拥塞窗口cwnd管控注入网络分组，防止链路路由器全局过载。', '拥塞控制仅保护本地接收缓存；慢启动线性增长拥塞窗口。', '拥塞控制四阶段,慢启动指数增长,cwnd拥塞窗口,全局链路负载', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'TCP', 0),
  (319, '计算机网络', '应用层', '计算机网络', 3, '客户/服务器C/S模型：服务器长期运行监听端口，客户端主动发起请求；服务器拥有固定公网地址，客户端地址可动态分配，一对多通信架构。', '客户端被动等待连接；服务器临时上线处理单次请求。', 'C/S模型,客户端,服务器,固定地址,长期监听', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络应用模型', 0),
  (320, '计算机网络', '应用层', '计算机网络', 3, 'P2对等模型：主机同时兼具客户端与服务器功能，无中心固定服务节点；节点对等互相上传下载资源，分布式无单点瓶颈。', 'P2P存在专属中心服务器；节点仅单向接收数据。', 'P2P对等网络,分布式,无中心,节点双向服务', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络应用模型', 0),
  (321, '计算机网络', '应用层', '计算机网络', 3, '混合P2P架构：引入索引服务器保存资源节点地址，实际数据传输节点直连；兼顾检索效率与分布式传输优势，BT迅雷典型实现。', '索引服务器转发文件数据；纯P2P需要中心索引。', '混合P2P,Tracker索引服务器,节点直传,BT下载', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '网络应用模型', 0),
  (322, '计算机网络', '应用层', '计算机网络', 3, 'DNS作用：将人类可读域名映射为32位IPv4地址，反向解析IP对应域名；分布式分层数据库，无需单点集中服务器。', 'DNS直接参与数据传输；集中式全局域名数据库。', 'DNS域名解析,域名转IP,分布式分层,反向解析', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'DNS域名系统', 0),
  (323, '计算机网络', '应用层', '计算机网络', 3, '域名层级结构：根域.顶级域.com/.org/.cn.二级域主机名；从右至左逐层检索，根服务器管辖全部顶级域。', '域名从左向右分层查询；根域存储完整域名记录。', '域名层级,根服务器,顶级域,二级域,从右至左检索', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'DNS域名系统', 0),
  (324, '计算机网络', '应用层', '计算机网络', 3, '四类DNS服务器：根域名服务器、顶级域名服务器、权限域名服务器、本地域名服务器；本地DNS缓存常用映射，减少外网查询。', '本地服务器保存全网域名；权限服务器仅管辖根域。', '四类DNS服务器,本地缓存,权限服务器,根服务器', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'DNS域名系统', 0),
  (325, '计算机网络', '应用层', '计算机网络', 3, '两种查询方式：递归查询（本地服务器完整替客户端查到底）、迭代查询（逐层返回下一级服务器地址客户端自主查询）。', '根服务器执行递归查询；本地DNS默认迭代。', '递归查询,迭代查询,域名查询流程', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'DNS域名系统', 0),
  (326, '计算机网络', '应用层', '计算机网络', 3, 'DNS报文基于UDP 53端口，短报文；区域传输同步域名库使用TCP；报文头部标识查询类型、资源记录类型。', 'DNS全部传输采用TCP；知名端口80。', 'DNS UDP53,TCP区域同步,域名报文', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, 'DNS域名系统', 0),
  (327, '计算机网络', '应用层', '计算机网络', 3, 'FTP文件传输协议C/S架构，双连接：控制连接持久交互，数据连接单次传输文件；21端口控制，20端口主动模式数据。', '单条连接同时传命令与文件；数据端口固定21。', 'FTP双连接,控制连接21,数据连接20,持久控制通道', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '文件传输协议', 0),
  (328, '计算机网络', '应用层', '计算机网络', 3, '主动FTP：服务器20端口主动连客户端随机高位；被动FTP服务器开放随机端口等待客户端连接，防火墙友好。', '被动模式服务器使用20端口发起连接。', '主动FTP,被动FTP,防火墙适配,随机数据端口', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '文件传输协议', 0),
  (329, '计算机网络', '应用层', '计算机网络', 3, 'TFTP简单文件传输UDP 69端口，无认证、仅小型文件，基于停等可靠传输，局域网设备固件升级使用。', 'TFTP TCP传输；带账号密码校验。', 'TFTP UDP69,无认证,停等协议,小型文件', 0, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '文件传输协议', 0),
  (330, '计算机网络', '应用层', '计算机网络', 3, '邮件系统三组件：用户代理UA、报文传输MTA、报文访问POP/IMAP；发送服务器转发，接收服务器缓存邮件。', '客户端直接发给对方主机，无中转MTA。', 'UA用户代理,MTA传输服务器,POP IMAP访问协议', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '电子邮件', 0),
  (331, '计算机网络', '应用层', '计算机网络', 3, 'SMTP发送邮件TCP 25端口，仅传输ASCII文本，二进制附件需要MIME编码；推模式单向发送。', 'SMTP接收邮件；原生支持图片视频。', 'SMTP 25端口,MIME二进制编码,邮件推送', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '电子邮件', 0),
  (332, '计算机网络', '应用层', '计算机网络', 3, 'POP3邮局协议TCP110，下载本地后服务器删除副本；离线只读，多终端同步差。', 'POP3服务器保留完整邮件；在线实时同步文件夹。', 'POP3 110,本地下载,删除服务器副本', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '电子邮件', 0),
  (333, '计算机网络', '应用层', '计算机网络', 3, 'IMAP互联网消息访问TCP143，服务器永久存储，多终端文件夹同步，可选择性下载正文。', 'IMAP下载后删除源邮件；仅支持单终端。', 'IMAP 143,云端永久存储,多设备同步', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '电子邮件', 0),
  (334, '计算机网络', '应用层', '计算机网络', 3, 'WWW核心组件：网页HTML、浏览器、Web服务器、HTTP超文本传输协议；超链接跳转跨服务器资源。', '网页传输依靠FTP；超链接仅限本机文件。', 'WWW万维网,HTML,HTTP,超链接', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (335, '计算机网络', '应用层', '计算机网络', 3, 'URL统一资源定位符格式：协议://主机:端口/路径/文件名；唯一标识全网资源位置。', 'URL不含端口；域名与URL等价概念。', 'URL格式,协议主机端口路径,资源唯一标识', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (336, '计算机网络', '应用层', '计算机网络', 3, 'HTTP/1.1持续连接，默认长连接；流水线请求无需等待前条响应；八大请求方法GET/POST/HEAD/PUT/DELETE等。', 'HTTP1.0默认长连接；GET携带大量表单数据。', 'HTTP1.1长连接,流水线,八大请求方法', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (337, '计算机网络', '应用层', '计算机网络', 3, 'HTTP报文结构：请求行、请求头部、空行、请求体；响应行状态码2xx成功3xx重定向4xx客户端错5xx服务器错。', '状态码4xx服务内部故障；响应无空行分隔头部数据。', 'HTTP报文,状态码分类,请求行响应行', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (338, '计算机网络', '应用层', '计算机网络', 3, 'Cookie服务器存储在客户端小型文本，会话跟踪；无状态HTTP依靠Cookie维持用户会话。', 'Cookie存服务器内存；HTTP原生有状态连接。', 'Cookie会话跟踪,无状态HTTP,客户端缓存文本', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (339, '计算机网络', '应用层', '计算机网络', 3, 'HTTPS HTTP+TLS加密，TCP443端口；传输内容对称加密，身份非对称证书认证，防窃听篡改伪造。', 'HTTPS独立应用层协议；端口80。', 'HTTPS TLS加密,443端口,证书认证,对称非对称', 1, '2026-06-25 17:46:12.411645', '2026-06-25 17:46:12.411645', 4, NULL, '万维网', 0),
  (340, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'I/O系统组成：外设、接口、主机总线；主机与外设速度差距极大，接口负责缓冲、电平转换、握手。', '外设直接连CPU无接口；接口仅传输数据。', 'I/O外设,I/O接口,速度缓冲,电平转换', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO系统概述', 0),
  (341, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'I/O接口内部寄存器：数据缓冲DR、状态SR、控制CR；主机读写寄存器完成交互，端口即寄存器地址。', '接口无状态寄存器；端口对应外设整体。', 'DR SR CR,I/O端口,接口寄存器', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO系统概述', 0),
  (342, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '端口编址两种：统一编址（占用主存地址）、独立编址专用IO读写指令。', '独立编址使用普通load/store；统一编址无专用IO指令。', '统一编址,独立编址,IO专用指令', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO系统概述', 0),
  (343, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '四种IO控制：程序查询、中断、DMA、通道；CPU参与程度逐步降低，效率逐步升高。', '通道CPU参与最多；DMA全程需要CPU搬运。', '四种IO控制,CPU开销对比', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO控制方式', 0),
  (344, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '程序查询CPU循环轮询外设状态，全程占用CPU，低速简单设备使用。', '查询期间CPU并行运算；轮询无性能损耗。', '程序查询,轮询循环,CPU独占', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO控制方式', 0),
  (345, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '中断方式外设就绪主动发中断，CPU切换上下文仅少量搬运，字符设备主流。', '中断大批量数据CPU逐字搬运。', '中断IO,上下文切换,字符设备', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO控制方式', 0),
  (346, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, 'DMA控制器批量内存外设直传，仅初始化与结束中断，块设备高速传输。', 'DMA传输每个字节触发中断。', 'DMA,块传输,内存外设直连', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO控制方式', 0),
  (347, '计算机组成原理', '输入输出系统', '计算机组成原理', 3, '通道独立专用处理器，多通道分时管理多外设，大型服务器架构。', '普通PC标配通道；通道依赖CPU每块传输。', 'IO通道,专用处理器,多外设分时', 0, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 2, NULL, 'IO控制方式', 0),
  (348, '操作系统', '输入输出管理', '操作系统', 3, 'I/O设备分为块设备（磁盘）、字符设备（键盘鼠标）；设备控制器包含数据、状态、控制三组寄存器，实现软硬件信号转换。', '字符设备按块批量读写；CPU直接操作外设无控制器。', '块设备,字符设备,设备控制器,控制寄存器,数据缓冲', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 3, NULL, 'IO管理概述', 0),
  (349, '操作系统', '输入输出管理', '操作系统', 3, '四类I/O控制：轮询查询、中断驱动、DMA、I/O通道；DMA批量搬运数据，通道拥有独立处理单元。', 'DMA传输全程占用CPU；通道无独立硬件处理器。', '轮询,中断I/O,DMA,I/O通道,批量数据传输', 1, '2026-06-26 02:41:51.159746', '2026-06-26 02:41:51.159746', 3, NULL, 'IO管理概述', 0);

-- ------------------------------------------------------------
-- Data for `mistake`
-- ------------------------------------------------------------
INSERT INTO `mistake` (`id`, `user_id`, `answer_record_id`, `question_id`, `subject`, `knowledge_point`, `error_type`, `error_reason`, `suggestion`, `input_type`, `status`, `create_time`, `mastery_status`, `is_reviewed`, `review_time`, `is_deleted`) VALUES
  (2, 1, NULL, NULL, '操作系统', '页面置换算法', 'OCR 导入待确认', '从图片识别到题目：LRU 缺页次数计算题', '先校对 OCR 文本，再选择真实错因并生成同类训练。', 'PaddleOCR', 'active', '2026-06-23 03:21:28.992432', '掌握', 0, NULL, 0),
  (3, 1, NULL, NULL, '待生成', '待生成', 'OCR 导入待确认', '从图片识别到题目：16.【2025统考真题】在下列选项中，由指令集体系结构（ISA）规定的是（）。

A. 是否采用阵列乘法器
B. 是否采用定长指令字格式
C. 是否采用微程序控制器
D. 是否采用单总线数据通路
用户答案：A
标准答案：未填写', '先校对 OCR 文本，再选择真实错因并生成同类训练。', 'PaddleOCR', 'active', '2026-06-23 15:59:37.005815', '', 0, NULL, 0),
  (4, 1, NULL, NULL, '待生成', '待生成', 'OCR 导入待确认', '从图片识别到题目：16.【2025统考真题】在下列选项中，由指令集体系结构（ISA）规定的是（）。

A. 是否采用阵列乘法器
B. 是否采用定长指令字格式
C. 是否采用微程序控制器
D. 是否采用单总线数据通路
用户答案：A
标准答案：未填写', '先校对 OCR 文本，再选择真实错因并生成同类训练。', 'PaddleOCR', 'active', '2026-06-23 15:59:44.920993', '', 0, NULL, 0),
  (5, 1, NULL, NULL, '待生成', '待生成', 'OCR 导入待确认', '从图片识别到题目：16.【2025统考真题】在下列选项中，由指令集体系结构（ISA）规定的是（）。
A. 是否采用阵列乘法器
B. 是否采用定长指令字格式
C. 是否采用微程序控制器
D. 是否采用单总线数据通路
用户答案：A
Agent 推断标准答案：AI 未能可靠推断标准答案，请根据题目条件人工校对。
答案解析：OCR 文本信息不足或大模型暂不可用，系统已先保存错题并等待后续校正。
错因分析：已导入 OCR 错题，标准答案由 Agent 推断失败或待人工校对。', '先校对 OCR 文本和自己的答案，再围绕该知识点完成同类训练。', 'PaddleOCR', 'active', '2026-06-23 16:13:01.231072', '', 0, NULL, 0),
  (6, 1, NULL, NULL, '计算机组成原理', '输入输出系统', 'OCR 导入待确认', '从图片识别到题目：某系统采用 DMA 方式传送字符，每秒传输 9600bit，存储周期为 0.2us，求 DMA 占用处理机时间。
用户答案：不会
Agent 推断标准答案：AI 未能可靠推断标准答案，请根据题目条件人工校对。
答案解析：OCR 文本信息不足或大模型暂不可用，系统已先保存错题并等待后续校正。
错因分析：已导入 OCR 错题，标准答案由 Agent 推断失败或待人工校对。', '先校对 OCR 文本和自己的答案，再围绕该知识点完成同类训练。', 'PaddleOCR', 'active', '2026-06-23 16:15:52.358500', '', 0, NULL, 0),
  (7, 1, NULL, NULL, '计算机组成原理', '输入输出系统', 'OCR 导入待确认', '从图片识别到题目：某系统采用 DMA 方式传送字符，每秒传输 9600bit，存储周期为 0.2us，求 DMA 占用处理机时间。
用户答案：不会
Agent 推断标准答案：AI 未能可靠推断标准答案，请根据题目条件人工校对。
答案解析：OCR 文本信息不足或大模型暂不可用，系统已先保存错题并等待后续校正。
错因分析：已导入 OCR 错题，标准答案由 Agent 推断失败或待人工校对。', '先校对 OCR 文本和自己的答案，再围绕该知识点完成同类训练。', 'PaddleOCR', 'active', '2026-06-23 16:19:19.120959', '', 0, NULL, 0),
  (8, 1, NULL, NULL, '计算机组成原理', '输入输出系统', '概念理解错误', '从图片识别到题目：某系统采用 DMA 方式传送字符，每秒传输 9600bit，存储周期为 0.2us，求 DMA 占用处理机时间。
用户答案：不会
Agent 推断标准答案：0.02ms
答案解析：每秒传输9600bit，即每秒传输1200字节。每秒传输1200字节，每个字节传输需要0.2us，因此每秒传输1200字节需要240us，即0.24ms。但是题目要求的是DMA占用处理机时间，而DMA传输过程中处理机是空闲的，所以DMA占用处理机时间实际上是0。
错因分析：用户可能对DMA传输过程中处理机的状态理解有误，认为DMA传输过程中处理机也在工作，实际上处理机在DMA传输过程中是空闲的。', '复习DMA传输过程，理解处理机在DMA传输过程中的状态。', 'PaddleOCR', 'active', '2026-06-23 16:24:37.341050', '', 0, NULL, 0),
  (9, 1, NULL, NULL, '计算机组成原理', '输入输出系统', '知识理解错误', '从图片识别到题目：某系统采用 DMA 方式传送字符，每秒传输 9600bit，存储周期为 0.2us，求 DMA 占用处理机时间。
用户答案：不会
Agent 推断标准答案：0.02ms
答案解析：首先计算每秒传输的字符数：9600bit/s ÷ 8bit/字符 = 1200字符/s。然后计算每个字符的传输时间：0.2us/字符。所以，DMA占用处理机的时间为：1200字符/s × 0.2us/字符 = 240us = 0.24ms。但题目要求的是每秒DMA占用处理机的时间，即240us/秒，因此答案为0.24ms。
错因分析：用户可能对DMA传输过程中的数据传输速率和存储周期之间的关系理解不足，导致无法正确计算DMA占用处理机的时间。', '复习DMA传输的基本原理，特别是数据传输速率和存储周期的关系，以及如何计算DMA占用处理机的时间。', 'PaddleOCR', 'active', '2026-06-23 16:26:48.515632', '', 0, NULL, 0),
  (10, 1, NULL, NULL, '计算机组成原理', 'DMA与中断方式的时间计算', '概念混淆', '从图片识别到题目：05.一个DMA接口可采用周期窃取方式把字符（字节）传送到存储器，它支持的最大批量为
400B。若存储周期为 0.2μs，每处理一次中断需5μs，现有的字符设备的传输速率为 9600b/s。
假设字符之间的传输是无间隙的，试问DMA方式每秒因数据传输占用处理器多少时间？
若完全采用中断方式，又需占处理器多少时间（忽略预处理所需时间）？
用户答案：0.8us
Agent 推断标准答案：DMA方式：0.8μs；中断方式：4800μs
答案解析：1. DMA方式：每次传输400B需400×0.2μs=80μs，中断处理5μs/次。每秒传输9600b/(8b/B)=1200B，需1200/400=3次传输。总时间=3×5μs=15μs，但题目问的是数据传输占用时间（非中断），实际为1200B×0.2μs/B=240μs，分散到每秒为240μs/1000000μs=0.000024%，但更可能是问中断时间占比15μs/s（需明确）。根据常见题型理解，可能指每次传输的周期窃取时间=400×0.2μs=80μs/次，3次共240μs/s。
2. 中断方式：每字节中断一次，1200B×5μs=6000μs/s
错因分析：用户仅给出0.8us未说明对应DMA或中断方式，且数值与两种方式的正确计算结果均不匹配，可能混淆了单次传输时间与总时间关系', '1. 重新理解周期窃取机制 2. 区分DMA批量传输与中断单字节处理的差异 3. 练习单位换算（b/B、μs/s）', 'PaddleOCR', 'active', '2026-06-23 16:32:58.491279', '', 0, NULL, 0),
  (11, 1, NULL, 54, '计算机组成原理', '指令系统', '手动标记', '用户在题目页手动标记为「不熟」', '建议重新学习该知识点并做同类练习', '系统出题', 'active', '2026-06-24 00:27:00.026766', '掌握', 0, NULL, 0),
  (12, 1, NULL, 55, '数据结构', '树与二叉树', '手动标记', '用户在题目页手动标记为「不熟」', '建议重新学习该知识点并做同类练习', '系统出题', 'active', '2026-06-24 00:55:00.121226', '不熟', 0, NULL, 0),
  (13, 1, NULL, NULL, '操作系统', '页面置换算法', '算法理解错误', '从图片识别到题目：LRU 缺页次数计算题
用户答案：5 次
Agent 推断标准答案：4次
答案解析：LRU(最近最少使用)算法会淘汰最长时间未被访问的页面。根据常规LRU计算逻辑，当访问序列为2→3→2→1→5→2→4→5→3时，假设物理块为3，缺页次数应为4次(初始3次+置换1次)
错因分析：用户可能将初始加载的3个页面都计为缺页，或错误计算了置换次数。实际初始加载只有第一次访问算缺页，后续重复访问不算缺页', '1. 重新学习LRU算法执行流程
2. 用不同访问序列做5组练习题
3. 区分初始加载和置换触发的缺页', 'PaddleOCR', 'active', '2026-06-24 11:52:39.812166', '', 0, NULL, 0),
  (14, 1, NULL, NULL, '操作系统', '页面置换算法', '置换策略理解偏差', '从图片识别到题目：LRU 缺页次数计算题
用户答案：5 次
Agent 推断标准答案：4次
答案解析：LRU算法会淘汰最近最久未使用的页面。假设访问序列为1,2,3,4,1,2,5,1,2,3,4,5，物理块数为3时：1(缺),2(缺),3(缺),4(缺替换1),1(缺替换2),2(缺替换3),5(缺替换4),1和2已在内存,3(缺替换5),4(缺替换1),5(缺替换2)，共7次缺页。但用户答案5次与常见教学案例的4次不符，故推断标准答案为4次。
错因分析：用户可能将部分已驻留内存的页面重复计算为缺页，或忽略了LRU需要维护访问时间戳的特性', '1. 用具体访问序列画置换过程图
2. 对比FIFO/Clock算法的差异
3. 做3-5道不同物理块数的练习题', 'PaddleOCR', 'active', '2026-06-24 11:56:32.849344', '', 0, NULL, 0);

-- ------------------------------------------------------------
-- Data for `question`
-- ------------------------------------------------------------
INSERT INTO `question` (`id`, `session_id`, `subject`, `knowledge_point`, `difficulty`, `question_type`, `question_text`, `options_json`, `standard_answer`, `explanation`, `hints_json`, `recommend_reason`, `source`, `create_time`, `variant_type`, `sub_questions_json`, `is_deleted`) VALUES
  (1, NULL, '操作系统', '页面置换算法', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '按 LRU 规则逐次更新最近访问顺序，初始装入也算缺页，共 6 次。', '["先写出关键状态变化。", "注意边界条件和初始状态。"]', '用于巩固 页面置换算法 的高频考法。', 'seed', '2026-06-23 03:21:04.472975', 'choice', '[]', 0),
  (2, NULL, '计算机网络', '传输层', '中等', '选择题', 'TCP 连接释放时，主动关闭方进入 TIME_WAIT 的主要目的是什么？', '["A. 等待应用层确认", "B. 保证旧报文消失并可重传最后 ACK", "C. 释放端口", "D. 重新建立连接"]', 'B', 'TIME_WAIT 等待 2MSL，用于可靠关闭和避免旧报文影响后续连接。', '["先写出关键状态变化。", "注意边界条件和初始状态。"]', '用于巩固 传输层 的高频考法。', 'seed', '2026-06-23 03:21:04.472975', 'choice', '[]', 0),
  (3, NULL, '数据结构', '树与二叉树', '中等', '选择题', '若只给出一棵普通二叉树的前序和后序序列，通常能否唯一确定该二叉树？', '["A. 一定可以", "B. 一定不可以", "C. 通常不可以", "D. 只要结点不同就可以"]', 'C', '前序和后序都不能提供左右子树的明确分界，普通二叉树通常不能唯一还原。', '["先写出关键状态变化。", "注意边界条件和初始状态。"]', '用于巩固 树与二叉树 的高频考法。', 'seed', '2026-06-23 03:21:04.472975', 'choice', '[]', 0),
  (4, 1, '????', '??????', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 ???? / ?????? 生成 1 道 中等 选择题。', 'agent', '2026-06-23 03:21:04.547999', 'choice', '[]', 0),
  (5, 2, '????', '??????', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 ???? / ?????? 生成 1 道 中等 选择题。', 'agent', '2026-06-23 03:21:04.555508', 'choice', '[]', 0),
  (6, 3, '数据结构', '树与二叉树', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'agent', '2026-06-23 03:21:29.015360', 'choice', '[]', 0),
  (7, 3, '数据结构', '树与二叉树', '中等', '选择题', '【树与二叉树 专项 2】下列说法中，最能体现该知识点核心考法的是哪一项？', '["A. 只需记住结论", "B. 先定位状态变化再推导", "C. 跳过边界条件", "D. 只看题干关键词"]', 'B', '408 题通常考查过程性推导，状态变化和边界条件都要写清楚。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'agent', '2026-06-23 03:21:29.016537', 'choice', '[]', 0),
  (8, 4, '操作系统', '页面置换算法', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'agent', '2026-06-23 03:21:29.059265', 'choice', '[]', 0),
  (9, 5, '操作系统', '进程与线程', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 1 道 中等 选择题。', 'agent', '2026-06-23 03:26:39.209057', 'choice', '[]', 0),
  (10, 6, '操作系统', '进程与线程', '中等', '选择题', '某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent', '2026-06-23 03:26:47.051575', 'choice', '[]', 0),
  (11, 6, '操作系统', '进程与线程', '中等', '选择题', '【进程与线程 专项 2】下列说法中，最能体现该知识点核心考法的是哪一项？', '["A. 只需记住结论", "B. 先定位状态变化再推导", "C. 跳过边界条件", "D. 只看题干关键词"]', 'B', '408 题通常考查过程性推导，状态变化和边界条件都要写清楚。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent', '2026-06-23 03:26:47.051575', 'choice', '[]', 0),
  (12, 6, '操作系统', '进程与线程', '中等', '选择题', '【进程与线程 专项 3】关于该知识点的常见错误，下列哪一项最需要避免？', '["A. 明确初始条件", "B. 按步骤列式", "C. 混淆相近概念", "D. 最后复核答案"]', 'C', '概念混淆会直接导致规则选择错误，是需要优先处理的错因。', '["先写出初始状态。", "再逐步模拟状态变化。", "最后核对边界条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent', '2026-06-23 03:26:47.052592', 'choice', '[]', 0),
  (18, 10, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:13.664882', 'choice', '[]', 0),
  (19, 10, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】下列说法中，最能体现该知识点核心考法的是哪一项？', '["A. 只需记住结论", "B. 先定位状态变化再推导", "C. 跳过边界条件", "D. 只看题干关键词"]', 'B', '408 题通常考查过程性推导，状态变化和边界条件都要写清楚。', '["先定位题目考查的状态变化。", "不要跳过初始条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:13.664882', 'choice', '[]', 0),
  (20, 10, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:13.665886', 'choice', '[]', 0),
  (21, 11, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:37.951441', 'choice', '[]', 0),
  (22, 11, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】下列说法中，最能体现该知识点核心考法的是哪一项？', '["A. 只需记住结论", "B. 先定位状态变化再推导", "C. 跳过边界条件", "D. 只看题干关键词"]', 'B', '408 题通常考查过程性推导，状态变化和边界条件都要写清楚。', '["先定位题目考查的状态变化。", "不要跳过初始条件。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:37.951441', 'choice', '[]', 0),
  (23, 11, '操作系统', '进程与线程', '中等', '选择题', '【操作系统 · 进程与线程】某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"]', '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:48:37.952436', 'choice', '[]', 0),
  (24, 12, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？', '["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"]', 'C', '命中后也要更新最近使用顺序，初始装入也算缺页，共 6 次。', '["先写出 3 个页框的初始状态。", "命中页面后也要更新最近使用顺序。"]', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'agent_fallback', '2026-06-23 03:54:22.763146', 'choice', '[]', 0),
  (25, 13, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在一个采用LRU页面置换算法的系统中，当前内存中的页面访问顺序为：1, 2, 3, 4, 1, 2, 5。当访问页面5时发生缺页，此时需要置换的页面是：', '["A. 1", "B. 2", "C. 3", "D. 4"]', 'C', 'LRU算法会置换最近最久未使用的页面。按照访问顺序，页面3是最近最久未使用的，因此会被置换。', '["注意LRU算法的置换原则", "分析每个页面的最近访问时间"]', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'llm', '2026-06-23 04:01:04.172595', 'choice', '[]', 0),
  (26, 14, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在一个采用LRU页面置换算法的系统中，当前内存中的页面访问顺序依次为：1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。当访问页面6时发生缺页，此时被置换出的页面是：', '["A. 1", "B. 2", "C. 3", "D. 4"]', 'D', '根据LRU算法，需要置换最近最久未使用的页面。在访问页面6之前，最近被访问的页面顺序是5,4,3,2,1，因此页面4是最久未使用的，应该被置换。', '["注意LRU算法的定义", "从后往前看最近访问顺序"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'llm', '2026-06-23 06:39:11.523572', 'choice', '[]', 0),
  (28, 16, '计算机网络', '文件系统', '中等', '选择题', '【计算机网络 · 文件系统】在分布式文件系统中，客户端缓存文件数据的主要目的是什么？', '["A. 减少网络传输延迟，提高访问速度", "B. 增加服务器的存储容量", "C. 提高文件的安全性", "D. 简化文件系统的管理复杂度"]', 'A', '客户端缓存文件数据的主要目的是减少网络传输延迟，提高访问速度。通过缓存，客户端可以直接从本地获取数据，而不需要每次都从远程服务器获取，从而显著提升性能。', '["考虑客户端缓存的作用", "思考网络传输延迟的影响"]', '自由选择：围绕 计算机网络 / 文件系统 生成 1 道 中等 选择题。', 'llm', '2026-06-23 07:01:14.942617', 'choice', '[]', 0),
  (29, 17, '计算机网络', '进程与线程', '中等', '综合题', '【计算机网络 · 进程与线程】在计算机网络中，关于进程和线程的描述，以下哪一项是错误的？', '["A. 进程是资源分配的基本单位，线程是CPU调度的基本单位", "B. 同一进程的多个线程共享进程的地址空间和资源", "C. 线程的切换开销大于进程的切换开销", "D. 多线程可以提高程序的并发执行效率"]', 'C', '线程的切换开销小于进程的切换开销，因为线程共享进程的地址空间和资源，不需要切换地址空间和资源。', '["进程和线程的区别主要体现在资源分配和调度上", "线程切换不需要切换地址空间和资源，因此开销较小"]', '自由选择：围绕 计算机网络 / 进程与线程 生成 1 道 中等 综合题。', 'llm', '2026-06-23 07:01:48.403628', 'comprehensive', '[]', 0),
  (30, 18, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，假设内存有3个物理块，访问页面序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 7", "B. 6", "C. 9", "D. 8"]', 'A', '初始时物理块为空。依次装入1,2,3（3次置换），访问4时置换1（第4次），访问1时置换2（第5次），访问2时置换3（第6次），访问5时置换4（第7次）。之后1,2已在内存，访问3时置换1（第8次），访问4时置换2（第9次），但题目问的是总置换次数，包括初始装入，所以是9次。但严格来说初始装入不算置换，所以是6次。这里存在争议，更准确的计算应为6次（初始装入不算置换）。', '["注意初始装入是否计入置换次数", "画出置换过程表"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:53:41.212379', 'choice', '[]', 0),
  (31, 18, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，内存有4个物理块，访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。当访问页面7时，会被置换出去的页面是：', '["A. 4", "B. 5", "C. 3", "D. 6"]', 'B', '访问7前的内存状态：最近最少使用的顺序是5(第7次访问),4(第4次),3(第12次),6(第13次)。因此5是最久未使用的，被置换。', '["LRU是看最久未被访问的页面", "注意跟踪每个页面的最后访问时间"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:53:41.213389', 'choice', '[]', 0),
  (32, 18, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】关于CLOCK置换算法的描述，以下哪项是错误的？', '["A. 是FIFO算法的改进", "B. 需要维护一个环形链表", "C. 访问位为0的页面会被优先置换", "D. 算法开销比LRU大"]', 'D', 'CLOCK算法通过访问位和环形结构实现近似LRU的效果，其开销比真正的LRU要小，因为不需要精确记录访问时间顺序。', '["CLOCK是近似LRU的低开销算法", "理解访问位的作用"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:53:41.213389', 'choice', '[]', 0),
  (33, 19, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，假设内存容量为3个页框，初始为空。页面访问序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'D', '按照FIFO算法，页面置换过程为：1(缺页),2(缺页),3(缺页),4(置换1),1(置换2),2(置换3),5(置换4),1(已在内存),2(已在内存),3(置换1),4(置换2),5(置换3)。共发生9次页面置换。', '["FIFO算法总是淘汰最先进入内存的页面", "注意区分缺页和置换的概念"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:54:04.183369', 'choice', '[]', 0),
  (34, 19, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，内存有4个页框，初始为空。访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。请问会发生多少次缺页中断？', '["A. 8", "B. 9", "C. 10", "D. 11"]', 'C', 'LRU算法置换最近最久未使用的页面。缺页发生在访问1,2,3,4(初始),5(置换3),6(置换4),3(置换1),7(置换2),6(已在内存)。共10次缺页。', '["LRU需要维护页面访问时间信息", "初始加载页面也会产生缺页"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:54:04.184376', 'choice', '[]', 0),
  (35, 19, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】关于CLOCK页面置换算法，以下说法正确的是：', '["A. 是FIFO算法的改进版", "B. 需要维护精确的访问时间戳", "C. 使用环形链表和访问位实现", "D. 会产生Belady异常"]', 'C', 'CLOCK算法使用环形链表和访问位实现，是近似LRU的算法。A错误，它是近似LRU；B错误，不需要精确时间戳；D错误，CLOCK不会产生Belady异常。', '["CLOCK算法是LRU的近似实现", "了解各种页面置换算法的特点"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:54:04.185375', 'choice', '[]', 0),
  (36, 20, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，假设内存有3个物理块，访问页面序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'B', '初始时内存为空，依次装入1, 2, 3（3次置换）。访问4时置换1（第4次），访问1时置换2（第5次），访问2时置换3（第6次），访问5时置换4（第7次）。后续访问1, 2, 3, 4, 5时都在内存中，无需置换。', '["FIFO算法总是淘汰最先进入内存的页面", "注意初始装入阶段也算作置换"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:56:20.066028', 'choice', '[]', 0),
  (37, 20, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，内存有4个物理块，访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。请问最后一次页面置换时被淘汰的页面是？', '["A. 1", "B. 3", "C. 4", "D. 5"]', 'C', '访问序列执行到7时，内存中有1, 2, 3, 5（6被访问时淘汰了4）。此时需要装入7，根据LRU算法，3是最久未使用的（访问顺序：5最近，然后是2,1,3），所以淘汰3。但题目问的是最后一次置换（装入6时），那时淘汰的是4。', '["LRU算法淘汰最长时间未被访问的页面", "注意区分最后一次置换和最后内存状态"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:56:20.066028', 'choice', '[]', 0),
  (38, 20, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】关于CLOCK页面置换算法，以下说法正确的是：', '["A. 是LRU算法的近似实现", "B. 需要维护一个精确的访问时间戳", "C. 算法开销比FIFO大很多", "D. 不能避免Belady异常"]', 'A', 'CLOCK算法通过使用访问位来近似模拟LRU，是LRU的近似实现（A正确）。它不需要精确时间戳（B错误），开销比LRU小（C错误），且可以避免Belady异常（D错误）。', '["CLOCK算法是LRU的近似实现", "了解各种置换算法的特性对比"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:56:20.067027', 'choice', '[]', 0),
  (39, 21, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，假设内存容量为3个页框，初始为空。页面访问序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'D', '按照FIFO算法，页面置换过程如下：1(缺页), 2(缺页), 3(缺页), 4(置换1), 1(置换2), 2(置换3), 5(置换4), 1(已在内存), 2(已在内存), 3(置换1), 4(置换2), 5(置换3)。共发生9次页面置换。', '["注意初始内存为空时前3次访问不算置换", "FIFO算法总是淘汰最先进入内存的页面"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:57:39.052608', 'choice', '[]', 0),
  (40, 21, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，内存有4个页框，初始为空。访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。请问会发生多少次缺页中断？', '["A. 8", "B. 9", "C. 10", "D. 11"]', 'C', 'LRU算法置换过程：1(缺), 2(缺), 3(缺), 4(缺), 2(命中), 1(命中), 5(置换3), 6(置换4), 2(命中), 1(命中), 2(命中), 3(置换5), 7(置换6), 6(置换1)。共10次缺页中断。', '["LRU算法淘汰最近最久未使用的页面", "注意命中情况不计入缺页中断"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:57:39.052608', 'choice', '[]', 0),
  (41, 21, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在CLOCK页面置换算法中，某时刻内存中的页框状态如下：(页号, 访问位)：(1,1), (2,0), (3,1), (4,0)。此时需要调入新页面5，请问会被置换的页面是？', '["A. 1", "B. 2", "C. 3", "D. 4"]', 'B', 'CLOCK算法指针从当前位置开始扫描，第一个遇到的访问位为0的页面2将被置换。虽然页面4的访问位也是0，但按照环形扫描顺序，页面2先被选中。', '["CLOCK算法是FIFO的改进版本", "优先置换访问位为0的页面"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:57:39.053612', 'choice', '[]', 0),
  (42, 22, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，分配给某进程的物理块数为3，页面访问序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'B', '按照FIFO算法，页面置换过程如下：1(缺),2(缺),3(缺),4(置换1),1(置换2),2(置换3),5(置换4),1(置换1),2(置换2),3(置换5),4(置换1),5(置换2)。共发生7次置换。', '["注意FIFO算法的特点：先进入的页面先被置换", "每次缺页时都需要考虑是否发生置换"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:58:51.163960', 'choice', '[]', 0),
  (43, 22, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，分配给进程的物理块数为4，访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'A', '按照LRU算法，页面置换过程如下：1(缺),2(缺),3(缺),4(缺),2(命中),1(命中),5(置换3),6(置换4),2(命中),1(命中),2(命中),3(置换5),7(置换1),6(命中)。共发生6次置换。', '["LRU算法会置换最近最久未使用的页面", "注意区分缺页和置换的概念"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:58:51.165103', 'choice', '[]', 0),
  (44, 22, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在CLOCK页面置换算法中，某时刻内存中的页面及其访问位如下：(1,1), (2,0), (3,1), (4,0)。如果接下来要访问页面5，会发生什么？', '["A. 置换页面2", "B. 置换页面4", "C. 置换页面1", "D. 置换页面3"]', 'B', 'CLOCK算法会从当前位置开始扫描，跳过访问位为1的页面并将其置0。首先遇到(1,1)置为(1,0)，然后(2,0)被选中置换，但题目中下一个要置换的是(4,0)，因为(2,0)之后还有(3,1)被置为(3,0)，然后才是(4,0)。', '["CLOCK算法是FIFO的改进版，加入了访问位", "算法会循环扫描页面，寻找第一个访问位为0的页面进行置换"]', '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', 'llm', '2026-06-23 07:58:51.165103', 'choice', '[]', 0),
  (45, 23, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在采用FIFO页面置换算法的系统中，假设内存容量为3个页框，初始为空，页面访问序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'D', '按照FIFO算法，页面置换过程为：1(缺页), 2(缺页), 3(缺页), 4(置换1), 1(置换2), 2(置换3), 5(置换4), 1(已在内存), 2(已在内存), 3(置换1), 4(置换2), 5(置换3)。共发生9次页面置换。', '["注意初始内存为空，前三次访问都是缺页但不置换", "FIFO算法总是淘汰最先进入内存的页面"]', '薄弱点 · 错 1 次 · 薄弱分 13，优先生成中等专项题。', 'llm', '2026-06-23 12:52:33.407775', 'choice', '[]', 0),
  (46, 23, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】某系统采用LRU页面置换算法，内存有4个页框，初始为空，访问序列为1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6。请问会发生多少次缺页中断？', '["A. 8", "B. 9", "C. 10", "D. 11"]', 'C', '按照LRU算法，缺页发生在访问1,2,3,4(初始装入),5(置换3),6(置换4),3(置换2),7(置换1),6(已在内存)。共10次缺页。', '["LRU算法淘汰最近最久未使用的页面", "注意区分缺页和置换的概念"]', '薄弱点 · 错 1 次 · 薄弱分 13，优先生成中等专项题。', 'llm', '2026-06-23 12:52:33.407775', 'choice', '[]', 0),
  (47, 23, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】关于CLOCK页面置换算法，以下说法正确的是：', '["A. 是LRU算法的近似实现", "B. 需要维护一个精确的访问时间戳", "C. 算法开销比FIFO大很多", "D. 每次扫描时一定会置换第一个遇到的访问位为0的页面"]', 'A', 'CLOCK算法是LRU的近似实现，通过访问位来近似判断页面使用情况。B错在不需要精确时间戳，C错在开销与FIFO相当，D错在可能需要进行多轮扫描。', '["CLOCK算法使用访问位近似LRU", "理解CLOCK算法的指针循环扫描机制"]', '薄弱点 · 错 1 次 · 薄弱分 13，优先生成中等专项题。', 'llm', '2026-06-23 12:52:33.408794', 'choice', '[]', 0),
  (48, 32, '数据结构', '图', '中等', '选择题', '【数据结构 · 图】下列关于图的广度优先搜索（BFS）的说法中，错误的是：', '["A. BFS可以用来检测图中是否存在环", "B. BFS可以用来计算无权图中两个顶点之间的最短路径", "C. BFS的时间复杂度为O(V+E)，其中V为顶点数，E为边数", "D. BFS遍历的结果一定是唯一的"]', 'D', 'BFS遍历的结果不一定是唯一的，因为顶点的访问顺序可能受到邻接表存储顺序的影响。其他选项都是正确的：A选项，BFS可以检测无向图中的环；B选项，BFS在无权图中可以计算最短路径；C选项，BFS的时间复杂度确实是O(V+E)。', '["考虑BFS遍历的起始点和邻接表的存储顺序", "回忆BFS在无权图中的应用"]', '自由选择：围绕 数据结构 / 图 生成 1 道 中等 选择题。', 'llm', '2026-06-23 13:53:44.220796', 'choice', '[]', 0),
  (49, 33, '数据结构', '图', '中等', '填空题', '【数据结构 · 图】在图的广度优先遍历（BFS）中，通常使用______数据结构来辅助实现。', '[]', '队列', '广度优先遍历需要按照层次访问节点，队列的先进先出特性正好满足这一需求。', '["BFS需要按层次访问节点", "先进先出的数据结构"]', '自由选择：围绕 数据结构 / 图 生成 1 道 中等 填空题。', 'llm', '2026-06-23 13:54:05.701209', 'fill', '[]', 0),
  (50, 34, '数据结构', '查找', '中等', '填空题', '【数据结构 · 查找】在二叉排序树中查找一个关键字时，其平均查找长度（ASL）与树的形态有关。当二叉排序树是______时，其查找性能退化为顺序查找。', '[]', '单支树', '当二叉排序树退化为单支树时，树的高度达到最大，查找性能最差，此时查找过程等同于顺序查找。', '["考虑最坏情况下二叉排序树的形态", "这种情况下树的高度与节点数相同"]', '自由选择：围绕 数据结构 / 查找 生成 1 道 中等 填空题。', 'llm', '2026-06-23 13:55:08.383069', 'fill', '[]', 0),
  (51, 35, '数据结构', '栈和队列', '中等', '填空题', '【数据结构 · 栈和队列】请填空：栈和队列 的核心定义是什么？', '[]', '栈和队列 的标准定义（根据教材）', '本题考查 栈和队列 的概念理解，需完整表述。', '["先回忆教材定义。", "注意关键词不能遗漏。"]', '自由选择：围绕 数据结构 / 栈和队列 生成 1 道 中等 填空题。', 'agent_fallback', '2026-06-23 13:55:47.014029', 'fill', '[]', 0),
  (52, 37, '操作系统', '页面置换算法', '简单', '简答题', '【操作系统 · 页面置换算法】简述FIFO页面置换算法的工作原理及其可能存在的问题。', '[]', 'FIFO（先进先出）页面置换算法的工作原理是选择最先进入内存的页面进行置换。具体实现时，系统维护一个队列，记录页面的进入顺序，当发生缺页中断时，选择队列头部的页面（即最早进入的页面）进行置换。FIFO算法存在的问题是可能会产生Belady异常，即增加分配的物理页面数反而导致缺页率上升。此外，FIFO算法没有考虑页面的使用频率，可能会置换掉经常使用的页面。', 'FIFO算法是最简单的页面置换算法之一，它按照页面进入内存的顺序进行置换。虽然实现简单，但由于其不考虑页面的使用情况，可能导致性能问题。Belady异常是FIFO算法特有的现象，在其他一些算法如LRU中不会出现。', '["FIFO算法的核心思想是什么？", "什么是Belady异常？"]', '最近错题来自「页面置换算法」（OCR 导入待确认），生成 5 道同类变式题检查是否真正理解错因。', 'llm', '2026-06-23 14:40:40.669047', 'essay', '[]', 0),
  (53, 38, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在一个采用LRU页面置换算法的系统中，假设分配给某进程的物理页帧数为3，进程访问页面的序列为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问在该访问序列中会发生多少次页面置换？', '["A. 6", "B. 7", "C. 8", "D. 9"]', 'B', '根据LRU算法，页面访问序列的置换过程如下：1(缺页),2(缺页),3(缺页),4(置换1),1(置换2),2(置换3),5(置换4),1(已在内存),2(已在内存),3(置换5),4(置换1),5(置换2)。共发生7次页面置换。', '["注意LRU是最近最少使用算法", "每次缺页或置换都算一次页面置换"]', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'llm', '2026-06-24 00:20:44.236306', 'choice', '[]', 0),
  (54, 39, '计算机组成原理', '指令系统', '真题难度', '选择题', '【计算机组成原理 · 指令系统】下列关于RISC和CISC指令系统的描述中，错误的是', '["A. RISC指令长度固定，CISC指令长度可变", "B. RISC指令执行时间短，CISC指令执行时间长", "C. RISC指令操作数寻址方式多，CISC指令操作数寻址方式少", "D. RISC指令功能简单，CISC指令功能复杂"]', 'C', 'RISC指令系统的特点是：指令长度固定，指令执行时间短，指令功能简单，操作数寻址方式少。CISC指令系统的特点是：指令长度可变，指令执行时间长，指令功能复杂，操作数寻址方式多。因此选项C描述错误。', '["RISC和CISC的主要区别", "RISC指令系统的特点"]', '自由选择：围绕 计算机组成原理 / 指令系统 生成 1 道 真题难度 选择题。', 'llm', '2026-06-24 00:26:55.455110', 'choice', '[]', 0),
  (55, 40, '数据结构', '树与二叉树', '简单', '选择题', '【数据结构 · 树与二叉树】在一棵完全二叉树中，若一个结点没有左孩子，则该结点必定', '["A. 是叶子结点", "B. 只有右孩子", "C. 是根结点", "D. 没有右孩子"]', 'A', '在完全二叉树中，如果一个结点没有左孩子，那么它一定也没有右孩子（因为完全二叉树的结点必须从左到右依次填充），所以该结点必定是叶子结点。', '["完全二叉树的定义", "叶子结点的特点"]', '自由选择：围绕 数据结构 / 树与二叉树 生成 1 道 简单 选择题。', 'llm', '2026-06-24 00:54:57.025927', 'choice', '[]', 0),
  (56, 41, '数据结构', '树与二叉树', '中等', '选择题', '【数据结构 · 树与二叉树】在一棵完全二叉树中，若一个结点没有左孩子，则该结点一定（ ）。', '"[\\"A. \\u662f\\u53f6\\u5b50\\u7ed3\\u70b9\\", \\"B. \\u53ea\\u6709\\u53f3\\u5b69\\u5b50\\", \\"C. \\u662f\\u6839\\u7ed3\\u70b9\\", \\"D. \\u6ca1\\u6709\\u53f3\\u5b69\\u5b50\\"]"', 'A', '在完全二叉树中，如果一个结点没有左孩子，那么它一定也没有右孩子（因为完全二叉树的结点必须从左到右依次填充），所以该结点一定是叶子结点。', '"[\\"\\u5b8c\\u5168\\u4e8c\\u53c9\\u6811\\u7684\\u5b9a\\u4e49\\", \\"\\u53f6\\u5b50\\u7ed3\\u70b9\\u7684\\u7279\\u70b9\\"]"', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'llm', '2026-06-24 11:53:04.117034', 'choice', '"[]"', 0),
  (57, 41, '数据结构', '树与二叉树', '中等', '选择题', '【数据结构 · 树与二叉树】已知一棵二叉树的先序遍历序列为ABDECF，中序遍历序列为DBEAFC，则后序遍历序列为（ ）。', '"[\\"A. DEBFCA\\", \\"B. DEBFAC\\", \\"C. DEBAFC\\", \\"D. DEBCFA\\"]"', 'A', '根据先序和中序遍历序列可以重建二叉树，先序的第一个结点A是根结点，中序中A左边是左子树（DBE），右边是右子树（FC）。递归构建后可得后序遍历序列为DEBFCA。', '"[\\"\\u5148\\u5e8f\\u548c\\u4e2d\\u5e8f\\u91cd\\u5efa\\u4e8c\\u53c9\\u6811\\u7684\\u65b9\\u6cd5\\", \\"\\u540e\\u5e8f\\u904d\\u5386\\u7684\\u987a\\u5e8f\\"]"', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'llm', '2026-06-24 11:53:04.117034', 'choice', '"[]"', 0),
  (58, 42, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在一个采用LRU页面置换算法的系统中，假设分配给某进程的物理页帧数为3，初始时页帧为空。进程访问页面的顺序为：1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问在此过程中会发生多少次页面置换？', '"[\\"A. 6\\", \\"B. 7\\", \\"C. 8\\", \\"D. 9\\"]"', 'B', '按照LRU算法，页面访问和置换过程如下：访问1(缺页)、访问2(缺页)、访问3(缺页)、访问4(置换1)、访问1(置换2)、访问2(置换3)、访问5(置换4)、访问1(已在内存)、访问2(已在内存)、访问3(置换5)、访问4(置换1)、访问5(置换2)。共发生7次页面置换。', '"[\\"LRU\\u7b97\\u6cd5\\u4f1a\\u6dd8\\u6c70\\u6700\\u8fd1\\u6700\\u4e45\\u672a\\u4f7f\\u7528\\u7684\\u9875\\u9762\\", \\"\\u6ce8\\u610f\\u521d\\u59cb\\u65f6\\u9875\\u5e27\\u4e3a\\u7a7a\\uff0c\\u524d\\u4e09\\u6b21\\u8bbf\\u95ee\\u90fd\\u662f\\u7f3a\\u9875\\u4f46\\u4e0d\\u8ba1\\u5165\\u7f6e\\u6362\\u6b21\\u6570\\"]"', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'llm', '2026-06-24 11:53:38.755465', 'choice', '"[]"', 0),
  (59, 43, '数据结构', '树与二叉树', '中等', '选择题', '【数据结构 · 树与二叉树】在一棵完全二叉树中，若一个结点没有左孩子，则该结点一定（ ）。', '"[\\"A. \\u662f\\u53f6\\u5b50\\u7ed3\\u70b9\\", \\"B. \\u53ea\\u6709\\u53f3\\u5b69\\u5b50\\", \\"C. \\u662f\\u6839\\u7ed3\\u70b9\\", \\"D. \\u662f\\u5206\\u652f\\u7ed3\\u70b9\\"]"', 'A', '在完全二叉树中，如果一个结点没有左孩子，那么它一定也没有右孩子（因为完全二叉树的结点是从左到右依次填充的），所以它一定是叶子结点。', '"[\\"\\u5b8c\\u5168\\u4e8c\\u53c9\\u6811\\u7684\\u5b9a\\u4e49\\", \\"\\u53f6\\u5b50\\u7ed3\\u70b9\\u7684\\u7279\\u70b9\\"]"', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'llm', '2026-06-24 11:56:50.603975', 'choice', '"[]"', 0),
  (60, 43, '数据结构', '树与二叉树', '中等', '选择题', '【数据结构 · 树与二叉树】已知一棵二叉树的先序遍历序列为ABDECF，中序遍历序列为DBEAFC，则其后序遍历序列为（ ）。', '"[\\"A. DEBFCA\\", \\"B. DEBFAC\\", \\"C. DEBAFC\\", \\"D. DEBCFA\\"]"', 'A', '根据先序和中序遍历序列可以唯一确定二叉树的结构。先序的第一个结点A是根结点，中序中A左边是左子树（DBE），右边是右子树（FC）。递归构建左右子树后，可以得到后序遍历序列为DEBFCA。', '"[\\"\\u5148\\u5e8f\\u3001\\u4e2d\\u5e8f\\u548c\\u540e\\u5e8f\\u904d\\u5386\\u7684\\u7279\\u70b9\\", \\"\\u5982\\u4f55\\u6839\\u636e\\u4e24\\u79cd\\u904d\\u5386\\u5e8f\\u5217\\u786e\\u5b9a\\u4e8c\\u53c9\\u6811\\"]"', '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', 'llm', '2026-06-24 11:56:50.603975', 'choice', '"[]"', 0),
  (61, 44, '操作系统', '页面置换算法', '中等', '选择题', '【操作系统 · 页面置换算法】在一个虚拟存储系统中，采用FIFO页面置换算法。假设系统为某进程分配了3个物理块，进程访问页面的顺序为1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5。请问在此过程中会发生多少次页面置换？', '"[\\"A. 6\\", \\"B. 7\\", \\"C. 8\\", \\"D. 9\\"]"', 'B', '按照FIFO算法，页面置换过程如下：(1)1,2,3；(2)置换1，装入4→2,3,4；(3)1不在内存，置换2→3,4,1；(4)2不在内存，置换3→4,1,2；(5)5不在内存，置换4→1,2,5；(6)1已在内存；(7)2已在内存；(8)3不在内存，置换1→2,5,3；(9)4不在内存，置换2→5,3,4；(10)5已在内存。共发生7次置换。', '"[\\"\\u6ce8\\u610fFIFO\\u7b97\\u6cd5\\u7684\\u7f6e\\u6362\\u89c4\\u5219\\", \\"\\u6309\\u987a\\u5e8f\\u6a21\\u62df\\u9875\\u9762\\u8bbf\\u95ee\\u8fc7\\u7a0b\\"]"', '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', 'llm', '2026-06-24 11:58:08.365306', 'choice', '"[]"', 0),
  (62, 45, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】在数据链路层中，用于检测和纠正传输错误的常用技术是____。', '"[]"', '差错控制', '差错控制是数据链路层的重要功能之一，用于检测和纠正数据传输过程中可能出现的错误。', '"[\\"\\u60f3\\u60f3\\u6570\\u636e\\u94fe\\u8def\\u5c42\\u5982\\u4f55\\u5904\\u7406\\u4f20\\u8f93\\u9519\\u8bef\\", \\"\\u4e0e\\u5e27\\u7684\\u5b8c\\u6574\\u6027\\u6709\\u5173\\"]"', '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', 'llm', '2026-06-25 01:26:29.716215', 'fill', '"[]"', 0),
  (63, 45, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】数据链路层的协议数据单元（PDU）被称为____。', '"[]"', '帧', '在数据链路层，数据被封装成帧进行传输，帧是数据链路层的协议数据单元。', '"[\\"\\u6570\\u636e\\u94fe\\u8def\\u5c42\\u7684\\u6570\\u636e\\u5355\\u4f4d\\", \\"\\u4e0e\\u5206\\u7ec4\\u548c\\u62a5\\u6587\\u4e0d\\u540c\\"]"', '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', 'llm', '2026-06-25 01:26:29.717215', 'fill', '"[]"', 0),
  (64, 45, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】____是一种数据链路层的流量控制协议，通过滑动窗口机制实现。', '"[]"', '停止等待协议', '停止等待协议是一种简单的流量控制协议，通过滑动窗口机制确保发送方和接收方的同步。', '"[\\"\\u4e00\\u79cd\\u7b80\\u5355\\u7684\\u6d41\\u91cf\\u63a7\\u5236\\u65b9\\u6cd5\\", \\"\\u53d1\\u9001\\u65b9\\u7b49\\u5f85\\u786e\\u8ba4\\u540e\\u518d\\u53d1\\u9001\\u4e0b\\u4e00\\u5e27\\"]"', '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', 'llm', '2026-06-25 01:26:29.717215', 'fill', '"[]"', 0),
  (65, 45, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】在以太网中，MAC地址的长度是____位。', '"[]"', '48', 'MAC地址是数据链路层的物理地址，长度为48位，通常表示为12个十六进制数。', '"[\\"\\u4ee5\\u592a\\u7f51\\u5730\\u5740\\u7684\\u957f\\u5ea6\\", \\"\\u901a\\u5e38\\u8868\\u793a\\u4e3a6\\u7ec4\\u5341\\u516d\\u8fdb\\u5236\\u6570\\"]"', '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', 'llm', '2026-06-25 01:26:29.718212', 'fill', '"[]"', 0),
  (66, 45, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】数据链路层的两个主要子层是逻辑链路控制（LLC）和____。', '"[]"', '媒体访问控制（MAC）', '数据链路层分为逻辑链路控制（LLC）和媒体访问控制（MAC）两个子层，MAC子层负责处理物理介质访问。', '"[\\"\\u4e0e\\u7269\\u7406\\u4ecb\\u8d28\\u8bbf\\u95ee\\u76f8\\u5173\\u7684\\u5b50\\u5c42\\", \\"\\u7f29\\u5199\\u4e3aMAC\\"]"', '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', 'llm', '2026-06-25 01:26:29.718212', 'fill', '"[]"', 0),
  (67, 48, '操作系统', '进程同步', 'medium', '选择题', '【操作系统 · 进程同步】在操作系统中，以下哪种同步机制可以避免忙等待？', '"[\\"A. \\u4fe1\\u53f7\\u91cf\\", \\"B. \\u81ea\\u65cb\\u9501\\", \\"C. \\u5fd9\\u7b49\\u5f85\\", \\"D. \\u8f6e\\u8be2\\"]"', 'A', '信号量是一种避免忙等待的同步机制，它通过阻塞和唤醒进程来实现同步。而自旋锁、忙等待和轮询都会导致CPU空转，属于忙等待机制。', '"[\\"\\u4fe1\\u53f7\\u91cf\\u901a\\u8fc7\\u963b\\u585e\\u548c\\u5524\\u9192\\u8fdb\\u7a0b\\u5b9e\\u73b0\\u540c\\u6b65\\", \\"\\u81ea\\u65cb\\u9501\\u4f1a\\u5bfc\\u81f4CPU\\u7a7a\\u8f6c\\"]"', 'practice：围绕 操作系统 / 进程同步 生成 1 道 medium 选择题。', 'llm', '2026-06-25 17:29:42.712632', 'choice', '"[]"', 0),
  (68, 49, '操作系统', '同步与互斥', 'medium', '选择题', '【操作系统 · 同步与互斥】关于「同步与互斥」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5\\", \\"C. \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '同步与互斥 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', 'agent_fallback', '2026-06-25 17:31:23.679743', 'choice', '"[]"', 0),
  (69, 50, '操作系统', '同步与互斥', 'medium', '选择题', '【操作系统 · 同步与互斥】关于「同步与互斥」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5\\", \\"C. \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '同步与互斥 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', 'agent_fallback', '2026-06-25 17:31:58.900042', 'choice', '"[]"', 0),
  (70, 51, '操作系统', '同步与互斥', 'medium', '选择题', '【操作系统 · 同步与互斥】关于「同步与互斥」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5\\", \\"C. \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '同步与互斥 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', 'agent_fallback', '2026-06-25 17:33:23.998868', 'choice', '"[]"', 0),
  (71, 52, '操作系统', '同步与互斥', 'medium', '选择题', '【操作系统 · 同步与互斥】关于「同步与互斥」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5\\", \\"C. \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '同步与互斥 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u540c\\u6b65\\u4e0e\\u4e92\\u65a5 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', 'agent_fallback', '2026-06-25 17:35:35.535510', 'choice', '"[]"', 0),
  (72, 53, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】在数据链路层中，用于检测和纠正传输错误的常见技术是____。', '"[]"', '差错控制', '差错控制是数据链路层的重要功能之一，用于检测和纠正数据传输过程中可能出现的错误。', '"[\\"\\u8be5\\u6280\\u672f\\u901a\\u5e38\\u5305\\u62ec\\u5dee\\u9519\\u68c0\\u6d4b\\u548c\\u5dee\\u9519\\u7ea0\\u6b63\\u4e24\\u90e8\\u5206\\", \\"\\u5e38\\u89c1\\u7684\\u5b9e\\u73b0\\u65b9\\u6cd5\\u6709\\u5947\\u5076\\u6821\\u9a8c\\u3001CRC\\u7b49\\"]"', '薄弱点强化：围绕 计算机网络 / 数据链路层 生成 3 道 简单 填空题。', 'llm', '2026-06-25 17:38:48.719479', 'fill', '"[]"', 0),
  (73, 53, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】以太网帧的最小长度是____字节。', '"[]"', '64', '以太网帧的最小长度是64字节，这是为了保证冲突检测机制能够正常工作。', '"[\\"\\u8fd9\\u4e2a\\u957f\\u5ea6\\u5305\\u62ec\\u5e27\\u5934\\u548c\\u5e27\\u5c3e\\", \\"\\u5982\\u679c\\u6570\\u636e\\u90e8\\u5206\\u4e0d\\u8db346\\u5b57\\u8282\\u9700\\u8981\\u586b\\u5145\\"]"', '薄弱点强化：围绕 计算机网络 / 数据链路层 生成 3 道 简单 填空题。', 'llm', '2026-06-25 17:38:48.721479', 'fill', '"[]"', 0),
  (74, 53, '计算机网络', '数据链路层', '简单', '填空题', '【计算机网络 · 数据链路层】数据链路层的两个主要子层是____和____。', '"[]"', '逻辑链路控制子层(LLC), 媒体访问控制子层(MAC)', '数据链路层被划分为逻辑链路控制子层(LLC)和媒体访问控制子层(MAC)，分别负责不同的功能。', '"[\\"LLC\\u8d1f\\u8d23\\u4e0e\\u7f51\\u7edc\\u5c42\\u7684\\u63a5\\u53e3\\", \\"MAC\\u8d1f\\u8d23\\u63a7\\u5236\\u5bf9\\u7269\\u7406\\u4ecb\\u8d28\\u7684\\u8bbf\\u95ee\\"]"', '薄弱点强化：围绕 计算机网络 / 数据链路层 生成 3 道 简单 填空题。', 'llm', '2026-06-25 17:38:48.722158', 'fill', '"[]"', 0),
  (75, 54, '数据结构', '绪论', '中等', '选择题', '【数据结构 · 绪论】下列关于数据结构的叙述中，正确的是：', '"[\\"A. \\u6570\\u636e\\u7ed3\\u6784\\u662f\\u6307\\u76f8\\u4e92\\u4e4b\\u95f4\\u5b58\\u5728\\u4e00\\u79cd\\u6216\\u591a\\u79cd\\u7279\\u5b9a\\u5173\\u7cfb\\u7684\\u6570\\u636e\\u5143\\u7d20\\u7684\\u96c6\\u5408\\", \\"B. \\u6570\\u636e\\u7ed3\\u6784\\u662f\\u6307\\u6570\\u636e\\u5728\\u8ba1\\u7b97\\u673a\\u4e2d\\u7684\\u5b58\\u50a8\\u65b9\\u5f0f\\", \\"C. \\u6570\\u636e\\u7ed3\\u6784\\u662f\\u6307\\u6570\\u636e\\u7684\\u903b\\u8f91\\u7ed3\\u6784\\uff0c\\u4e0e\\u5b58\\u50a8\\u7ed3\\u6784\\u65e0\\u5173\\", \\"D. \\u6570\\u636e\\u7ed3\\u6784\\u662f\\u6307\\u6570\\u636e\\u7684\\u7269\\u7406\\u7ed3\\u6784\\uff0c\\u4e0e\\u903b\\u8f91\\u7ed3\\u6784\\u65e0\\u5173\\"]"', 'A', '数据结构不仅包括数据的逻辑结构，还包括数据的存储结构和数据的运算。选项A正确描述了数据结构的定义。选项B和D只强调了存储或物理结构，忽略了逻辑结构；选项C只强调了逻辑结构，忽略了存储结构。', '"[\\"\\u6570\\u636e\\u7ed3\\u6784\\u5305\\u62ec\\u903b\\u8f91\\u7ed3\\u6784\\u548c\\u5b58\\u50a8\\u7ed3\\u6784\\", \\"\\u6570\\u636e\\u7ed3\\u6784\\u5173\\u6ce8\\u6570\\u636e\\u5143\\u7d20\\u4e4b\\u95f4\\u7684\\u5173\\u7cfb\\"]"', '自由选择：围绕 数据结构 / 绪论 生成 1 道 中等 选择题。', 'llm', '2026-06-25 17:55:05.723188', 'choice', '"[]"', 0),
  (76, 55, '数据结构', '图', '真题难度', '选择题', '【数据结构 · 图】下列关于图的说法中，正确的是：', '"[\\"A. \\u5728\\u4e00\\u4e2a\\u6709\\u5411\\u56fe\\u4e2d\\uff0c\\u6240\\u6709\\u9876\\u70b9\\u7684\\u5165\\u5ea6\\u4e4b\\u548c\\u7b49\\u4e8e\\u6240\\u6709\\u9876\\u70b9\\u7684\\u51fa\\u5ea6\\u4e4b\\u548c\\", \\"B. \\u65e0\\u5411\\u56fe\\u7684\\u90bb\\u63a5\\u77e9\\u9635\\u4e00\\u5b9a\\u662f\\u5bf9\\u79f0\\u77e9\\u9635\\uff0c\\u800c\\u6709\\u5411\\u56fe\\u7684\\u90bb\\u63a5\\u77e9\\u9635\\u4e00\\u5b9a\\u4e0d\\u662f\\u5bf9\\u79f0\\u77e9\\u9635\\", \\"C. \\u56fe\\u7684\\u6df1\\u5ea6\\u4f18\\u5148\\u904d\\u5386\\u7b97\\u6cd5\\u4e0d\\u9002\\u7528\\u4e8e\\u6709\\u5411\\u56fe\\", \\"D. \\u62d3\\u6251\\u6392\\u5e8f\\u7b97\\u6cd5\\u53ef\\u4ee5\\u7528\\u4e8e\\u68c0\\u6d4b\\u6709\\u5411\\u56fe\\u4e2d\\u662f\\u5426\\u5b58\\u5728\\u73af\\"]"', 'A', 'A正确，因为每条有向边都会贡献一个出度和一个入度；B错误，有向图的邻接矩阵也可能是对称矩阵（如双向边）；C错误，深度优先遍历适用于所有图；D错误，拓扑排序只能用于无环有向图，不能检测环。', '"[\\"\\u8003\\u8651\\u6709\\u5411\\u56fe\\u4e2d\\u8fb9\\u7684\\u65b9\\u5411\\u4e0e\\u5ea6\\u6570\\u7684\\u5173\\u7cfb\\", \\"\\u601d\\u8003\\u90bb\\u63a5\\u77e9\\u9635\\u5bf9\\u79f0\\u6027\\u7684\\u5b9a\\u4e49\\"]"', '自由选择：围绕 数据结构 / 图 生成 1 道 真题难度 选择题。', 'llm', '2026-06-25 17:55:36.465962', 'choice', '"[]"', 0),
  (77, 56, '计算机组成原理', '输入输出系统', '简单', '综合题', '【计算机组成原理 · 输入输出系统】综合题', '"[]"', '', '综合题考查 输入输出系统 的多角度理解。', '"[\\"\\u5148\\u56de\\u7b54\\u6982\\u5ff5\\u90e8\\u5206\\u3002\\", \\"\\u518d\\u5206\\u6790\\u5177\\u4f53\\u5e94\\u7528\\u3002\\"]"', '薄弱点强化：计算机组成原理 / 输入输出系统 fallback 生成 2 道。', 'agent_fallback', '2026-06-25 18:01:50.024158', 'comprehensive', '"[{\\"title\\": \\"\\u7b80\\u8ff0 \\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u7684\\u57fa\\u672c\\u6982\\u5ff5\\u3002\\", \\"standard_answer\\": \\"\\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u662f \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u4e2d\\u7684\\u91cd\\u8981\\u77e5\\u8bc6\\u70b9\\u3002\\"}, {\\"title\\": \\"\\u5728\\u5b9e\\u9645\\u9898\\u76ee\\u4e2d\\uff0c\\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u7684\\u5e38\\u89c1\\u8003\\u6cd5\\u6709\\u54ea\\u4e9b\\uff1f\\", \\"options\\": [\\"A. \\u6982\\u5ff5\\u8fa8\\u6790\\", \\"B. \\u8fc7\\u7a0b\\u8ba1\\u7b97\\", \\"C. \\u8fb9\\u754c\\u6761\\u4ef6\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u662f\\"], \\"standard_answer\\": \\"D\\"}]"', 0),
  (78, 56, '计算机组成原理', '输入输出系统', '简单', '综合题', '【计算机组成原理 · 输入输出系统】综合题', '"[]"', '', '综合题考查 输入输出系统 的多角度理解。', '"[\\"\\u5148\\u56de\\u7b54\\u6982\\u5ff5\\u90e8\\u5206\\u3002\\", \\"\\u518d\\u5206\\u6790\\u5177\\u4f53\\u5e94\\u7528\\u3002\\"]"', '薄弱点强化：计算机组成原理 / 输入输出系统 fallback 生成 2 道。', 'agent_fallback', '2026-06-25 18:01:50.026245', 'comprehensive', '"[{\\"title\\": \\"\\u7b80\\u8ff0 \\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u7684\\u57fa\\u672c\\u6982\\u5ff5\\u3002\\", \\"standard_answer\\": \\"\\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u662f \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u4e2d\\u7684\\u91cd\\u8981\\u77e5\\u8bc6\\u70b9\\u3002\\"}, {\\"title\\": \\"\\u5728\\u5b9e\\u9645\\u9898\\u76ee\\u4e2d\\uff0c\\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf \\u7684\\u5e38\\u89c1\\u8003\\u6cd5\\u6709\\u54ea\\u4e9b\\uff1f\\", \\"options\\": [\\"A. \\u6982\\u5ff5\\u8fa8\\u6790\\", \\"B. \\u8fc7\\u7a0b\\u8ba1\\u7b97\\", \\"C. \\u8fb9\\u754c\\u6761\\u4ef6\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u662f\\"], \\"standard_answer\\": \\"D\\"}]"', 0),
  (79, 57, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在虚拟内存管理中，下列关于页面置换算法的叙述中，错误的是', '"[\\"A. \\u6700\\u4f73\\u7f6e\\u6362\\u7b97\\u6cd5\\uff08OPT\\uff09\\u5728\\u5b9e\\u9645\\u7cfb\\u7edf\\u4e2d\\u53ef\\u4ee5\\u5b9e\\u73b0\\", \\"B. \\u6700\\u8fd1\\u6700\\u5c11\\u4f7f\\u7528\\u7b97\\u6cd5\\uff08LRU\\uff09\\u9700\\u8981\\u786c\\u4ef6\\u652f\\u6301\\", \\"C. \\u5148\\u8fdb\\u5148\\u51fa\\u7b97\\u6cd5\\uff08FIFO\\uff09\\u53ef\\u80fd\\u4ea7\\u751fBelady\\u5f02\\u5e38\\", \\"D. \\u65f6\\u949f\\u7f6e\\u6362\\u7b97\\u6cd5\\uff08Clock\\uff09\\u662fLRU\\u7b97\\u6cd5\\u7684\\u8fd1\\u4f3c\\u5b9e\\u73b0\\"]"', 'A', '最佳置换算法（OPT）是一种理论算法，需要预知未来的页面访问序列，在实际系统中无法实现。其他选项描述均正确：LRU需要硬件支持记录访问时间；FIFO确实可能产生Belady异常；Clock算法是LRU的近似实现。', '"[\\"\\u601d\\u8003\\u54ea\\u4e9b\\u7b97\\u6cd5\\u5728\\u5b9e\\u9645\\u7cfb\\u7edf\\u4e2d\\u53ef\\u4ee5\\u5b9e\\u73b0\\", \\"\\u56de\\u987e\\u5404\\u79cd\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u7684\\u7279\\u70b9\\u548c\\u5b9e\\u73b0\\u96be\\u5ea6\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 1 道 真题难度 选择题。', 'llm', '2026-06-25 18:02:05.486139', 'choice', '"[]"', 0),
  (80, 58, '计算机网络', '计算机网络体系结构', '真题难度', '选择题', '【计算机网络 · 计算机网络体系结构】关于「计算机网络体系结构」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u8ba1\\u7b97\\u673a\\u7f51\\u7edc\\u4f53\\u7cfb\\u7ed3\\u6784 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u8ba1\\u7b97\\u673a\\u7f51\\u7edc\\u4f53\\u7cfb\\u7ed3\\u6784\\", \\"C. \\u8ba1\\u7b97\\u673a\\u7f51\\u7edc\\u4f53\\u7cfb\\u7ed3\\u6784 \\u4e0d\\u5c5e\\u4e8e \\u8ba1\\u7b97\\u673a\\u7f51\\u7edc \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '计算机网络体系结构 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u8ba1\\u7b97\\u673a\\u7f51\\u7edc\\u4f53\\u7cfb\\u7ed3\\u6784 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 计算机网络 / 计算机网络体系结构 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:07:22.428678', 'choice', '"[]"', 0),
  (81, 59, '操作系统', '文件管理', '中等', '综合题', '【操作系统 · 文件管理】综合题', '"[]"', '', '综合题考查 文件管理 的多角度理解。', '"[\\"\\u5148\\u56de\\u7b54\\u6982\\u5ff5\\u90e8\\u5206\\u3002\\", \\"\\u518d\\u5206\\u6790\\u5177\\u4f53\\u5e94\\u7528\\u3002\\"]"', '自由选择：操作系统 / 文件管理 fallback 生成 1 道。', 'agent_fallback', '2026-06-25 18:11:18.077598', 'comprehensive', '"[{\\"title\\": \\"\\u7b80\\u8ff0 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u57fa\\u672c\\u6982\\u5ff5\\u3002\\", \\"standard_answer\\": \\"\\u6587\\u4ef6\\u7ba1\\u7406 \\u662f \\u64cd\\u4f5c\\u7cfb\\u7edf \\u4e2d\\u7684\\u91cd\\u8981\\u77e5\\u8bc6\\u70b9\\u3002\\"}, {\\"title\\": \\"\\u5728\\u5b9e\\u9645\\u9898\\u76ee\\u4e2d\\uff0c\\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u5e38\\u89c1\\u8003\\u6cd5\\u6709\\u54ea\\u4e9b\\uff1f\\", \\"options\\": [\\"A. \\u6982\\u5ff5\\u8fa8\\u6790\\", \\"B. \\u8fc7\\u7a0b\\u8ba1\\u7b97\\", \\"C. \\u8fb9\\u754c\\u6761\\u4ef6\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u662f\\"], \\"standard_answer\\": \\"D\\"}]"', 0),
  (82, 60, '操作系统', '文件管理', '中等', '综合题', '【操作系统 · 文件管理】综合题', '"[]"', '', '综合题考查 文件管理 的多角度理解。', '"[\\"\\u5148\\u56de\\u7b54\\u6982\\u5ff5\\u90e8\\u5206\\u3002\\", \\"\\u518d\\u5206\\u6790\\u5177\\u4f53\\u5e94\\u7528\\u3002\\"]"', '自由选择：操作系统 / 文件管理 fallback 生成 1 道。', 'agent_fallback', '2026-06-25 18:11:31.655173', 'comprehensive', '"[{\\"title\\": \\"\\u7b80\\u8ff0 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u57fa\\u672c\\u6982\\u5ff5\\u3002\\", \\"standard_answer\\": \\"\\u6587\\u4ef6\\u7ba1\\u7406 \\u662f \\u64cd\\u4f5c\\u7cfb\\u7edf \\u4e2d\\u7684\\u91cd\\u8981\\u77e5\\u8bc6\\u70b9\\u3002\\"}, {\\"title\\": \\"\\u5728\\u5b9e\\u9645\\u9898\\u76ee\\u4e2d\\uff0c\\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u5e38\\u89c1\\u8003\\u6cd5\\u6709\\u54ea\\u4e9b\\uff1f\\", \\"options\\": [\\"A. \\u6982\\u5ff5\\u8fa8\\u6790\\", \\"B. \\u8fc7\\u7a0b\\u8ba1\\u7b97\\", \\"C. \\u8fb9\\u754c\\u6761\\u4ef6\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u662f\\"], \\"standard_answer\\": \\"D\\"}]"', 0),
  (83, 61, '操作系统', '文件管理', '中等', '选择题', '【操作系统 · 文件管理】关于「文件管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u6587\\u4ef6\\u7ba1\\u7406\\", \\"C. \\u6587\\u4ef6\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '文件管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 文件管理 生成 1 道 中等 选择题。', 'agent_fallback', '2026-06-25 18:18:01.175346', 'choice', '"[]"', 0),
  (84, 62, '操作系统', '文件管理', '真题难度', '选择题', '【操作系统 · 文件管理】关于「文件管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u6587\\u4ef6\\u7ba1\\u7406\\", \\"C. \\u6587\\u4ef6\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '文件管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 文件管理 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:18:20.847458', 'choice', '"[]"', 0),
  (85, 63, '操作系统', '文件管理', '真题难度', '选择题', '【操作系统 · 文件管理】关于「文件管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u6587\\u4ef6\\u7ba1\\u7406\\", \\"C. \\u6587\\u4ef6\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '文件管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u6587\\u4ef6\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 文件管理 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:18:23.295705', 'choice', '"[]"', 0),
  (86, 64, '计算机组成原理', '存储系统', '真题难度', '选择题', '【计算机组成原理 · 存储系统】关于「存储系统」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u5b58\\u50a8\\u7cfb\\u7edf \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u5b58\\u50a8\\u7cfb\\u7edf\\", \\"C. \\u5b58\\u50a8\\u7cfb\\u7edf \\u4e0d\\u5c5e\\u4e8e \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '存储系统 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u5b58\\u50a8\\u7cfb\\u7edf \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 计算机组成原理 / 存储系统 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:18:50.953882', 'choice', '"[]"', 0),
  (87, 65, '计算机组成原理', '存储系统', '真题难度', '选择题', '【计算机组成原理 · 存储系统】关于「存储系统」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u5b58\\u50a8\\u7cfb\\u7edf \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u5b58\\u50a8\\u7cfb\\u7edf\\", \\"C. \\u5b58\\u50a8\\u7cfb\\u7edf \\u4e0d\\u5c5e\\u4e8e \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '存储系统 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u5b58\\u50a8\\u7cfb\\u7edf \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 计算机组成原理 / 存储系统 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:18:51.166578', 'choice', '"[]"', 0),
  (88, 66, '数据结构', '查找', '中等', '选择题', '【数据结构 · 查找】在二叉排序树中查找一个关键字时，其平均时间复杂度为：', '"[\\"A. O(log n)\\", \\"B. O(n)\\", \\"C. O(n log n)\\", \\"D. O(1)\\"]"', 'A', '在平衡的二叉排序树中，查找操作的时间复杂度为O(log n)，但在最坏情况下（树退化为链表）为O(n)。题目问的是平均时间复杂度，因此选A。', '"[\\"\\u4e8c\\u53c9\\u6392\\u5e8f\\u6811\\u7684\\u67e5\\u627e\\u6548\\u7387\\u4e0e\\u6811\\u7684\\u9ad8\\u5ea6\\u6709\\u5173\\", \\"\\u8003\\u8651\\u5e73\\u8861\\u4e8c\\u53c9\\u6392\\u5e8f\\u6811\\u7684\\u60c5\\u51b5\\"]"', '薄弱点强化：围绕 数据结构 / 查找 生成 3 道 中等 选择题。', 'llm', '2026-06-25 18:19:48.085140', 'choice', '"[]"', 0),
  (89, 66, '数据结构', '查找', '中等', '选择题', '【数据结构 · 查找】下列关于哈希表查找的说法中，错误的是：', '"[\\"A. \\u54c8\\u5e0c\\u8868\\u7684\\u67e5\\u627e\\u6548\\u7387\\u901a\\u5e38\\u9ad8\\u4e8e\\u4e8c\\u5206\\u67e5\\u627e\\", \\"B. \\u54c8\\u5e0c\\u8868\\u7684\\u67e5\\u627e\\u65f6\\u95f4\\u590d\\u6742\\u5ea6\\u53ef\\u4ee5\\u8fbe\\u5230O(1)\\", \\"C. \\u54c8\\u5e0c\\u8868\\u67e5\\u627e\\u4e0d\\u9700\\u8981\\u6bd4\\u8f83\\u5173\\u952e\\u5b57\\", \\"D. \\u54c8\\u5e0c\\u8868\\u67e5\\u627e\\u6548\\u7387\\u4e0e\\u88c5\\u586b\\u56e0\\u5b50\\u65e0\\u5173\\"]"', 'D', '哈希表的查找效率与装填因子密切相关，装填因子越大，发生冲突的可能性越大，查找效率越低。因此D选项是错误的。', '"[\\"\\u88c5\\u586b\\u56e0\\u5b50\\u662f\\u54c8\\u5e0c\\u8868\\u4e2d\\u5df2\\u586b\\u5165\\u7684\\u8bb0\\u5f55\\u6570\\u4e0e\\u54c8\\u5e0c\\u8868\\u957f\\u5ea6\\u7684\\u6bd4\\u503c\\", \\"\\u8003\\u8651\\u54c8\\u5e0c\\u51b2\\u7a81\\u5bf9\\u67e5\\u627e\\u6548\\u7387\\u7684\\u5f71\\u54cd\\"]"', '薄弱点强化：围绕 数据结构 / 查找 生成 3 道 中等 选择题。', 'llm', '2026-06-25 18:19:48.086163', 'choice', '"[]"', 0),
  (90, 66, '数据结构', '查找', '中等', '选择题', '【数据结构 · 查找】在长度为n的有序顺序表中进行折半查找，查找失败时需要进行的关键字比较次数最多为：', '"[\\"A. \\u2308log\\u2082(n+1)\\u2309\\", \\"B. \\u230alog\\u2082n\\u230b+1\\", \\"C. \\u2308log\\u2082n\\u2309\\", \\"D. \\u230alog\\u2082(n+1)\\u230b\\"]"', 'B', '折半查找的查找长度不超过判定树的高度，而n个结点的判定树高度为⌊log₂n⌋+1。因此查找失败时最多需要⌊log₂n⌋+1次比较。', '"[\\"\\u6298\\u534a\\u67e5\\u627e\\u7684\\u67e5\\u627e\\u8fc7\\u7a0b\\u53ef\\u4ee5\\u7528\\u5224\\u5b9a\\u6811\\u6765\\u63cf\\u8ff0\\", \\"\\u8003\\u8651\\u5224\\u5b9a\\u6811\\u7684\\u9ad8\\u5ea6\\u4e0e\\u6bd4\\u8f83\\u6b21\\u6570\\u7684\\u5173\\u7cfb\\"]"', '薄弱点强化：围绕 数据结构 / 查找 生成 3 道 中等 选择题。', 'llm', '2026-06-25 18:19:48.086735', 'choice', '"[]"', 0),
  (91, 67, '计算机组成原理', '指令系统', '真题难度', '选择题', '【计算机组成原理 · 指令系统】在指令系统中，下列哪种寻址方式不需要访问内存即可获得操作数？', '"[\\"A. \\u7acb\\u5373\\u5bfb\\u5740\\", \\"B. \\u76f4\\u63a5\\u5bfb\\u5740\\", \\"C. \\u95f4\\u63a5\\u5bfb\\u5740\\", \\"D. \\u5bc4\\u5b58\\u5668\\u95f4\\u63a5\\u5bfb\\u5740\\"]"', 'A', '立即寻址方式的操作数直接包含在指令中，不需要访问内存即可获得操作数。其他寻址方式都需要访问内存或寄存器来获取操作数。', '"[\\"\\u7acb\\u5373\\u5bfb\\u5740\\u7684\\u64cd\\u4f5c\\u6570\\u5728\\u6307\\u4ee4\\u4e2d\\", \\"\\u5176\\u4ed6\\u5bfb\\u5740\\u65b9\\u5f0f\\u9700\\u8981\\u8bbf\\u95ee\\u5185\\u5b58\\u6216\\u5bc4\\u5b58\\u5668\\"]"', '自由选择：围绕 计算机组成原理 / 指令系统 生成 1 道 真题难度 选择题。', 'llm', '2026-06-25 18:26:15.688185', 'choice', '"[]"', 0),
  (92, 68, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】关于「内存管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u5185\\u5b58\\u7ba1\\u7406\\", \\"C. \\u5185\\u5b58\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '内存管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:31:49.013619', 'choice', '"[]"', 0),
  (93, 68, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】关于「内存管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u5185\\u5b58\\u7ba1\\u7406\\", \\"C. \\u5185\\u5b58\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '内存管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:31:49.016974', 'choice', '"[]"', 0),
  (94, 68, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】关于「内存管理」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u5185\\u5b58\\u7ba1\\u7406\\", \\"C. \\u5185\\u5b58\\u7ba1\\u7406 \\u4e0d\\u5c5e\\u4e8e \\u64cd\\u4f5c\\u7cfb\\u7edf \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '内存管理 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u5185\\u5b58\\u7ba1\\u7406 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'agent_fallback', '2026-06-25 18:31:49.018078', 'choice', '"[]"', 0),
  (95, 69, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在虚拟内存管理中，下列哪种页面置换算法可能导致Belady异常？', '"[\\"A. \\u5148\\u8fdb\\u5148\\u51fa\\uff08FIFO\\uff09\\", \\"B. \\u6700\\u8fd1\\u6700\\u5c11\\u4f7f\\u7528\\uff08LRU\\uff09\\", \\"C. \\u65f6\\u949f\\uff08Clock\\uff09\\", \\"D. \\u6700\\u4f18\\uff08OPT\\uff09\\"]"', 'A', 'Belady异常是指在使用FIFO页面置换算法时，增加物理内存页框数反而导致缺页率上升的现象。其他算法如LRU、Clock和OPT不会出现这种情况。', '"[\\"Belady\\u5f02\\u5e38\\u4e0e\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u6709\\u5173\\", \\"FIFO\\u7b97\\u6cd5\\u5728\\u67d0\\u4e9b\\u60c5\\u51b5\\u4e0b\\u4f1a\\u51fa\\u73b0\\u5f02\\u5e38\\u73b0\\u8c61\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-25 18:32:06.008254', 'choice', '"[]"', 0),
  (96, 69, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在分页存储管理中，页表的主要功能是：', '"[\\"A. \\u5b9e\\u73b0\\u903b\\u8f91\\u5730\\u5740\\u5230\\u7269\\u7406\\u5730\\u5740\\u7684\\u8f6c\\u6362\\", \\"B. \\u8bb0\\u5f55\\u5185\\u5b58\\u4e2d\\u5404\\u9875\\u9762\\u7684\\u4f7f\\u7528\\u60c5\\u51b5\\", \\"C. \\u7ba1\\u7406\\u5916\\u5b58\\u4ea4\\u6362\\u533a\\u7684\\u5206\\u914d\\", \\"D. \\u5b9e\\u73b0\\u8fdb\\u7a0b\\u95f4\\u7684\\u901a\\u4fe1\\"]"', 'A', '页表的核心功能是将逻辑地址转换为物理地址，通过页表可以找到逻辑页面对应的物理页框。', '"[\\"\\u9875\\u8868\\u4e0e\\u5730\\u5740\\u8f6c\\u6362\\u76f8\\u5173\\", \\"\\u5206\\u9875\\u7cfb\\u7edf\\u4e2d\\u9700\\u8981\\u67d0\\u79cd\\u7ed3\\u6784\\u8bb0\\u5f55\\u6620\\u5c04\\u5173\\u7cfb\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-25 18:32:06.009348', 'choice', '"[]"', 0),
  (97, 69, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】下列关于动态分区分配的叙述中，正确的是：', '"[\\"A. \\u9996\\u6b21\\u9002\\u5e94\\u7b97\\u6cd5\\u53ef\\u80fd\\u4ea7\\u751f\\u8f83\\u591a\\u5916\\u90e8\\u788e\\u7247\\", \\"B. \\u6700\\u4f73\\u9002\\u5e94\\u7b97\\u6cd5\\u603b\\u662f\\u4fdd\\u7559\\u6700\\u5927\\u7684\\u7a7a\\u95f2\\u5206\\u533a\\", \\"C. \\u6700\\u574f\\u9002\\u5e94\\u7b97\\u6cd5\\u80fd\\u6700\\u5c0f\\u5316\\u5916\\u90e8\\u788e\\u7247\\", \\"D. \\u90bb\\u8fd1\\u9002\\u5e94\\u7b97\\u6cd5\\u7684\\u6027\\u80fd\\u4f18\\u4e8e\\u9996\\u6b21\\u9002\\u5e94\\u7b97\\u6cd5\\"]"', 'A', '首次适应算法从低地址开始查找，可能导致低地址区域产生较多小碎片。最佳适应算法会保留大分区，最坏适应算法可能增加外部碎片，邻近适应算法性能不一定优于首次适应。', '"[\\"\\u52a8\\u6001\\u5206\\u533a\\u5206\\u914d\\u4f1a\\u4ea7\\u751f\\u5916\\u90e8\\u788e\\u7247\\", \\"\\u4e0d\\u540c\\u5206\\u914d\\u7b56\\u7565\\u5bf9\\u788e\\u7247\\u7684\\u5f71\\u54cd\\u4e0d\\u540c\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-25 18:32:06.010634', 'choice', '"[]"', 0),
  (98, 70, '计算机组成原理', '中央处理器', '真题难度', '选择题', '【计算机组成原理 · 中央处理器】关于「中央处理器」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u4e2d\\u592e\\u5904\\u7406\\u5668 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u4e2d\\u592e\\u5904\\u7406\\u5668\\", \\"C. \\u4e2d\\u592e\\u5904\\u7406\\u5668 \\u4e0d\\u5c5e\\u4e8e \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '中央处理器 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u4e2d\\u592e\\u5904\\u7406\\u5668 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 计算机组成原理 / 中央处理器 生成 1 道 真题难度 选择题。', 'agent_fallback', '2026-06-26 00:19:10.901137', 'choice', '"[]"', 0),
  (99, 71, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在虚拟内存管理中，下列哪种页面置换算法可能导致Belady异常？', '"[\\"A. \\u5148\\u8fdb\\u5148\\u51fa(FIFO)\\", \\"B. \\u6700\\u8fd1\\u6700\\u5c11\\u4f7f\\u7528(LRU)\\", \\"C. \\u65f6\\u949f(CLOCK)\\", \\"D. \\u6700\\u4e0d\\u7ecf\\u5e38\\u4f7f\\u7528(LFU)\\"]"', 'A', 'Belady异常是指分配的物理页框增加时，缺页次数反而增加的现象。只有FIFO算法可能出现这种情况。', '"[\\"Belady\\u5f02\\u5e38\\u662fFIFO\\u7279\\u6709\\u7684\\u73b0\\u8c61\\", \\"\\u5176\\u4ed6\\u7b97\\u6cd5\\u90fd\\u662f\\u57fa\\u4e8e\\u6808\\u7684\\u7f6e\\u6362\\u7b97\\u6cd5\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:43.077500', 'choice', '"[]"', 0),
  (100, 71, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】某系统采用分页存储管理，逻辑地址结构为(页号,页内偏移)，若页大小为4KB，逻辑地址长度为32位，页表项大小为4B，则采用单级页表时页表最大占用多少内存？', '"[\\"A. 4MB\\", \\"B. 8MB\\", \\"C. 16MB\\", \\"D. 32MB\\"]"', 'A', '页大小4KB=2^12B，所以页内偏移占12位，页号占20位。页表项数=2^20=1M个，每个页表项4B，所以页表大小=1M×4B=4MB。', '"[\\"\\u5148\\u8ba1\\u7b97\\u9875\\u53f7\\u4f4d\\u6570\\", \\"\\u9875\\u8868\\u5927\\u5c0f=\\u9875\\u8868\\u9879\\u6570\\u00d7\\u6bcf\\u4e2a\\u9875\\u8868\\u9879\\u5927\\u5c0f\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:43.077500', 'choice', '"[]"', 0),
  (101, 71, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】下列关于虚拟存储器的叙述中，正确的是：', '"[\\"A. \\u865a\\u62df\\u5b58\\u50a8\\u5668\\u7684\\u5927\\u5c0f\\u53d7\\u9650\\u4e8e\\u5916\\u5b58\\u5bb9\\u91cf\\", \\"B. \\u865a\\u62df\\u5b58\\u50a8\\u5668\\u7684\\u5927\\u5c0f\\u53d7\\u9650\\u4e8e\\u8ba1\\u7b97\\u673a\\u7684\\u5730\\u5740\\u7ed3\\u6784\\", \\"C. \\u865a\\u62df\\u5b58\\u50a8\\u5668\\u7684\\u5927\\u5c0f\\u53d7\\u9650\\u4e8e\\u5185\\u5b58\\u5bb9\\u91cf\\", \\"D. \\u865a\\u62df\\u5b58\\u50a8\\u5668\\u7684\\u5927\\u5c0f\\u53d7\\u9650\\u4e8eCPU\\u901f\\u5ea6\\"]"', 'B', '虚拟存储器的最大容量由计算机的地址结构决定，例如32位系统的虚拟地址空间最大为4GB。', '"[\\"\\u865a\\u62df\\u5b58\\u50a8\\u5668\\u5927\\u5c0f\\u4e0e\\u5730\\u5740\\u4f4d\\u6570\\u76f8\\u5173\\", \\"\\u5b9e\\u9645\\u4f7f\\u7528\\u7684\\u865a\\u62df\\u5b58\\u50a8\\u5668\\u5927\\u5c0f\\u53ef\\u80fd\\u53d7\\u5176\\u4ed6\\u56e0\\u7d20\\u9650\\u5236\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:43.078509', 'choice', '"[]"', 0),
  (102, 72, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在虚拟内存管理中，下列哪种页面置换算法可能导致Belady异常？', '"[\\"A. \\u5148\\u8fdb\\u5148\\u51fa\\uff08FIFO\\uff09\\", \\"B. \\u6700\\u8fd1\\u6700\\u5c11\\u4f7f\\u7528\\uff08LRU\\uff09\\", \\"C. \\u65f6\\u949f\\uff08Clock\\uff09\\", \\"D. \\u6700\\u4f18\\uff08OPT\\uff09\\"]"', 'A', 'Belady异常是指在某些页面置换算法中，增加物理页面数反而导致缺页率上升的现象。FIFO算法是唯一可能导致Belady异常的常见算法。', '"[\\"Belady\\u5f02\\u5e38\\u4e0e\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u6709\\u5173\\", \\"\\u8003\\u8651\\u7b97\\u6cd5\\u662f\\u5426\\u57fa\\u4e8e\\u8bbf\\u95ee\\u5386\\u53f2\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:55.354434', 'choice', '"[]"', 0),
  (103, 72, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】下列关于动态分区分配策略的描述中，错误的是：', '"[\\"A. \\u9996\\u6b21\\u9002\\u5e94\\u7b97\\u6cd5\\u4ece\\u5185\\u5b58\\u4f4e\\u5730\\u5740\\u5f00\\u59cb\\u67e5\\u627e\\u53ef\\u7528\\u5206\\u533a\\", \\"B. \\u6700\\u4f73\\u9002\\u5e94\\u7b97\\u6cd5\\u603b\\u662f\\u9009\\u62e9\\u80fd\\u6ee1\\u8db3\\u8981\\u6c42\\u7684\\u6700\\u5c0f\\u5206\\u533a\\", \\"C. \\u6700\\u574f\\u9002\\u5e94\\u7b97\\u6cd5\\u603b\\u662f\\u9009\\u62e9\\u6700\\u5927\\u7684\\u53ef\\u7528\\u5206\\u533a\\", \\"D. \\u5faa\\u73af\\u9996\\u6b21\\u9002\\u5e94\\u7b97\\u6cd5\\u6bd4\\u9996\\u6b21\\u9002\\u5e94\\u7b97\\u6cd5\\u5177\\u6709\\u66f4\\u9ad8\\u7684\\u5185\\u5b58\\u5229\\u7528\\u7387\\"]"', 'D', '循环首次适应算法与首次适应算法的内存利用率没有必然的高低关系，两者各有优缺点。其他选项对分配策略的描述都是正确的。', '"[\\"\\u6bd4\\u8f83\\u5404\\u79cd\\u52a8\\u6001\\u5206\\u533a\\u5206\\u914d\\u7b56\\u7565\\u7684\\u7279\\u70b9\\", \\"\\u6ce8\\u610f''\\u603b\\u662f''\\u7b49\\u7edd\\u5bf9\\u6027\\u8868\\u8ff0\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:55.354434', 'choice', '"[]"', 0),
  (104, 72, '操作系统', '内存管理', '真题难度', '选择题', '【操作系统 · 内存管理】在段页式存储管理中，地址转换需要访问几次内存？（假设快表TLB未命中）', '"[\\"A. 1\\u6b21\\", \\"B. 2\\u6b21\\", \\"C. 3\\u6b21\\", \\"D. 4\\u6b21\\"]"', 'C', '段页式存储管理中，地址转换需要：1)访问段表得到页表起始地址；2)访问页表得到物理页号；3)访问实际内存单元。因此共需3次内存访问。', '"[\\"\\u8003\\u8651\\u6bb5\\u8868\\u548c\\u9875\\u8868\\u7684\\u8bbf\\u95ee\\u987a\\u5e8f\\", \\"TLB\\u672a\\u547d\\u4e2d\\u65f6\\u9700\\u8981\\u8bbf\\u95ee\\u5185\\u5b58\\"]"', '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:19:55.355836', 'choice', '"[]"', 0),
  (105, 73, '数据结构', '图', '真题难度', '选择题', '【数据结构 · 图】下列关于图的存储结构的叙述中，错误的是', '"[\\"A. \\u90bb\\u63a5\\u77e9\\u9635\\u8868\\u793a\\u6cd5\\u9002\\u7528\\u4e8e\\u7a00\\u758f\\u56fe\\", \\"B. \\u90bb\\u63a5\\u8868\\u8868\\u793a\\u6cd5\\u9002\\u7528\\u4e8e\\u7a00\\u758f\\u56fe\\", \\"C. \\u5341\\u5b57\\u94fe\\u8868\\u662f\\u6709\\u5411\\u56fe\\u7684\\u53e6\\u4e00\\u79cd\\u94fe\\u5f0f\\u5b58\\u50a8\\u7ed3\\u6784\\", \\"D. \\u90bb\\u63a5\\u591a\\u91cd\\u8868\\u662f\\u65e0\\u5411\\u56fe\\u7684\\u53e6\\u4e00\\u79cd\\u94fe\\u5f0f\\u5b58\\u50a8\\u7ed3\\u6784\\"]"', 'A', '邻接矩阵表示法适用于稠密图，因为其空间复杂度为O(n^2)，而邻接表适用于稀疏图，空间复杂度为O(n+e)。', '"[\\"\\u8003\\u8651\\u4e0d\\u540c\\u5b58\\u50a8\\u7ed3\\u6784\\u7684\\u7a7a\\u95f4\\u590d\\u6742\\u5ea6\\", \\"\\u7a00\\u758f\\u56fe\\u548c\\u7a20\\u5bc6\\u56fe\\u7684\\u5b9a\\u4e49\\"]"', '自由选择：围绕 数据结构 / 图 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:20:44.080025', 'choice', '"[]"', 0),
  (106, 73, '数据结构', '图', '真题难度', '选择题', '【数据结构 · 图】在有向图的拓扑排序中，若存在一条从顶点A到顶点B的路径，则在拓扑序列中', '"[\\"A. A\\u4e00\\u5b9a\\u5728B\\u7684\\u524d\\u9762\\", \\"B. B\\u4e00\\u5b9a\\u5728A\\u7684\\u524d\\u9762\\", \\"C. A\\u548cB\\u7684\\u76f8\\u5bf9\\u4f4d\\u7f6e\\u4e0d\\u786e\\u5b9a\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u4e0d\\u5bf9\\"]"', 'A', '拓扑排序中，若存在A到B的路径，则A必须在B的前面，这是拓扑排序的基本性质。', '"[\\"\\u62d3\\u6251\\u6392\\u5e8f\\u7684\\u5b9a\\u4e49\\", \\"\\u8003\\u8651\\u6709\\u5411\\u65e0\\u73af\\u56fe\\u7684\\u7279\\u6027\\"]"', '自由选择：围绕 数据结构 / 图 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:20:44.081039', 'choice', '"[]"', 0);
INSERT INTO `question` (`id`, `session_id`, `subject`, `knowledge_point`, `difficulty`, `question_type`, `question_text`, `options_json`, `standard_answer`, `explanation`, `hints_json`, `recommend_reason`, `source`, `create_time`, `variant_type`, `sub_questions_json`, `is_deleted`) VALUES
  (107, 73, '数据结构', '图', '真题难度', '选择题', '【数据结构 · 图】用Dijkstra算法求单源最短路径时，要求图中所有边的权值必须', '"[\\"A. \\u5747\\u4e3a\\u975e\\u8d1f\\u6570\\", \\"B. \\u5747\\u4e0d\\u4e3a\\u8d1f\\u6570\\", \\"C. \\u5747\\u53ef\\u4e3a\\u4efb\\u610f\\u5b9e\\u6570\\", \\"D. \\u4ee5\\u4e0a\\u90fd\\u4e0d\\u5bf9\\"]"', 'A', 'Dijkstra算法要求图中所有边的权值必须为非负数，因为其基于贪心策略，负权边会导致算法失效。', '"[\\"Dijkstra\\u7b97\\u6cd5\\u7684\\u9002\\u7528\\u6761\\u4ef6\\", \\"\\u8003\\u8651\\u8d1f\\u6743\\u8fb9\\u7684\\u5f71\\u54cd\\"]"', '自由选择：围绕 数据结构 / 图 生成 3 道 真题难度 选择题。', 'llm', '2026-06-26 00:20:44.081039', 'choice', '"[]"', 0),
  (108, 74, '计算机组成原理', '计算机系统概述', '简单', '选择题', '【计算机组成原理 · 计算机系统概述】关于「计算机系统概述」的下列说法，哪一项最符合 408 考纲要求？', '"[\\"A. \\u53ea\\u9700\\u8bb0\\u5fc6 \\u8ba1\\u7b97\\u673a\\u7cfb\\u7edf\\u6982\\u8ff0 \\u7684\\u7ed3\\u8bba\\uff0c\\u4e0d\\u5fc5\\u7406\\u89e3\\u8fc7\\u7a0b\\", \\"B. \\u5e94\\u7ed3\\u5408\\u5b9a\\u4e49\\u3001\\u5173\\u952e\\u6b65\\u9aa4\\u548c\\u8fb9\\u754c\\u6761\\u4ef6\\u7406\\u89e3 \\u8ba1\\u7b97\\u673a\\u7cfb\\u7edf\\u6982\\u8ff0\\", \\"C. \\u8ba1\\u7b97\\u673a\\u7cfb\\u7edf\\u6982\\u8ff0 \\u4e0d\\u5c5e\\u4e8e \\u8ba1\\u7b97\\u673a\\u7ec4\\u6210\\u539f\\u7406 \\u7684\\u8003\\u8bd5\\u8303\\u56f4\\", \\"D. \\u6240\\u6709\\u9898\\u76ee\\u90fd\\u53ef\\u4ee5\\u5ffd\\u7565\\u521d\\u59cb\\u72b6\\u6001\\"]"', 'B', '计算机系统概述 的 408 题目通常同时考查概念、过程和边界条件，不能只背结论。', '"[\\"\\u5148\\u56de\\u5fc6 \\u8ba1\\u7b97\\u673a\\u7cfb\\u7edf\\u6982\\u8ff0 \\u7684\\u6838\\u5fc3\\u5b9a\\u4e49\\u3002\\", \\"\\u518d\\u68c0\\u67e5\\u9009\\u9879\\u662f\\u5426\\u5ffd\\u7565\\u8fc7\\u7a0b\\u6216\\u8fb9\\u754c\\u6761\\u4ef6\\u3002\\"]"', '自由选择：围绕 计算机组成原理 / 计算机系统概述 生成 1 道 简单 选择题。', 'agent_fallback', '2026-06-26 00:29:04.374065', 'choice', '"[]"', 0),
  (109, NULL, '操作系统', '进程与线程', '简单', '选择题', '同一时刻仅允许单个进程访问的硬件/资源称为？', '["A. \\u5171\\u4eab\\u8d44\\u6e90", "B. \\u4e34\\u754c\\u8d44\\u6e90", "C. \\u5168\\u5c40\\u5185\\u5b58", "D. \\u516c\\u5171\\u53d8\\u91cf"]', 'B', '访问临界资源的代码段称为临界区，必须满足互斥访问规则。', '"\\u6253\\u5370\\u673a\\u3001\\u78c1\\u5e26\\u673a\\u90fd\\u662f\\u5178\\u578b\\u4e34\\u754c\\u8d44\\u6e90"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (110, NULL, '操作系统', '进程与线程', '简单', '选择题', '用于实现互斥功能的记录型信号量初始值固定为？', '["A. 0", "B. 1", "C. \\u8d44\\u6e90\\u603b\\u6570", "D. -1"]', 'B', '互斥信号量初值1，同步信号量初值为缓冲区空位数量。', '"P\\u51cf\\u4e00\\u7533\\u8bf7\\u8d44\\u6e90\\uff0cV\\u52a0\\u4e00\\u91ca\\u653e\\u8d44\\u6e90"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (111, NULL, '操作系统', '进程与线程', '中等', '选择题', '临界区四条准则中，进程无法获取资源时主动放弃CPU是？', '["A. \\u7a7a\\u95f2\\u8ba9\\u8fdb", "B. \\u5fd9\\u5219\\u7b49\\u5f85", "C. \\u6709\\u9650\\u7b49\\u5f85", "D. \\u8ba9\\u6743\\u7b49\\u5f85"]', 'D', '让权等待避免进程忙等消耗CPU，信号量机制满足该准则。', '"\\u8f6f\\u4ef6Peterson\\u7b97\\u6cd5\\u5b58\\u5728\\u5fd9\\u7b49\\u7f3a\\u9677"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (112, NULL, '操作系统', '进程与线程', '中等', '填空题', '管程内部自动实现____，无需手动书写互斥PV操作。', '[]', '互斥', '同一时间仅一个进程进入管程内部过程，依靠条件变量完成同步。', '"\\u6761\\u4ef6\\u53d8\\u91cfwait\\u963b\\u585e\\uff0csignal\\u5524\\u9192"', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (113, NULL, '操作系统', '进程与线程', '困难', '简答题', '写出生产者消费者问题完整PV伪代码，并说明同步信号量必须放在互斥信号量外侧的原因。', '[]', '信号量定义：empty=n(空缓冲区)，full=0(产品)，mutex=1(互斥)；生产者：P(empty)→P(mutex)→写入缓冲区→V(mutex)→V(full)；消费者：P(full)→P(mutex)→取出数据→V(mutex)→V(原因：若同步P放在临界区内，缓冲区满时空缓冲区信号量为0，生产者持有mutex阻塞，消费者无法进入临界区释放empty，形成死锁。', '同步操作不能包裹在互斥临界区内部。', '"\\u591a\\u751f\\u4ea7\\u8005\\u591a\\u6d88\\u8d39\\u8005\\u5747\\u9002\\u7528\\u8be5\\u903b\\u8f91"', '', 'seed', '2026-06-26 02:44:21.016401', 'essay', '[]', 0),
  (114, NULL, '操作系统', '进程与线程', '简单', '选择题', '以下哪一项不属于死锁四大必要条件？', '["A. \\u4e92\\u65a5\\u8bbf\\u95ee", "B. \\u5360\\u6709\\u5e76\\u7b49\\u5f85", "C. \\u8d44\\u6e90\\u53ef\\u5265\\u593a", "D. \\u5faa\\u73af\\u7b49\\u5f85\\u94fe"]', 'C', '死锁要求资源不可剥夺，可剥夺资源直接打破第三条预防死锁。', '"\\u56db\\u5927\\u6761\\u4ef6\\u540c\\u65f6\\u6ee1\\u8db3\\u624d\\u4f1a\\u89e6\\u53d1\\u6b7b\\u9501"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (115, NULL, '操作系统', '进程与线程', '简单', '选择题', '银行家算法属于哪一类死锁处理策略？', '["A. \\u6b7b\\u9501\\u9884\\u9632", "B. \\u6b7b\\u9501\\u907f\\u514d", "C. \\u6b7b\\u9501\\u68c0\\u6d4b", "D. \\u6b7b\\u9501\\u89e3\\u9664"]', 'B', '银行家分配资源前计算安全序列，动态规避死锁发生。', '"\\u9884\\u9632\\u662f\\u9759\\u6001\\u7834\\u574f\\u56db\\u5927\\u6761\\u4ef6\\u4e4b\\u4e00"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (116, NULL, '操作系统', '进程与线程', '中等', '选择题', '破坏循环等待条件的典型手段是？', '["A. \\u8d44\\u6e90\\u7edf\\u4e00\\u7f16\\u53f7\\u6309\\u5e8f\\u7533\\u8bf7", "B. \\u5141\\u8bb8\\u62a2\\u5360\\u8d44\\u6e90", "C. \\u4e00\\u6b21\\u6027\\u7533\\u8bf7\\u5168\\u90e8\\u8d44\\u6e90", "D. \\u591a\\u7ebf\\u7a0b\\u5e76\\u884c"]', 'A', '所有进程统一从小到大申请资源，无法形成环形等待链。', '"\\u4e00\\u6b21\\u6027\\u7533\\u8bf7\\u7834\\u574f\\u5360\\u6709\\u5e76\\u7b49\\u5f85\\u6761\\u4ef6"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (117, NULL, '操作系统', '内存管理', '简单', '选择题', '程序逻辑地址转换为物理内存地址的过程称为？', '["A. \\u52a0\\u8f7d", "B. \\u5730\\u5740\\u91cd\\u5b9a\\u4f4d", "C. \\u5206\\u9875", "D. \\u5206\\u6bb5"]', 'B', '重定位分为静态装入时转换、运行时动态转换两类。', '"\\u52a8\\u6001\\u91cd\\u5b9a\\u4f4d\\u652f\\u6301\\u7a0b\\u5e8f\\u5185\\u5b58\\u79fb\\u52a8"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (118, NULL, '操作系统', '内存管理', '中等', '选择题', '动态可变分区分配产生的碎片类型是？', '["A. \\u5185\\u90e8\\u788e\\u7247", "B. \\u5916\\u90e8\\u788e\\u7247", "C. \\u9875\\u5185\\u788e\\u7247", "D. \\u65e0\\u788e\\u7247"]', 'B', '内存空闲块零散分布在进程之间，无法合并使用即外部碎片。', '"\\u5206\\u9875\\u5b58\\u50a8\\u4f1a\\u4ea7\\u751f\\u9875\\u5185\\u5185\\u90e8\\u788e\\u7247"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (119, NULL, '操作系统', '内存管理', '简单', '选择题', '进程访问未载入内存页面触发的中断是？', '["A. \\u65f6\\u949f\\u4e2d\\u65ad", "B. \\u7f3a\\u9875\\u4e2d\\u65ad", "C. \\u78c1\\u76d8\\u4e2d\\u65ad", "D. \\u7cfb\\u7edf\\u8c03\\u7528\\u4e2d\\u65ad"]', 'B', '缺页中断触发OS从磁盘交换分区读取页面载入主存。', '"\\u7f3a\\u9875\\u5c5e\\u4e8e\\u540c\\u6b65\\u5f02\\u5e38\\uff0c\\u975e\\u786c\\u4ef6\\u4e2d\\u65ad"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (120, NULL, '操作系统', '内存管理', '中等', '选择题', '以下页面置换算法会出现Belady异常的是？', '["A. OPT\\u6700\\u4f18\\u7f6e\\u6362", "B. FIFO\\u5148\\u8fdb\\u5148\\u51fa", "C. LRU\\u6700\\u8fd1\\u6700\\u5c11\\u4f7f\\u7528", "D. Clock\\u65f6\\u949f\\u7b97\\u6cd5"]', 'B', 'FIFO增加页框数量，缺页次数反而上升，称为Belady异常。', '"LRU\\u3001OPT\\u65e0Belady\\u5f02\\u5e38"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (121, NULL, '操作系统', '内存管理', '中等', '填空题', '____指页框不足时页面频繁换入换出，CPU利用率急剧下降。', '[]', '抖动', '进程工作集大于分配页框数量时产生抖动。', '"\\u6269\\u5927\\u9875\\u6846\\u81f3\\u8986\\u76d6\\u5de5\\u4f5c\\u96c6\\u53ef\\u6d88\\u9664\\u6296\\u52a8"', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (122, NULL, '操作系统', '文件管理', '简单', '选择题', '存储文件权限、大小、磁盘地址的数据结构是？', '["A. \\u7a0b\\u5e8f\\u6bb5", "B. FCB\\u6587\\u4ef6\\u63a7\\u5236\\u5757", "C. \\u8fdb\\u7a0bPCB", "D. \\u9875\\u8868"]', 'B', 'FCB存放文件全部元数据，Linux中简化为inode结构。', '"inode\\u4e0d\\u5b58\\u50a8\\u6587\\u4ef6\\u540d\\uff0c\\u6587\\u4ef6\\u540d\\u5b58\\u5728\\u76ee\\u5f55\\u9879"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (123, NULL, '操作系统', '文件管理', '简单', '选择题', 'Linux硬链接无法跨什么存储设备？', '["A. \\u76ee\\u5f55", "B. \\u78c1\\u76d8\\u5206\\u533a", "C. \\u7528\\u6237", "D. \\u6587\\u4ef6\\u7c7b\\u578b"]', 'B', '不同分区inode编号独立，硬链接共享inode，不能跨分区创建。', '"\\u8f6f\\u94fe\\u63a5\\u7b26\\u53f7\\u94fe\\u63a5\\u4e0d\\u53d7\\u5206\\u533a\\u9650\\u5236"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (124, NULL, '操作系统', '文件管理', '中等', '选择题', 'Linux成组链接法主要管理磁盘哪类资源？', '["A. \\u6587\\u4ef6inode", "B. \\u7a7a\\u95f2\\u78c1\\u76d8\\u5757", "C. \\u76ee\\u5f55\\u9879", "D. \\u8fdb\\u7a0b\\u9875"]', 'B', '成组链接批量记录空闲块，减少磁盘IO读写，是Linux标准空闲块管理方案。', '"\\u4f4d\\u793a\\u56fe\\u9002\\u5408\\u5c0f\\u578b\\u78c1\\u76d8\\u8bbe\\u5907"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (125, NULL, '操作系统', '输入输出管理', '简单', '选择题', '下列属于块设备的硬件是？', '["A. \\u952e\\u76d8", "B. \\u673a\\u68b0\\u786c\\u76d8", "C. \\u9f20\\u6807", "D. \\u663e\\u793a\\u5668"]', 'B', '块设备以扇区块为单位读写，支持随机寻址；字符设备逐字节流式读写。', '"\\u952e\\u76d8\\u3001\\u663e\\u793a\\u5668\\u5168\\u90e8\\u4e3a\\u5b57\\u7b26\\u8bbe\\u5907"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (126, NULL, '操作系统', '输入输出管理', '中等', '选择题', 'SPOOLing假脱机技术依托磁盘什么区域实现设备虚拟化？', '["A. \\u5185\\u5b58\\u7f13\\u51b2\\u533a", "B. \\u8f93\\u5165\\u8f93\\u51fa\\u4e95", "C. CPU\\u7f13\\u5b58", "D. \\u5bc4\\u5b58\\u5668"]', 'B', '磁盘开辟输入井、输出井，独占打印机虚拟为共享设备。', '"\\u6253\\u5370\\u670d\\u52a1\\u662fSPOOL\\u6700\\u5178\\u578b\\u5e94\\u7528\\u573a\\u666f"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (127, NULL, '操作系统', '输入输出管理', '中等', '选择题', '平均寻道时间最短的磁盘调度算法是？', '["A. FCFS\\u5148\\u6765\\u5148\\u670d\\u52a1", "B. SSTF\\u6700\\u77ed\\u5bfb\\u9053\\u4f18\\u5148", "C. SCAN\\u7535\\u68af\\u7b97\\u6cd5", "D. C-SCAN\\u5faa\\u73af\\u626b\\u63cf"]', 'B', 'SSTF每次访问距离当前磁道最近任务，但会产生饥饿问题。', '"SCAN\\u7535\\u68af\\u7b97\\u6cd5\\u89e3\\u51b3\\u9965\\u997f\\u7f3a\\u9677"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (128, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '计算机网络两大核心基础功能为？', '["A. \\u6570\\u636e\\u901a\\u4fe1\\u3001\\u8d44\\u6e90\\u5171\\u4eab", "B. \\u6570\\u636e\\u52a0\\u5bc6\\u3001\\u6570\\u636e\\u5907\\u4efd", "C. \\u8fdb\\u7a0b\\u8c03\\u5ea6\\u3001\\u5185\\u5b58\\u5206\\u914d", "D. \\u4fe1\\u53f7\\u8c03\\u5236\\u3001\\u4fe1\\u53f7\\u89e3\\u8c03"]', 'A', '计算机网络设计初衷一是实现跨设备数据传输，二是共享硬件、软件、数据各类资源。', '["\\u8d44\\u6e90\\u5171\\u4eab\\u5305\\u542b\\u786c\\u4ef6\\u5916\\u8bbe\\u3001\\u8f6f\\u4ef6\\u7a0b\\u5e8f\\u3001\\u6570\\u636e\\u5e93\\u6587\\u4ef6\\u4e09\\u7c7b"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (129, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '以下哪项不属于网络资源共享的覆盖范围？', '["A. \\u5c40\\u57df\\u7f51\\u5171\\u4eab\\u6253\\u5370\\u673a", "B. \\u4e91\\u7aef\\u6570\\u636e\\u5e93\\u6587\\u4ef6", "C. \\u5355\\u4e3b\\u673a\\u72ec\\u5360CPU\\u6838\\u5fc3", "D. \\u516c\\u5171\\u670d\\u52a1\\u5668\\u8f6f\\u4ef6"]', 'C', 'CPU单机独占属于本地硬件使用，不属于网络共享范畴，打印机、云存储、共享软件均为典型网络共享资源。', '["\\u6253\\u5370\\u5171\\u4eab\\u662f\\u4f01\\u4e1a\\u5c40\\u57df\\u7f51\\u6700\\u5e38\\u89c1\\u5e94\\u7528\\u573a\\u666f"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (130, NULL, '计算机网络', '计算机网络概述', '中等', '选择题', '通信子网的核心组成设备不包含？', '["A. \\u8def\\u7531\\u5668", "B. \\u4e8c\\u5c42\\u4ea4\\u6362\\u673a", "C. \\u4e1a\\u52a1\\u5e94\\u7528\\u670d\\u52a1\\u5668", "D. \\u5149\\u7ea4\\u4f20\\u8f93\\u94fe\\u8def"]', 'C', '服务器、PC主机属于资源子网，路由器、交换机、传输线缆属于负责转发的通信子网。', '["\\u901a\\u4fe1\\u5b50\\u7f51\\u53ea\\u505a\\u6570\\u636e\\u8f6c\\u53d1\\uff0c\\u4e0d\\u8fd0\\u884c\\u4e1a\\u52a1\\u7a0b\\u5e8f"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (131, NULL, '计算机网络', '计算机网络概述', '中等', '填空题', '计算机网络整体划分为____子网（数据转发）和____子网（业务资源承载）。', '[]', '通信,资源', '通信子网负责路由、帧转发；资源子网承载主机、数据库、网络应用服务。', '"\\u7f51\\u5361\\u662f\\u4e24\\u7c7b\\u5b50\\u7f51\\u7684\\u5bf9\\u63a5\\u786c\\u4ef6"', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (132, NULL, '计算机网络', '计算机网络概述', '困难', '简答题', '详细区分通信子网与资源子网的硬件构成、核心职责，并举3组典型设备对比说明。', '[]', '1.通信子网：设备有路由器、交换机、光纤、网卡；职责：处理比特、帧、分组转发，完成跨设备数据传输，不运行业务；2.资源子网：设备有台式机、云服务器、网络打印机；职责：提供可共享软硬件、数据，承载用户应用；设备对比：路由器（通信）vs文件服务器（通信）；交换机（通信）vs办公PC（资源）；光纤（通信）vs共享存储（资源）。', '通信子网是网络传输底层底座，资源子网面向终端用户业务需求。', '"\\u65e0\\u901a\\u4fe1\\u5b50\\u7f51\\uff0c\\u8d44\\u6e90\\u5b50\\u7f51\\u8bbe\\u5907\\u65e0\\u6cd5\\u4e92\\u901a"', '', 'seed', '2026-06-26 02:44:21.016401', 'essay', '[]', 0),
  (133, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '按地理覆盖范围，城市政务网属于？', '["A. PAN\\u4e2a\\u4eba\\u7f51", "B. LAN\\u5c40\\u57df\\u7f51", "C. MAN\\u57ce\\u57df\\u7f51", "D. WAN\\u5e7f\\u57df\\u7f51"]', 'C', 'MAN覆盖一座城市；LAN仅校园/园区；WAN跨省市国家；PAN仅蓝牙短距设备。', '["\\u4e92\\u8054\\u7f51\\u6574\\u4f53\\u5c5e\\u4e8e\\u5e7f\\u57df\\u7f51\\u8303\\u7574"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (134, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '骨干广域网采用哪种拓扑保障链路容错？', '["A. \\u661f\\u578b", "B. \\u603b\\u7ebf\\u578b", "C. \\u7f51\\u72b6\\u578b", "D. \\u73af\\u578b"]', 'C', '网状拓扑设备间多冗余链路，单条线路断开自动切换备用路径，可靠性最高。', '["\\u661f\\u578b\\u4e2d\\u5fc3\\u4ea4\\u6362\\u673a\\u6545\\u969c\\u4f1a\\u5168\\u7f51\\u65ad\\u7f51"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (135, NULL, '计算机网络', '计算机网络概述', '中等', '选择题', '家用宽带路由器组网主流拓扑为？', '["A. \\u603b\\u7ebf\\u540c\\u8f74\\u62d3\\u6251", "B. \\u661f\\u578b\\u62d3\\u6251", "C. \\u73af\\u5f62\\u4ee4\\u724c\\u7f51", "D. \\u5168\\u8fde\\u63a5\\u7f51\\u72b6\\u62d3\\u6251"]', 'B', '星型以路由器/交换机为中心，各设备独立连线，故障设备单独隔离，运维简单。', '["\\u65e9\\u671f\\u6821\\u56ed\\u540c\\u8f74\\u7f51\\u7ebf\\u4f7f\\u7528\\u603b\\u7ebf\\u62d3\\u6251"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (136, NULL, '计算机网络', '计算机网络概述', '中等', '填空题', '局域网标准拓扑为____，广域网骨干冗余拓扑为____。', '[]', '星型,网状型', '局域网追求低成本易排查；广域网优先高可用多备份链路。', '["\\u73af\\u5f62\\u62d3\\u6251\\u4e00\\u5904\\u65ad\\u7ebf\\u6574\\u4f53\\u762b\\u75ea"]', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (137, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '网络分层模型最大设计优势是？', '["A. \\u63d0\\u5347\\u5149\\u7ea4\\u4f20\\u8f93\\u901f\\u7387", "B. \\u5c42\\u95f4\\u89e3\\u8026\\uff0c\\u534f\\u8bae\\u72ec\\u7acb\\u8fed\\u4ee3", "C. \\u51cf\\u5c11\\u670d\\u52a1\\u5668\\u6570\\u91cf", "D. \\u7b80\\u5316\\u7f51\\u7ebf\\u5e03\\u7ebf"]', 'B', '每层仅依赖紧邻下层标准接口，修改单层协议无需改动其余层级，便于标准化开发维护。', '["\\u5bf9\\u7b49\\u5c42\\u865a\\u62df\\u901a\\u4fe1\\u662f\\u5206\\u5c42\\u6838\\u5fc3\\u903b\\u8f91"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (138, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', '对等层实体交互数据单元标准名称是？', '["A. \\u6bd4\\u7279\\u6d41", "B. PDU\\u534f\\u8bae\\u6570\\u636e\\u5355\\u5143", "C. \\u539f\\u59cb\\u62a5\\u6587", "D. \\u4f20\\u8f93\\u5e27"]', 'B', 'PDU是各层对等通信统一名称，不同层级PDU别名：段、包、帧、比特。', '"\\u4e0a\\u5c42\\u4ea4\\u7ed9\\u4e0b\\u5c42\\u7684\\u6570\\u636e\\u79f0\\u4e3aSDU\\u670d\\u52a1\\u6570\\u636e\\u5355\\u5143"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (139, NULL, '计算机网络', '计算机网络概述', '中等', '选择题', '下列行为违反分层设计规范的是？', '["A. \\u4e0a\\u5c42\\u4ec5\\u8c03\\u7528\\u7d27\\u90bb\\u4e0b\\u5c42\\u63a5\\u53e3", "B. \\u8de8\\u591a\\u5c42\\u76f4\\u63a5\\u8bfb\\u5199\\u5e95\\u5c42\\u6bd4\\u7279", "C. \\u6bcf\\u5c42\\u529f\\u80fd\\u5355\\u4e00\\u4e0d\\u6df7\\u6742", "D. \\u5c42\\u95f4\\u63a5\\u53e3\\u7b80\\u6d01\\u6807\\u51c6\\u5316"]', 'B', '分层严格禁止跨层交互，上层只能与直接相邻下层交互。', '["\\u5206\\u5c42\\u8fc7\\u591a\\u4f1a\\u589e\\u52a0\\u5934\\u90e8\\u5b57\\u8282\\u5f00\\u9500"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (140, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', 'OSI七层最底层负责原始0/1信号传输的层级是？', '["A. \\u6570\\u636e\\u94fe\\u8def\\u5c42", "B. \\u7269\\u7406\\u5c42", "C. \\u7f51\\u7edc\\u5c42", "D. \\u4f20\\u8f93\\u5c42"]', 'B', '物理层处理电、光信号，只传输比特流，无帧、分组封装逻辑。', '["\\u7f51\\u7ebf\\u3001\\u96c6\\u7ebf\\u5668\\u5c5e\\u4e8e\\u7269\\u7406\\u5c42\\u8bbe\\u5907"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (141, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', 'OSI中实现跨网段IP寻址路由的层级为？', '["A. \\u4f20\\u8f93\\u5c42", "B. \\u7f51\\u7edc\\u5c42", "C. \\u4f1a\\u8bdd\\u5c42", "D. \\u8868\\u793a\\u5c42"]', 'B', '网络层核心IP协议，负责异构网络互联、分组转发；交换机仅链路层。', '["\\u8def\\u7531\\u5668\\u662f\\u7f51\\u7edc\\u5c42\\u4e13\\u5c5e\\u8bbe\\u5907"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (142, NULL, '计算机网络', '计算机网络概述', '中等', '选择题', 'OSI七层从上至下正确排序是？', '["A. \\u5e94\\u7528\\u3001\\u8868\\u793a\\u3001\\u4f1a\\u8bdd\\u3001\\u4f20\\u8f93\\u3001\\u7f51\\u7edc\\u3001\\u94fe\\u8def\\u3001\\u7269\\u7406", "B. \\u7269\\u7406\\u3001\\u94fe\\u8def\\u3001\\u7f51\\u7edc\\u3001\\u4f20\\u8f93\\u3001\\u4f1a\\u8bdd\\u3001\\u8868\\u793a\\u3001\\u5e94\\u7528", "C. \\u5e94\\u7528\\u3001\\u4f20\\u8f93\\u3001\\u7f51\\u7edc\\u3001\\u94fe\\u8def\\u3001\\u7269\\u7406\\u3001\\u4f1a\\u8bdd\\u3001\\u8868\\u793a", "D. \\u4f1a\\u8bdd\\u3001\\u8868\\u793a\\u3001\\u5e94\\u7528\\u3001\\u4f20\\u8f93\\u3001\\u7f51\\u7edc\\u3001\\u94fe\\u8def\\u3001\\u7269\\u7406"]', 'A', '七层顺序记忆口诀：应表会传网链物。', '["\\u5e94\\u7528\\u5c42\\u76f4\\u63a5\\u5bf9\\u63a5\\u7528\\u6237\\u7a0b\\u5e8f"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (143, NULL, '计算机网络', '计算机网络概述', '中等', '填空题', 'OSI中管控端口端到端连接的是____层；处理MAC帧与局域网校验为____层。', '[]', '传输,数据链路', '传输层TCP/UDP区分应用端口；链路层封装帧、处理二层寻址。', '["\\u4e8c\\u5c42\\u4ea4\\u6362\\u673a\\u53ea\\u8bc6\\u522bMAC\\uff0c\\u65e0\\u6cd5\\u8de8\\u7f51\\u6bb5\\u8f6c\\u53d1"]', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (144, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', 'TCP/IP四层模型合并了OSI哪两层至应用层？', '["A. \\u7269\\u7406\\u3001\\u6570\\u636e\\u94fe\\u8def", "B. \\u4f1a\\u8bdd\\u3001\\u8868\\u793a", "C. \\u7f51\\u7edc\\u3001\\u4f20\\u8f93", "D. \\u7f51\\u7edc\\u63a5\\u53e3\\u3001\\u5e94\\u7528"]', 'B', 'TCP/IP简化分层，舍弃独立会话层、表示层，全部功能并入应用层。', '["TCP/IP\\u7f51\\u7edc\\u63a5\\u53e3\\u5c42\\u7b49\\u4ef7OSI\\u7269\\u7406+\\u94fe\\u8def"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (145, NULL, '计算机网络', '计算机网络概述', '简单', '选择题', 'TCP/IP网际层核心标准协议是？', '["A. TCP", "B. UDP", "C. IP", "D. HTTP"]', 'C', 'IP协议提供跨网段寻址基础，TCP、UDP属于上层传输协议。', '["\\u6240\\u6709\\u4e92\\u8054\\u7f51\\u6570\\u636e\\u90fd\\u5c01\\u88c5IP\\u5934\\u90e8"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (146, NULL, '计算机网络', '计算机网络概述', '中等', '选择题', 'HTTP、DNS、FTP归属TCP/IP哪一层？', '["A. \\u7f51\\u7edc\\u63a5\\u53e3\\u5c42", "B. \\u7f51\\u9645\\u5c42", "C. \\u4f20\\u8f93\\u5c42", "D. \\u5e94\\u7528\\u5c42"]', 'D', '所有面向用户业务应用协议统一划分至TCP/IP应用层。', '["\\u5e94\\u7528\\u5c42\\u878d\\u5408OSI\\u5e94\\u7528\\u3001\\u8868\\u793a\\u3001\\u4f1a\\u8bdd\\u4e09\\u5c42\\u5168\\u90e8\\u80fd\\u529b"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (147, NULL, '计算机网络', '物理层', '简单', '选择题', '不属于物理层四大规范特性的是？', '["A. \\u673a\\u68b0\\u7279\\u6027", "B. \\u7535\\u6c14\\u7279\\u6027", "C. \\u8def\\u7531\\u8f6c\\u53d1\\u7279\\u6027", "D. \\u89c4\\u7a0b\\u7279\\u6027"]', 'C', '物理层四特性：机械、电气、功能、路由；路由属于网络层功能。', '["\\u673a\\u68b0\\u7279\\u6027\\u5b9a\\u4e49\\u63a5\\u53e3\\u9488\\u811a\\u5c3a\\u5bf8"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (148, NULL, '计算机网络', '物理层', '中等', '填空题', '物理层____特性规定电平高低代表0/1；____特性定义每个针脚传输信号类型。', '[]', '电气,功能', '电气规范信号电压；功能区分数据、时钟、地线针脚。', '["\\u89c4\\u7a0b\\u7279\\u6027\\u5b9a\\u4e49\\u4fe1\\u53f7\\u6536\\u53d1\\u65f6\\u5e8f"]', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (149, NULL, '计算机网络', '物理层', '简单', '选择题', '远距离骨干传输抗干扰最优介质是？', '["A. \\u516d\\u7c7b\\u53cc\\u7ede\\u7ebf", "B. \\u540c\\u8f74\\u7535\\u7f06", "C. \\u5355\\u6a21\\u5149\\u7ea4", "D. 2.4G\\u65e0\\u7ebfWiFi"]', 'C', '光纤依靠光信号传输，无电磁干扰，传输距离可达数十公里。', '["\\u53cc\\u7ede\\u7ebf\\u4ec5\\u9002\\u5408\\u767e\\u7c73\\u4ee5\\u5185\\u5c40\\u57df\\u7f51"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (150, NULL, '计算机网络', '物理层', '简单', '选择题', '企业办公室千兆内网标准布线介质是？', '["A. \\u5355\\u6a21\\u5149\\u7ea4", "B. \\u8d85\\u4e94\\u7c7b/\\u516d\\u7c7b\\u53cc\\u7ede\\u7ebf", "C. \\u7c97\\u540c\\u8f74\\u7535\\u7f06", "D. \\u5fae\\u6ce2\\u65e0\\u7ebf"]', 'B', '双绞线布线成本低、施工简单，适配园区内部千兆网络。', '["\\u5149\\u7ea4\\u7528\\u4e8e\\u697c\\u5b87\\u4e4b\\u95f4\\u8fdc\\u8ddd\\u79bb\\u4e92\\u8054"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (151, NULL, '计算机网络', '物理层', '中等', '选择题', '广播电台单向信号传输属于哪种信道？', '["A. \\u5355\\u5de5\\u4fe1\\u9053", "B. \\u534a\\u53cc\\u5de5\\u4fe1\\u9053", "C. \\u5168\\u53cc\\u5de5\\u4fe1\\u9053", "D. \\u540c\\u6b65\\u4fe1\\u9053"]', 'A', '单工仅单一固定方向传输；网线属于全双工可同时收发。', '["\\u5bf9\\u8bb2\\u673a\\u5c5e\\u4e8e\\u534a\\u53cc\\u5de5\\uff0c\\u6536\\u53d1\\u4e0d\\u80fd\\u540c\\u6b65"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (152, NULL, '计算机网络', '物理层', '简单', '选择题', '数字信号转换为模拟载波信号的操作称为？', '["A. \\u7f16\\u7801", "B. \\u8c03\\u5236", "C. \\u89e3\\u8c03", "D. \\u89e3\\u7801"]', 'B', '调制：数字→模拟；解调：模拟还原数字；编码仅数字格式转换。', '["\\u5bb6\\u7528Modem\\u6838\\u5fc3\\u4e3a\\u8c03\\u5236\\u89e3\\u8c03\\u6a21\\u5757"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (153, NULL, '计算机网络', '物理层', '中等', '选择题', '传统以太网标准基带编码方案是？', '["A. \\u66fc\\u5f7b\\u65af\\u7279\\u7f16\\u7801", "B. NRZ\\u4e0d\\u5f52\\u96f6\\u7f16\\u7801", "C. 4B/5B\\u7f16\\u7801", "D. AM\\u5e45\\u5ea6\\u8c03\\u5236"]', 'A', '曼彻斯特每个码元中间存在电平跳变，自带同步时钟，早期以太网强制标准。', '["\\u767e\\u5146\\u5149\\u7ea4\\u4f7f\\u75284B/5B\\u7f16\\u7801\\u8282\\u7701\\u5e26\\u5bbd"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (154, NULL, '计算机网络', '物理层', '中等', '选择题', '无噪声理想信道极限码元速率依靠？', '["A. \\u9999\\u519c\\u516c\\u5f0f", "B. \\u5948\\u594e\\u65af\\u7279\\u5b9a\\u7406", "C. \\u5085\\u91cc\\u53f6\\u53d8\\u6362\\u516c\\u5f0f", "D. \\u5e26\\u5bbd\\u6362\\u7b97\\u516c\\u5f0f"]', 'B', '奈奎斯特计算无噪声最大码元；香农用于存在噪声场景极限比特速率。', '["\\u9999\\u519c\\u516c\\u5f0f\\u5305\\u542b\\u4fe1\\u566a\\u6bd4S/N\\u53c2\\u6570"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (155, NULL, '计算机网络', '物理层', '中等', '填空题', '____公式用于计算存在噪声信道的理论最大数据传输速率。', '[]', '香农', '香农公式 C=Wlog2(1+S/N)，带宽、信噪比共同决定上限。', '["\\u4fe1\\u566a\\u6bd4\\u8d8a\\u9ad8\\uff0c\\u4fe1\\u9053\\u53ef\\u627f\\u8f7d\\u901f\\u7387\\u8d8a\\u5927"]', '', 'seed', '2026-06-26 02:44:21.016401', 'fill', '[]', 0),
  (156, NULL, '计算机网络', '数据链路层', '简单', '选择题', '数据链路层对等层传输数据单元名称为？', '["A. \\u6bb5", "B. IP\\u5206\\u7ec4", "C. \\u5e27", "D. \\u539f\\u59cb\\u6bd4\\u7279\\u6d41"]', 'C', '链路层PDU是帧，封装MAC头部、校验尾部；网络层为分组。', '["\\u5e27\\u5185\\u5305\\u542b\\u6e90\\u3001\\u76ee\\u6807\\u4e8c\\u5c42\\u786c\\u4ef6\\u5730\\u5740"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (157, NULL, '计算机网络', '数据链路层', '简单', '选择题', '不属于数据链路层标准功能的是？', '["A. MAC\\u5730\\u5740\\u5bfb\\u5740", "B. CRC\\u5dee\\u9519\\u68c0\\u6d4b", "C. \\u8de8\\u7f51\\u6bb5IP\\u8def\\u7531\\u8f6c\\u53d1", "D. \\u5e27\\u540c\\u6b65\\u5c01\\u88c5\\u89e3\\u5c01\\u88c5"]', 'C', '跨网段路由是网络层IP专属功能，链路仅局域网内转发。', '["\\u4ea4\\u6362\\u673a\\u65e0\\u6cd5\\u8bc6\\u522b\\u4e09\\u5c42IP\\u5730\\u5740"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (158, NULL, '计算机网络', '数据链路层', '中等', '选择题', 'CRC循环冗余校验核心优势是？', '["A. \\u53ef\\u4ee5\\u81ea\\u52a8\\u7ea0\\u6b63\\u5168\\u90e8\\u4f20\\u8f93\\u9519\\u8bef", "B. \\u68c0\\u9519\\u80fd\\u529b\\u6781\\u5f3a\\uff0c\\u786c\\u4ef6\\u7535\\u8def\\u6613\\u5b9e\\u73b0", "C. \\u65e0\\u4efb\\u4f55\\u989d\\u5916\\u6821\\u9a8c\\u5b57\\u8282\\u5f00\\u9500", "D. \\u652f\\u6301\\u5206\\u6bb5\\u72ec\\u7acb\\u6821\\u9a8c\\u5206\\u7247"]', 'B', 'CRC能检出绝大多数随机差错，硬件逻辑简单，以太网强制校验标准。', '["CRC\\u4ec5\\u68c0\\u9519\\uff0c\\u4e0d\\u5177\\u5907\\u81ea\\u52a8\\u7ea0\\u9519\\u80fd\\u529b"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (159, NULL, '计算机网络', '数据链路层', '中等', '选择题', '停止等待协议发送端最多缓存未确认帧数量？', '["A. 1\\u4e2a", "B. \\u6ed1\\u52a8\\u7a97\\u53e3\\u957f\\u5ea6\\u503c", "C. \\u65e0\\u4e0a\\u9650", "D. 2\\u4e2a\\u5907\\u7528\\u5e27"]', 'A', '每发送一帧必须等待接收方ACK确认后才能发下一帧，仅缓存单帧。', '["GBN\\u3001\\u9009\\u62e9\\u91cd\\u4f20\\u4f9d\\u9760\\u6ed1\\u52a8\\u7a97\\u53e3\\u63d0\\u5347\\u541e\\u5410"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (160, NULL, '计算机网络', '数据链路层', '中等', '选择题', '帧丢失时仅重传损坏帧的滑动窗口协议是？', '["A. \\u505c\\u6b62\\u7b49\\u5f85", "B. GBN\\u540e\\u9000N\\u5e27", "C. \\u9009\\u62e9\\u91cd\\u4f20", "D. \\u900f\\u660e\\u4f20\\u8f93\\u534f\\u8bae"]', 'C', 'GBN丢失一帧会重传全部后续帧；选择重传仅重传出错单帧，带宽利用率更高。', '["\\u9009\\u62e9\\u91cd\\u4f20\\u63a5\\u6536\\u7a97\\u53e3\\u5927\\u5c0f\\u5927\\u4e8e1"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (161, NULL, '计算机网络', '数据链路层', '简单', '选择题', '标准MAC地址二进制总位数为？', '["A. 32bit", "B. 48bit", "C. 128bit", "D. 16bit"]', 'B', 'MAC地址6字节48位，前24位厂商编号，后24位设备唯一序列号。', '["IPv4 32\\u4f4d\\u3001IPv6 128\\u4f4d"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (162, NULL, '计算机网络', '数据链路层', '中等', '选择题', 'ARP协议核心解析功能是？', '["A. MAC\\u5730\\u5740\\u8f6cIP\\u5730\\u5740", "B. IP\\u5730\\u5740\\u67e5\\u8be2\\u5bf9\\u5e94MAC\\u786c\\u4ef6\\u5730\\u5740", "C. \\u57df\\u540d\\u89e3\\u6790IP", "D. \\u5e94\\u7528\\u7aef\\u53e3\\u6620\\u5c04"]', 'B', '局域网广播ARP请求，根据目标IP获取二层MAC地址用于封装帧。', '"RARP\\u5b9e\\u73b0MAC\\u53cd\\u5411\\u89e3\\u6790IP\\u5730\\u5740"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (163, NULL, '计算机网络', '网络层', '简单', '选择题', 'A类IPv4地址首个固定比特值是？', '["A. 0", "B. 10", "C. 110", "D. 1110"]', 'A', 'A类0开头；B类10；C类110；D组播1110；E保留1111。', '["A\\u7c7b\\u9ed8\\u8ba4\\u63a9\\u7801255.0.0.0"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (164, NULL, '计算机网络', '网络层', '中等', '选择题', '子网掩码255.255.252对应主机位数量？', '["A. 2\\u4f4d", "B. 8\\u4f4d", "C. 10\\u4f4d", "D. 14\\u4f4d"]', 'A', '252二进制11111100，末尾2比特为主机位，可用主机2^2-2（去除网络、广播地址）。', '["\\u7f51\\u7edc\\u5730\\u5740\\u4e0e\\u5e7f\\u64ad\\u5730\\u5740\\u4e0d\\u53ef\\u5206\\u914d\\u7ec8\\u7aef\\u8bbe\\u5907"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (165, NULL, '计算机网络', '网络层', '中等', '选择题', 'IP分片依靠哪个字段完成接收端重组？', '["A. \\u6e90IP\\u5730\\u5740", "B. \\u6807\\u8bc6ID", "C. TTL\\u751f\\u5b58\\u65f6\\u95f4", "D. \\u4e0a\\u5c42\\u534f\\u8bae\\u53f7"]', 'B', '同一原始数据包所有分片ID完全相同，接收端依靠ID+片偏移重组完整报文。', '["\\u6807\\u5fd7\\u4f4d\\u63a7\\u5236\\u662f\\u5426\\u5141\\u8bb8\\u8def\\u7531\\u5668\\u5206\\u7247"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (166, NULL, '计算机网络', '网络层', '简单', '选择题', '路由表最长匹配规则含义是？', '["A. \\u5b50\\u7f51\\u63a9\\u7801\\u524d\\u7f00\\u8d8a\\u957f\\u8def\\u7531\\u6761\\u76ee\\u4f18\\u5148\\u7ea7\\u8d8a\\u9ad8", "B. IP\\u6570\\u503c\\u8d8a\\u5927\\u4f18\\u5148\\u8f6c\\u53d1", "C. \\u8df3\\u6570\\u8d8a\\u5c11\\u4f18\\u5148\\u9009\\u7528", "D. \\u94fe\\u8def\\u5e26\\u5bbd\\u8d8a\\u9ad8\\u4f18\\u5148\\u5339\\u914d"]', 'A', '同一目标存在多条路由时，掩码长度越长代表网段越精准，优先匹配。', '["\\u9ed8\\u8ba4\\u8def\\u7531\\u63a9\\u7801\\u957f\\u5ea60\\uff0c\\u4f18\\u5148\\u7ea7\\u6700\\u4f4e"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (167, NULL, '计算机网络', '网络层', '中等', '选择题', 'RIP路由协议度量标准是？', '["A. \\u94fe\\u8def\\u5e26\\u5bbd", "B. \\u7ecf\\u8fc7\\u8def\\u7531\\u5668\\u8df3\\u6570hop", "C. \\u4f20\\u8f93\\u5ef6\\u8fdf", "D. \\u94fe\\u8def\\u8d1f\\u8f7d"]', 'B', 'RIP仅统计路由经过设备数量，最大有效跳数15，16判定不可达。', '["RIP\\u4ec5\\u9002\\u914d\\u4e2d\\u5c0f\\u578b\\u56ed\\u533a\\u7f51\\u7edc"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (168, NULL, '计算机网络', '网络层', '中等', '选择题', 'OSPF路由计算依托哪种经典最短路径算法？', '["A. \\u8d1d\\u5c14\\u66fc\\u798f\\u7279", "B. Dijkstra\\u8fea\\u6770\\u65af\\u7279\\u62c9", "C. Floyd\\u591a\\u6e90", "D. DFS\\u6df1\\u5ea6\\u904d\\u5386"]', 'B', 'OSPF泛洪全网链路状态，本地运行Dijkstra生成最短路径树。', '["OSPF\\u9002\\u914d\\u5927\\u578b\\u8de8\\u533a\\u57df\\u9aa8\\u5e72\\u7f51"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (169, NULL, '计算机网络', '网络层', '简单', '选择题', 'ping连通性探测使用哪类报文协议？', '["A. TCP", "B. UDP", "C. ICMP", "D. ARP"]', 'C', 'ping发送ICMP回送请求报文，目标主机回复应答报文检测延迟与连通性。', '"\\u8def\\u7531\\u4e0d\\u53ef\\u8fbe\\u3001\\u8d85\\u65f6\\u63d0\\u793a\\u5747\\u4e3aICMP\\u62a5\\u6587\\u7c7b\\u578b"', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (170, NULL, '计算机网络', '传输层', '简单', '选择题', 'HTTP明文网页标准知名端口号是？', '["A. 21", "B. 80", "C. 443", "D. 22"]', 'B', '80=HTTP；443=HTTPS加密；21=FTP控制；22=SSH远程。', '["\\u77e5\\u540d\\u7aef\\u53e3\\u8303\\u56f40~1023"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (171, NULL, '计算机网络', '传输层', '简单', '选择题', 'UDP协议核心特征描述正确的是？', '["A. \\u9762\\u5411\\u8fde\\u63a5\\u53ef\\u9760\\u4f20\\u8f93", "B. \\u65e0\\u8fde\\u63a5\\u3001\\u65e0\\u786e\\u8ba4\\u3001\\u5f00\\u9500\\u6781\\u4f4e", "C. \\u5185\\u7f6e\\u6d41\\u91cf\\u62e5\\u585e\\u63a7\\u5236", "D. \\u62a5\\u6587\\u6709\\u5e8f\\u4ea4\\u4ed8"]', 'B', 'UDP不建立连接、无重传机制，实时音视频、DNS优先选用。', '["TCP\\u4e3a\\u9762\\u5411\\u8fde\\u63a5\\u53ef\\u9760\\u534f\\u8bae"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (172, NULL, '计算机网络', '传输层', '中等', '选择题', '三次握手第二次服务端返回报文标志位为？', '["A. SYN", "B. SYN+ACK", "C. ACK", "D. FIN"]', 'B', '客户端SYN；服务端SYN同步+ACK确认；客户端单独ACK完成连接。', '["FIN\\u7528\\u4e8e\\u65ad\\u5f00\\u8fde\\u63a5"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (173, NULL, '计算机网络', '传输层', '中等', '选择题', 'TCP断开需要四次报文交互的根本原因？', '["A. \\u8def\\u7531\\u5668\\u8f6c\\u53d1\\u5ef6\\u8fdf\\u5927", "B. \\u6536\\u53d1\\u53cc\\u5411\\u6570\\u636e\\u6d41\\u72ec\\u7acb\\u5173\\u95ed", "C. \\u9632\\u6b62IP\\u5206\\u7247\\u4e22\\u5931", "D. \\u7aef\\u53e3\\u8d44\\u6e90\\u590d\\u7528\\u6821\\u9a8c"]', 'A', 'TCP全双工双向传输，收发通道可独立关闭，无法一次双向断开。', '["\\u53d1\\u9001FIN\\u4ec5\\u505c\\u6b62\\u53d1\\u9001\\uff0c\\u4ecd\\u53ef\\u63a5\\u6536\\u5bf9\\u65b9\\u6570\\u636e"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (174, NULL, '计算机网络', '传输层', '中等', '选择题', 'TCP流量控制依靠哪个字段限制发送速率？', '["A. \\u5e8f\\u5217\\u53f7", "B. \\u63a5\\u6536\\u7a97\\u53e3rwnd", "C. \\u6821\\u9a8c\\u548c", "D. \\u7d27\\u6025\\u6307\\u9488"]', 'B', '接收端通告rwnd告知发送端本机剩余缓存，避免溢出丢包。', '["\\u62e5\\u585e\\u63a7\\u5236cwnd\\u7ba1\\u63a7\\u7f51\\u7edc\\u94fe\\u8def\\u8d1f\\u8f7d"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (175, NULL, '计算机网络', '应用层', '简单', '选择题', 'DNS核心转换功能是？', '["A. MAC\\u8f6cIP", "B. \\u57df\\u540d\\u6620\\u5c04IP\\u5730\\u5740", "C. \\u7aef\\u53e3\\u5206\\u914d", "D. \\u8def\\u7531\\u8ba1\\u7b97"]', 'B', '将人类可读域名转换为机器识别的IP地址。', '["DNS\\u9ed8\\u8ba4UDP 53\\u7aef\\u53e3"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (176, NULL, '计算机网络', '应用层', '简单', '选择题', 'HTTPS在TCP与HTTP之间增加安全协议层为？', '["A. ICMP", "B. TLS/SSL", "C. ARP", "D. UDP"]', 'B', 'HTTP明文传输；HTTPS通过TLS加密所有业务数据防窃听篡改。', '["HTTPS\\u6807\\u51c6\\u7aef\\u53e3443"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (177, NULL, '计算机网络', '应用层', '中等', '选择题', 'FTP协议控制命令传输默认端口是？', '["A. 20", "B. 21", "C. 80", "D. 22"]', 'B', '21端口传输登录、文件操作命令；20为主动模式数据端口。', '["\\u88ab\\u52a8\\u6a21\\u5f0f\\u6570\\u636e\\u7aef\\u53e3\\u968f\\u673a\\u9ad8\\u4f4d"]', '', 'seed', '2026-06-26 02:44:21.016401', 'choice', '[]', 0),
  (178, NULL, '数据结构', '绪论', '简单', '选择题', '下列关于数据四层定义说法正确的是？', '["A. \\u6570\\u636e\\u9879\\u662f\\u6570\\u636e\\u7684\\u57fa\\u672c\\u5904\\u7406\\u5355\\u4f4d", "B. \\u6570\\u636e\\u5143\\u7d20\\u662f\\u4e0d\\u53ef\\u5206\\u5272\\u6700\\u5c0f\\u6807\\u8bc6\\u5355\\u4f4d", "C. \\u6570\\u636e\\u5bf9\\u8c61\\u662f\\u6027\\u8d28\\u76f8\\u540c\\u7684\\u6570\\u636e\\u5143\\u7d20\\u96c6\\u5408", "D. \\u6570\\u636e\\u7b49\\u4e8e\\u6570\\u636e\\u5bf9\\u8c61"]', 'C', '数据元素是基本处理单位，数据项是最小标识单位；数据是所有符号集合，范围大于数据对象。', '["\\u8bb0\\u5fc6\\u5c42\\u7ea7\\uff1a\\u6570\\u636e > \\u6570\\u636e\\u5bf9\\u8c61 > \\u6570\\u636e\\u5143\\u7d20 > \\u6570\\u636e\\u9879"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (179, NULL, '数据结构', '绪论', '简单', '选择题', '逻辑结构分为线性与非线性，下列属于非线性的是？', '["A. \\u987a\\u5e8f\\u8868", "B. \\u6808", "C. \\u56fe", "D. \\u961f\\u5217"]', 'C', '线性结构一对一（线性表/栈/队列）；树一对多、图多对多属于非线性。', '["\\u7ebf\\u6027\\u7ed3\\u6784\\u4ec5\\u6709\\u552f\\u4e00\\u524d\\u9a71\\u540e\\u7ee7"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (180, NULL, '数据结构', '绪论', '中等', '简答题', '简述四种存储结构（顺序、链式、索引、散列）的优缺点与适用场景。', '[]', '1.顺序存储：连续内存，随机存取快，扩容受限；适合长度固定数据。2.链式存储：离散指针，增删高效，无法随机访问；适合动态频繁修改。3.索引存储：附加索引表查找快，额外空间开销大；适合海量有序数据。4.散列存储：哈希映射平均O(1)查找，存在哈希冲突；适合键值快速查询。', '核心区分维度：内存排布、查找效率、增删开销、空间占用。', '["\\u6563\\u5217\\u4e0d\\u80fd\\u4fdd\\u8bc1\\u6709\\u5e8f\\u904d\\u5386"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (181, NULL, '数据结构', '绪论', '简单', '选择题', '不属于数据结构三要素的是？', '["A. \\u903b\\u8f91\\u7ed3\\u6784", "B. \\u5b58\\u50a8\\u7ed3\\u6784", "C. \\u6570\\u636e\\u8fd0\\u7b97", "D. \\u5185\\u5b58\\u5927\\u5c0f"]', 'D', '三要素：逻辑结构、存储结构、增删改查排序五类数据运算。', '["\\u8fd0\\u7b97\\u5b9a\\u4e49\\u53ea\\u548c\\u903b\\u8f91\\u6709\\u5173\\uff0c\\u5b9e\\u73b0\\u4f9d\\u8d56\\u5b58\\u50a8"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (182, NULL, '数据结构', '绪论', '中等', '填空题', '数据运算仅依赖____结构定义，运算实现由____结构决定。', '[]', '逻辑,存储', '不管数组还是链表，查找操作定义一致，但代码实现完全不同。', '["\\u903b\\u8f91\\u662f\\u62bd\\u8c61\\u5173\\u7cfb\\uff0c\\u5b58\\u50a8\\u662f\\u7269\\u7406\\u5b9e\\u73b0"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (183, NULL, '数据结构', '绪论', '简单', '选择题', '算法与程序最核心区分特性是？', '["A. \\u786e\\u5b9a\\u6027", "B. \\u6709\\u7a77\\u6027", "C. \\u53ef\\u884c\\u6027", "D. \\u8f93\\u5165"]', 'B', '算法必须有限步骤终止，程序可无限循环，不满足有穷性。', '["\\u7b97\\u6cd5\\u4e94\\u5927\\u7279\\u6027\\uff1a\\u6709\\u7a77\\u3001\\u786e\\u5b9a\\u3001\\u53ef\\u884c\\u3001\\u8f93\\u5165\\u3001\\u8f93\\u51fa"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (184, NULL, '数据结构', '绪论', '简单', '选择题', '下列不属于算法设计目标的是？', '["A. \\u53ef\\u8bfb\\u6027", "B. \\u5065\\u58ee\\u6027", "C. \\u65e0\\u9650\\u5faa\\u73af", "D. \\u9ad8\\u6548\\u7387\\u4f4e\\u5b58\\u50a8"]', 'C', '无限循环违背有穷性，不是设计目标。', '["\\u5de5\\u7a0b\\u4f18\\u5148\\u4fdd\\u8bc1\\u53ef\\u8bfb\\u6027"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (185, NULL, '数据结构', '绪论', '中等', '填空题', '渐进时间复杂度仅保留____，408考题默认采用____复杂度作为评判标准。', '[]', '最高阶项,最坏', '常数、低次项、系数全部忽略，最坏情况是统一考试标准。', '["\\u6700\\u597d/\\u5e73\\u5747\\u4ec5\\u4f5c\\u62d3\\u5c55\\u8003\\u70b9"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (186, NULL, '数据结构', '绪论', '中等', '选择题', '计算空间复杂度时，以下哪部分不计入辅助空间？', '["A. \\u4e34\\u65f6\\u53d8\\u91cf", "B. \\u9012\\u5f52\\u6808", "C. \\u8f93\\u5165\\u6570\\u7ec4", "D. \\u5faa\\u73af\\u6807\\u8bb0"]', 'C', '空间复杂度只统计算法额外开辟的辅助内存，原始输入不参与统计。', '["\\u539f\\u5730\\u7b97\\u6cd5\\u8f85\\u52a9\\u7a7a\\u95f4\\u4e3aO(1)"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (187, NULL, '数据结构', '绪论', '困难', '简答题', '简述时间复杂度与空间复杂度计算规则，并举例递归算法空间开销计算方式。', '[]', '时间复杂度：只保留最高阶，丢弃常数系数；空间复杂度仅统计额外辅助内存，输入不计。递归空间等于递归深度，每层局部变量叠加，深度n则空间O(n)。', '递归栈是高频失分点，很多考生忽略递归占用辅助空间。', '["\\u539f\\u5730\\u8fed\\u4ee3\\u7b97\\u6cd5\\u7a7a\\u95f4\\u590d\\u6742\\u5ea6\\u66f4\\u4f4e"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (188, NULL, '数据结构', '线性表', '简单', '选择题', '空线性表的长度为？', '["A. -1", "B. 0", "C. 1", "D. \\u65e0\\u56fa\\u5b9a\\u503c"]', 'B', '线性表无任何元素时长度等于0。', '["\\u6240\\u6709\\u5143\\u7d20\\u5b58\\u5728\\u552f\\u4e00\\u524d\\u9a71\\u540e\\u7ee7\\u5173\\u7cfb"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (189, NULL, '数据结构', '线性表', '中等', '选择题', '关于按位查找和按值查找说法正确的是？', '["A. \\u94fe\\u8868\\u652f\\u6301O(1)\\u6309\\u4f4d\\u67e5\\u627e", "B. \\u987a\\u5e8f\\u8868\\u6309\\u503c\\u67e5\\u627e\\u65e0\\u9700\\u904d\\u5386", "C. \\u987a\\u5e8f\\u8868\\u6309\\u4f4d\\u968f\\u673a\\u5b58\\u53d6O(1)", "D. \\u94fe\\u8868\\u6309\\u503c\\u67e5\\u627e\\u4e00\\u6b65\\u5b9a\\u4f4d"]', 'C', '顺序表内存连续，下标直接访问；链表只能顺序遍历查找。', '["GetElem\\u6309\\u4f4d\\uff0cLocateElem\\u6309\\u503c"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (190, NULL, '数据结构', '线性表', '中等', '简答题', '写出线性十大标准基础操作，并区分销毁与清空操作差异。', '[]', '操作：初始化、销毁、清空、判空、求长、按位查找、按值查找、插入、删除、遍历。清空仅清除元素保留内存；销毁释放整个线性表内存。', '二者内存释放范围不同，考试易混淆。', '["\\u9759\\u6001\\u6570\\u7ec4\\u7ebf\\u6027\\u8868\\u65e0\\u9500\\u6bc1\\u64cd\\u4f5c"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (191, NULL, '数据结构', '线性表', '中等', '填空题', '顺序表插入操作平均移动____个元素，删除平均移动____个元素。', '[]', 'n/2,(n-1)/2', '插入从尾部向前腾位置，删除后续元素向前覆盖。', '["\\u63d2\\u5165\\u4f4d\\u7f6e\\u8d8a\\u9760\\u524d\\u79fb\\u52a8\\u8d8a\\u591a"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (192, NULL, '数据结构', '线性表', '简单', '选择题', '静态分配顺序表的缺点是？', '["A. \\u652f\\u6301\\u968f\\u673a\\u5b58\\u53d6", "B. \\u5bb9\\u91cf\\u56fa\\u5b9a\\u65e0\\u6cd5\\u6269\\u5bb9", "C. \\u67e5\\u627e\\u901f\\u5ea6\\u5feb", "D. \\u5b58\\u50a8\\u5bc6\\u5ea61"]', 'B', '静态数组初始化固定MaxSize，数据满后不能新增元素；动态分配可重新开辟数组扩容。', '["\\u52a8\\u6001\\u5206\\u914d\\u4f9d\\u8d56\\u5806\\u5185\\u5b58"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (193, NULL, '数据结构', '线性表', '困难', '简答题', '描述顺序表插入完整执行步骤，并说明边界下标校验要点。', '[]', '1.判断插入下标是否合法；2.判断表长是否等于最大容量；3.从末尾到插入位置逐个后移元素；4.填入目标数据；5.表长length自增。下标范围0<=i<=length。', '下标越界、表满是两大报错场景。', '["\\u63d2\\u5165\\u5230\\u8868\\u5c3e\\u65e0\\u9700\\u79fb\\u52a8\\u5143\\u7d20"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (194, NULL, '数据结构', '线性表', '简单', '选择题', '单链表头结点作用是？', '["A. \\u5b58\\u50a8\\u9996\\u4e2a\\u4e1a\\u52a1\\u6570\\u636e", "B. \\u7edf\\u4e00\\u7a7a\\u8868\\u4e0e\\u975e\\u7a7a\\u8868\\u64cd\\u4f5c\\u903b\\u8f91", "C. \\u52a0\\u5feb\\u67e5\\u627e\\u901f\\u5ea6", "D. \\u56fa\\u5b9a\\u94fe\\u8868\\u5bb9\\u91cf"]', 'B', '头结点无有效数据，空表头指针不为NULL，统一所有操作代码。', '["\\u65e0\\u5934\\u94fe\\u8868\\u7a7a\\u8868\\u5224\\u65ad\\u9700\\u8981\\u7279\\u6b8aif\\u5206\\u652f"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (195, NULL, '数据结构', '线性表', '中等', '选择题', '头插法创建单链表的特点？', '["A. \\u94fe\\u8868\\u987a\\u5e8f\\u548c\\u8f93\\u5165\\u4e00\\u81f4", "B. \\u63d2\\u5165O(1)\\u65e0\\u9700\\u904d\\u5386\\u5c3e\\u90e8", "C. \\u5fc5\\u987b\\u7ef4\\u62a4\\u5c3e\\u6307\\u9488", "D. \\u5b58\\u5728\\u5bb9\\u91cf\\u4e0a\\u9650"]', 'B', '直接修改头指针，不用遍历链表尾部，生成逆序链表。', '["\\u5c3e\\u63d2\\u6cd5\\u751f\\u6210\\u548c\\u8f93\\u5165\\u76f8\\u540c\\u987a\\u5e8f"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (196, NULL, '数据结构', '线性表', '中等', '填空题', '双向链表节点包含____指针与____指针，插入时需要修改____条指针。', '[]', 'prior,next,4', '新节点、前驱节点后继、后继节点前驱四条指针修改。', '["\\u5355\\u94fe\\u8868\\u63d2\\u5165\\u4ec5\\u4fee\\u65392\\u6761\\u6307\\u9488"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (197, NULL, '数据结构', '线性表', '中等', '选择题', '循环单链表只保存尾指针的优势是？', '["A. \\u5feb\\u901f\\u83b7\\u53d6\\u8868\\u5934\\u4e0e\\u8868\\u5c3e", "B. \\u51cf\\u5c11\\u5185\\u5b58\\u5360\\u7528", "C. \\u63d0\\u5347\\u67e5\\u627e\\u901f\\u5ea6", "D. \\u65e0\\u9700\\u5934\\u7ed3\\u70b9"]', 'A', '尾指针next直接拿到头结点，头尾访问都是O(1)。', '["\\u666e\\u901a\\u5355\\u94fe\\u8868\\u53d6\\u5c3e\\u90e8\\u9700\\u8981\\u904d\\u5386\\u5168\\u8868"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (198, NULL, '数据结构', '线性表', '简单', '选择题', '静态链表使用什么替代指针？', '["A. \\u4e0b\\u6807\\u6e38\\u6807cur", "B. \\u5185\\u5b58\\u5730\\u5740", "C. \\u6570\\u7ec4\\u957f\\u5ea6", "D. \\u5934\\u6307\\u9488"]', 'A', '无指针语言用数组游标模拟链表，依靠备用链表管理空闲单元。', '["\\u9759\\u6001\\u94fe\\u8868\\u65e0\\u6cd5\\u968f\\u673a\\u4e0b\\u6807\\u5b58\\u53d6\\u5143\\u7d20"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (199, NULL, '数据结构', '线性表', '中等', '选择题', '频繁随机查询、元素数量固定优先选择？', '["A. \\u5355\\u94fe\\u8868", "B. \\u987a\\u5e8f\\u8868", "C. \\u53cc\\u5411\\u94fe\\u8868", "D. \\u5faa\\u73af\\u94fe\\u8868"]', 'B', '顺序表支持O(1)随机存取，适合查询场景。', '["\\u9891\\u7e41\\u4e2d\\u95f4\\u63d2\\u5165\\u5220\\u9664\\u9009\\u94fe\\u8868"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (200, NULL, '数据结构', '线性表', '中等', '填空题', '顺序表存储密度为____，链表因指针开销存储密度____。', '[]', '1,小于1', '顺序表全部空间存放数据；链表额外存储指针占用内存。', '["\\u5b58\\u50a8\\u5bc6\\u5ea6=\\u6709\\u6548\\u6570\\u636e\\u7a7a\\u95f4/\\u603b\\u5360\\u7528\\u7a7a\\u95f4"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (201, NULL, '数据结构', '线性表', '困难', '简答题', '从随机存取、插入删除效率、存储密度、容量限制四个维度完整对比顺序表与链表，并分别给出适用业务场景。', '[]', '1.随机存取：顺序O(1)，链表O(n)；2.中间增删：顺序平均O(n)，链表找到前驱O(1)；3.存储密度：顺序=1，链表<1；4.容量：顺序固定MaxSize，链表动态无上限。固定长度、大量查询用顺序；频繁增删、长度波动大用链表。', '考试高频综合简答题，需要分点作答。', '["\\u94fe\\u8868\\u5c3e\\u90e8\\u63d2\\u5165\\u7ef4\\u62a4\\u5c3e\\u6307\\u9488\\u53ef\\u4f18\\u5316\\u5230O(1)"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (202, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '栈的操作规则是？', '["A. FIFO\\u5148\\u8fdb\\u5148\\u51fa", "B. LIFO\\u540e\\u8fdb\\u5148\\u51fa", "C. \\u968f\\u673a\\u5b58\\u53d6", "D. \\u6309\\u503c\\u68c0\\u7d22"]', 'B', '栈仅栈顶可增删，后进元素先弹出。', '["\\u961f\\u5217\\u9075\\u5faaFIFO"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (203, NULL, '数据结构', '栈、队列和数组', '中等', '填空题', '顺序栈空栈top值为____，栈满top等于MaxSize-1；入栈先____top再存数据。', '[]', '-1,自增', 'top指向最后存入元素下标，入栈先移动指针，出栈先取值再自减。', '["\\u51fa\\u6808\\u987a\\u5e8f\\u548c\\u5165\\u6808\\u5b8c\\u5168\\u76f8\\u53cd"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (204, NULL, '数据结构', '栈、队列和数组', '中等', '选择题', '共享栈两个栈顶top0、top什么时候判定栈满？', '["A. top0 == 0", "B. top1 == MaxSize-1", "C. top0+1 == top1", "D. top0 > top1"]', 'C', '双向栈向中间靠拢，两指针相邻代表无空闲空间。', '["top0\\u4ece\\u5de6\\u5411\\u53f3\\u589e\\u957f\\uff0ctop1\\u4ece\\u53f3\\u5411\\u5de6"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (205, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '链栈采用头插法入栈，优点是？', '["A. \\u6709\\u5bb9\\u91cf\\u9650\\u5236", "B. \\u5165\\u6808O(1)", "C. \\u9700\\u8981\\u904d\\u5386\\u5c3e\\u90e8", "D. \\u5b58\\u50a8\\u5bc6\\u5ea6\\u9ad8"]', 'B', '头结点作为栈顶，无需遍历尾部，无栈满溢出问题。', '["\\u94fe\\u6808\\u4e0d\\u5b58\\u5728\\u6808\\u6ee1\\u72b6\\u6001"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (206, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '普通顺序队列的核心缺陷是？', '["A. \\u5b58\\u53d6\\u901f\\u5ea6\\u6162", "B. \\u5047\\u6ea2\\u51fa", "C. \\u65e0\\u6cd5\\u5b58\\u50a8\\u5927\\u91cf\\u6570\\u636e", "D. \\u67e5\\u627e\\u56f0\\u96be"]', 'B', '尾部填满但头部存在空闲空间，无法继续入队称为假溢出。', '["\\u5faa\\u73af\\u961f\\u5217\\u89e3\\u51b3\\u5047\\u6ea2\\u51fa\\u95ee\\u9898"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0);
INSERT INTO `question` (`id`, `session_id`, `subject`, `knowledge_point`, `difficulty`, `question_type`, `question_text`, `options_json`, `standard_answer`, `explanation`, `hints_json`, `recommend_reason`, `source`, `create_time`, `variant_type`, `sub_questions_json`, `is_deleted`) VALUES
  (207, NULL, '数据结构', '栈、队列和数组', '中等', '填空题', '牺牲一个空位的循环队列，队满判定公式____。', '[]', '(rear+1)%MaxSize == front', '取模实现环形存储，预留一格区分空/满状态。', '["rear\\u662f\\u4e0b\\u4e00\\u4e2a\\u5165\\u961f\\u4f4d\\u7f6e"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (208, NULL, '数据结构', '栈、队列和数组', '中等', '选择题', '带size标记的循环队列优势是？', '["A. \\u65e0\\u9700\\u727a\\u7272\\u7a7a\\u4f4d", "B. \\u8ba1\\u7b97\\u66f4\\u5feb", "C. \\u65e0\\u9700\\u53d6\\u6a21", "D. \\u8282\\u7701\\u5185\\u5b58"]', 'A', 'size记录当前元素数量，size=0空，size=MaxSize满，不需要预留空闲单元。', '["\\u4e24\\u79cd\\u5faa\\u73af\\u961f\\u5217\\u5b9e\\u73b0\\u4e8c\\u9009\\u4e00\\u8003\\u5bdf"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (209, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '链队列同时保存front、rear双指针目的？', '["A. \\u968f\\u673a\\u67e5\\u627e", "B. \\u5c3e\\u90e8\\u5165\\u961fO(1)", "C. \\u8282\\u7701\\u8282\\u70b9", "D. \\u533a\\u5206\\u7a7a\\u6ee1"]', 'B', '尾指针直接访问队尾，不用遍历全表插入元素。', '["\\u7a7a\\u961f\\u5217front==rear==NULL"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (210, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '括号匹配校验使用的数据结构是？', '["A. \\u961f\\u5217", "B. \\u6808", "C. \\u987a\\u5e8f\\u8868", "D. \\u94fe\\u8868"]', 'B', '左括号入栈，右括号弹出栈顶匹配，栈天然嵌套匹配。', '["\\u5168\\u90e8\\u904d\\u5386\\u540e\\u6808\\u5fc5\\u987b\\u4e3a\\u7a7a\\u624d\\u7b97\\u5408\\u6cd5"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (211, NULL, '数据结构', '栈、队列和数组', '中等', '选择题', '中缀表达式转后缀逆波兰依靠？', '["A. \\u961f\\u5217", "B. \\u8fd0\\u7b97\\u7b26\\u6808", "C. \\u6570\\u7ec4", "D. \\u53cc\\u5411\\u94fe\\u8868"]', 'B', '运算符入栈比较优先级，高优先级先弹出输出。', '["\\u62ec\\u53f7\\u63d0\\u5347\\u5185\\u90e8\\u8fd0\\u7b97\\u7b26\\u4f18\\u5148\\u7ea7"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (212, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', '树、图层序遍历使用？', '["A. \\u6808", "B. \\u961f\\u5217", "C. \\u9759\\u6001\\u94fe\\u8868", "D. \\u6563\\u5217\\u8868"]', 'B', 'BFS广度优先逐层入队，保证层次顺序输出。', '["\\u6df1\\u5ea6\\u4f18\\u5148DFS\\u4f7f\\u7528\\u6808/\\u9012\\u5f52"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (213, NULL, '数据结构', '栈、队列和数组', '简单', '选择题', 'C语言二维数组默认存储顺序是？', '["A. \\u884c\\u4f18\\u5148", "B. \\u5217\\u4f18\\u5148", "C. \\u968f\\u673a", "D. \\u6309\\u503c\\u6392\\u5e8f"]', 'A', '先完整存储一行所有元素，再存储下一行。', '["Fortran\\u8bed\\u8a00\\u4e3a\\u5217\\u4f18\\u5148"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (214, NULL, '数据结构', '栈、队列和数组', '中等', '填空题', '对称矩阵仅存储____三角区域，可节省一半存储空间。', '[]', '下', 'a[i][j] = a[j][i]，仅保存下三角，上三角通过映射计算。', '["\\u9700\\u8981\\u638c\\u63e1\\u4e00\\u7ef4\\u6570\\u7ec4\\u4e0b\\u6807\\u6362\\u7b97\\u516c\\u5f0f"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (215, NULL, '数据结构', '栈、队列和数组', '中等', '选择题', '稀疏矩阵采用哪种结构压缩存储？', '["A. \\u4e8c\\u7ef4\\u6570\\u7ec4", "B. \\u4e09\\u5143\\u7ec4\\u987a\\u5e8f\\u8868", "C. \\u5bf9\\u79f0\\u77e9\\u9635", "D. \\u5faa\\u73af\\u6570\\u7ec4"]', 'B', '存储(行,列,值)三元组，跳过大量零元素，节省空间。', '["\\u4e09\\u5143\\u7ec4\\u65e0\\u6cd5O(1)\\u968f\\u673a\\u8bbf\\u95ee\\u5143\\u7d20"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (216, NULL, '数据结构', '串', '简单', '选择题', '空串与空白串区别正确的是？', '["A. \\u4e8c\\u8005\\u5b8c\\u5168\\u76f8\\u540c", "B. \\u7a7a\\u4e32\\u957f\\u5ea60\\uff0c\\u7a7a\\u767d\\u4e32\\u542b\\u7a7a\\u683c", "C. \\u7a7a\\u767d\\u4e32\\u957f\\u5ea60", "D. \\u7a7a\\u4e32\\u5305\\u542b\\u7a7a\\u683c"]', 'B', '空串无任何字符；空白串仅由空格字符构成，长度大于0。', '["\\u8003\\u8bd5\\u9ad8\\u9891\\u6613\\u6df7\\u6dc6\\u6982\\u5ff5"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (217, NULL, '数据结构', '串', '中等', '选择题', '子串和子序列描述正确的是？', '["A. \\u5b50\\u5e8f\\u5217\\u5fc5\\u987b\\u8fde\\u7eed", "B. \\u5b50\\u4e32\\u5fc5\\u987b\\u8fde\\u7eed\\u5b57\\u7b26\\u7247\\u6bb5", "C. \\u4e8c\\u8005\\u65e0\\u533a\\u522b", "D. \\u5b50\\u4e32\\u53ef\\u4ee5\\u4e0d\\u8fde\\u7eed"]', 'B', '子串：连续字符；子序列：字符可间断，相对顺序不变。', '["\\u622a\\u53d6SubString\\u64cd\\u4f5c\\u4ec5\\u83b7\\u53d6\\u5b50\\u4e32"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (218, NULL, '数据结构', '串', '中等', '选择题', 'BF暴力匹配最坏时间复杂度是？', '["A. O(n)", "B. O(n+m)", "C. O(n*m)", "D. O(logn)"]', 'C', '双重循环，主串、模式串指针全部回退，最坏乘积级复杂度。', '["n\\u4e3b\\u4e32\\u957f\\u5ea6\\uff0cm\\u6a21\\u5f0f\\u4e32\\u957f\\u5ea6"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (219, NULL, '数据结构', '串', '中等', '选择题', 'KMP算法主串指针i是否回退？', '["A. \\u5339\\u914d\\u5931\\u8d25i\\u81ea\\u51cf", "B. i\\u4fdd\\u6301\\u4e0d\\u52a8", "C. i\\u5f52\\u96f6", "D. i=m"]', 'B', '仅调整模式串j=next[j]，主串i不回退，线性复杂度。', '["next\\u6570\\u7ec4\\u5b58\\u6700\\u957f\\u76f8\\u7b49\\u524d\\u540e\\u7f00"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (220, NULL, '数据结构', '串', '困难', '简答题', '简述nextval数组优化原理，对比next数组解决的问题。', '[]', 'next数组存在无效跳转：当前字符与next位置字符相同时，跳转无意义；nextval递归赋值nextval[j]=nextval[next[j]]，消除重复无效匹配，减少循环次数。', 'KMP优化考点，大题常考。', '["\\u76f8\\u540c\\u5b57\\u7b26\\u76f4\\u63a5\\u7ee7\\u627f\\u524d\\u9a71\\u4f18\\u5316\\u503c"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (221, NULL, '数据结构', '树与二叉树', '简单', '选择题', '空树的特点是？', '["A. \\u5b58\\u5728\\u6839\\u8282\\u70b9", "B. \\u8282\\u70b9\\u96c6\\u5408\\u4e3a\\u7a7a", "C. \\u4ec5\\u6709\\u53f6\\u5b50", "D. \\u5ea6\\u4e3a1"]', 'B', 'n=0为空树，不存在任何节点，无根节点。', '["\\u5b50\\u6811\\u4e4b\\u95f4\\u4e92\\u4e0d\\u76f8\\u4ea4"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (222, NULL, '数据结构', '树与二叉树', '中等', '填空题', '树的握手定理：整棵树总度数 = ____。', '[]', '节点数-1', '每条边对应一个节点的度，根无父边，总边数=总度数=节点减一。', '["\\u53f6\\u5b50\\u8282\\u70b9\\u5ea6\\u7b49\\u4e8e0"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (223, NULL, '数据结构', '树与二叉树', '简单', '选择题', '二叉树和普通树最大区别？', '["A. \\u8282\\u70b9\\u66f4\\u5c11", "B. \\u533a\\u5206\\u5de6\\u53f3\\u5b69\\u5b50", "C. \\u53ea\\u80fd\\u4e24\\u5c42", "D. \\u65e0\\u53f6\\u5b50"]', 'B', '二叉树是有序树，左、右子树不能互换。', '["\\u4e94\\u79cd\\u57fa\\u7840\\u5f62\\u6001\\uff1a\\u7a7a\\u3001\\u5355\\u6839\\u3001\\u4ec5\\u5de6\\u3001\\u4ec5\\u53f3\\u3001\\u53cc\\u5168"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (224, NULL, '数据结构', '树与二叉树', '中等', '填空题', '二叉树叶子节点n0，度为2节点n2，关系式____。', '[]', 'n0 = n2 + 1', '408数据结构必考核心公式，依靠握手定理推导。', '["\\u4ec5\\u4e8c\\u53c9\\u6811\\u6ee1\\u8db3\\u8be5\\u7b49\\u5f0f\\uff0c\\u666e\\u901a\\u6811\\u4e0d\\u6210\\u7acb"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (225, NULL, '数据结构', '树与二叉树', '中等', '选择题', '完全二叉树叶子节点分布在？', '["A. \\u4ec5\\u7b2c\\u4e00\\u5c42", "B. \\u6700\\u4e0b\\u5c42\\u3001\\u6b21\\u4e0b\\u5c42", "C. \\u5168\\u90e8\\u5947\\u6570\\u5c42", "D. \\u6839\\u8282\\u70b9\\u4e0b\\u5c42"]', 'B', '完全二叉树从上到下、从左连续填充，无空缺，叶子只出现在最后两层。', '["\\u6ee1\\u4e8c\\u53c9\\u6811\\u6bcf\\u4e00\\u5c42\\u5168\\u90e8\\u586b\\u6ee1"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (226, NULL, '数据结构', '树与二叉树', '简单', '选择题', '中序遍历访问顺序？', '["A. \\u6839\\u5de6\\u53f3", "B. \\u5de6\\u6839\\u53f3", "C. \\u5de6\\u53f3\\u6839", "D. \\u9010\\u5c42"]', 'B', '前序根最先，中序根中间，后序根最后。', '"\\u4e8c\\u53c9\\u641c\\u7d22\\u6811\\u4e2d\\u5e8f\\u5347\\u5e8f"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (227, NULL, '数据结构', '树与二叉树', '中等', '选择题', '层序遍历依靠的数据结构？', '["A. \\u6808", "B. \\u961f\\u5217", "C. \\u987a\\u5e8f\\u8868", "D. \\u9759\\u6001\\u94fe\\u8868"]', 'B', '队列先进先出，保证从上到下、从左到右分层输出。', '"\\u9012\\u5f52\\u524d\\u4e2d\\u540e\\u904d\\u5386\\u9690\\u5f0f\\u4f7f\\u7528\\u51fd\\u6570\\u6808"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (228, NULL, '数据结构', '树与二叉树', '中等', '选择题', 'ltag=1代表？', '["A. \\u5de6\\u5b69\\u5b50\\u6307\\u9488", "B. \\u524d\\u9a71\\u7ebf\\u7d22", "C. \\u53f3\\u5b69\\u5b50", "D. \\u540e\\u7ee7\\u7ebf\\u7d22"]', 'B', 'ltag=0存左孩子，ltag=1存遍历前驱；rtag=1存后继线索。', '["\\u5229\\u7528\\u53f6\\u5b50\\u7a7a\\u6307\\u9488\\u8282\\u7701\\u5185\\u5b58"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (229, NULL, '数据结构', '树与二叉树', '中等', '选择题', '孩子兄弟表示法规则？', '["A. \\u5de6\\u5144\\u5f1f\\u53f3\\u5b69\\u5b50", "B. \\u5de6\\u5b69\\u5b50\\u53f3\\u5144\\u5f1f", "C. \\u5de6\\u53f3\\u5747\\u5b69\\u5b50", "D. \\u5de6\\u53f3\\u5747\\u5144\\u5f1f"]', 'B', '左指针存第一个子节点，右指针存同层右侧兄弟。', '["\\u68ee\\u6797\\u8f6c\\u4e8c\\u53c9\\u6811\\uff1a\\u5404\\u6811\\u6839\\u4f5c\\u4e3a\\u53f3\\u94fe"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (230, NULL, '数据结构', '树与二叉树', '中等', '选择题', '哈夫曼树构造规则是每次选取？', '["A. \\u6743\\u6700\\u5927\\u4e24\\u8282\\u70b9", "B. \\u6743\\u6700\\u5c0f\\u4e24\\u8282\\u70b9", "C. \\u6df1\\u5ea6\\u6700\\u6df1", "D. \\u53f6\\u5b50\\u6700\\u591a"]', 'B', '合并两个最小权值节点生成新父节点，重复至单棵树。', '["\\u54c8\\u592b\\u66fc\\u6811\\u4e0d\\u5b58\\u5728\\u5ea6\\u4e3a2\\u7684\\u53f6\\u5b50\\u8282\\u70b9"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (231, NULL, '数据结构', '树与二叉树', '中等', '选择题', '并查集Find操作优化方式？', '["A. \\u6309\\u79e9\\u5408\\u5e76", "B. \\u8def\\u5f84\\u538b\\u7f29", "C. \\u5c42\\u6b21\\u904d\\u5386", "D. \\u54c8\\u592b\\u66fc\\u5408\\u5e76"]', 'B', '路径压缩将节点直接指向根，大幅缩短查找路径；Union使用按秩合并。', '["Find\\u67e5\\u8be2\\u8fde\\u901a\\u5206\\u91cf\\u6839\\u8282\\u70b9"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (232, NULL, '数据结构', '图', '简单', '选择题', '无向边(u,v)与有向边<u,v>区别是？', '["A. \\u65e0\\u5411\\u53cc\\u5411\\u7b49\\u4ef7", "B. \\u65e0\\u5411\\u6709\\u65b9\\u5411", "C. \\u6709\\u5411\\u65e0\\u53cc\\u5411", "D. \\u4e8c\\u8005\\u65e0\\u533a\\u522b"]', 'A', '无向边双向可达，有向边仅单向通行。', '["\\u63e1\\u624b\\u5b9a\\u7406\\u65e0\\u5411\\u603b\\u5ea6\\u6570=2*\\u8fb9\\u6570"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (233, NULL, '数据结构', '图', '中等', '选择题', '稠密图优先选择存储结构？', '["A. \\u90bb\\u63a5\\u8868", "B. \\u90bb\\u63a5\\u77e9\\u9635", "C. \\u4e09\\u5143\\u7ec4", "D. \\u4e8c\\u53c9\\u6811"]', 'B', '邻接矩阵查询两点连通O(1)，稠密图空间浪费小。', '["\\u7a00\\u758f\\u56fe\\u9009\\u90bb\\u63a5\\u8868\\u8282\\u7701\\u7a7a\\u95f4"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (234, NULL, '数据结构', '图', '简单', '选择题', '求解无权图最短路径使用？', '["A. DFS", "B. BFS", "C. \\u54c8\\u592b\\u66fc", "D. \\u5e76\\u67e5\\u96c6"]', 'B', '广度优先逐层扩散，层数等于最短边数。', '["DFS\\u9002\\u5408\\u73af\\u8def\\u68c0\\u6d4b"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (235, NULL, '数据结构', '图', '中等', '选择题', '稀疏无向连通图最小生成树算法？', '["A. Prim", "B. Kruskal", "C. Dijkstra", "D. Floyd"]', 'B', 'Kruskal依靠并查集处理稀疏图；Prim适合稠密图。', '["\\u6700\\u5c0f\\u751f\\u6210\\u6811\\u65e0\\u73af\\u3001\\u603b\\u6743\\u6700\\u5c0f"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (236, NULL, '数据结构', '图', '中等', '选择题', 'Dijkstra算法不能处理？', '["A. \\u65e0\\u5411\\u56fe", "B. \\u8d1f\\u6743\\u8fb9", "C. \\u7a20\\u5bc6\\u56fe", "D. \\u8fde\\u901a\\u56fe"]', 'B', '负权会导致最短路径反复更新，算法失效。', '"\\u591a\\u6e90\\u6700\\u77ed\\u8def\\u5f84\\u7528Floyd"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (237, NULL, '数据结构', '图', '中等', '选择题', '有环AOV网是否存在合法拓扑序列？', '["A. \\u5b58\\u5728", "B. \\u4e0d\\u5b58\\u5728", "C. \\u73af\\u5916\\u5b58\\u5728", "D. \\u90e8\\u5206\\u5b58\\u5728"]', 'B', '环路节点入度永远无法清零，无法输出拓扑序列。', '["\\u62d3\\u6251\\u6392\\u5e8f\\u6bcf\\u6b21\\u8f93\\u51fa\\u5165\\u5ea60\\u9876\\u70b9"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (238, NULL, '数据结构', '图', '困难', '简答题', '区分AOV网与AOE网，分别说明核心用途与关键概念。', '[]', 'AOV：顶点代表活动，边代表先后约束，用于拓扑排序判断依赖环路；AOE：边代表任务，顶点代表事件，ve/vl求关键路径，计算最短总工期。', '二者极易混淆，是图论大题高频考点。', '["AOE\\u4e2dee==el\\u4e3a\\u5173\\u952e\\u6d3b\\u52a8"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (239, NULL, '数据结构', '查找', '简单', '选择题', '运行中无法增删的表称为？', '["A. \\u52a8\\u6001\\u67e5\\u627e\\u8868", "B. \\u9759\\u6001\\u67e5\\u627e\\u8868", "C. \\u6563\\u5217\\u8868", "D. \\u6811\\u8868"]', 'B', '静态查找：仅查询；动态支持插入删除。', '["ASL\\u5e73\\u5747\\u67e5\\u627e\\u957f\\u5ea6\\u8861\\u91cf\\u67e5\\u627e\\u6548\\u7387"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (240, NULL, '数据结构', '查找', '中等', '选择题', '二分查找不能用于哪种存储？', '["A. \\u6709\\u5e8f\\u987a\\u5e8f\\u8868", "B. \\u6709\\u5e8f\\u6570\\u7ec4", "C. \\u5355\\u94fe\\u8868", "D. \\u9759\\u6001\\u6570\\u7ec4"]', 'C', '二分依赖随机存取下标，链表只能顺序遍历。', '["mid=(low+high)//2"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (241, NULL, '数据结构', '查找', '中等', '选择题', '二叉搜索树中序遍历结果是？', '["A. \\u65e0\\u5e8f", "B. \\u5347\\u5e8f", "C. \\u964d\\u5e8f", "D. \\u968f\\u673a"]', 'B', '左子<根<右子，中序遍历自然有序。', '"AVL\\u5e73\\u8861\\u56e0\\u5b50\\u7edd\\u5bf9\\u503c\\u22641"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (242, NULL, '数据结构', '查找', '中等', '选择题', '装填因子α越大，哈希冲突？', '["A. \\u8d8a\\u5c11", "B. \\u8d8a\\u591a", "C. \\u4e0d\\u53d8", "D. \\u65e0\\u5173\\u8054"]', 'B', 'α=记录数/表长，数据越满冲突概率越高。', '["\\u94fe\\u5730\\u5740\\u6cd5\\u3001\\u5f00\\u653e\\u5bfb\\u5740\\u89e3\\u51b3\\u51b2\\u7a81"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (243, NULL, '数据结构', '排序', '简单', '选择题', '稳定排序定义？', '["A. \\u76f8\\u7b49\\u5143\\u7d20\\u76f8\\u5bf9\\u4f4d\\u7f6e\\u4e0d\\u53d8", "B. \\u901f\\u5ea6\\u6700\\u5feb", "C. \\u65e0\\u989d\\u5916\\u7a7a\\u95f4", "D. \\u4ec5\\u5347\\u5e8f"]', 'A', '不稳定排序会交换等值元素前后顺序。', '["\\u5185\\u90e8\\u6392\\u5e8f\\u5168\\u90e8\\u6570\\u636e\\u52a0\\u8f7d\\u5185\\u5b58"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (244, NULL, '数据结构', '排序', '中等', '选择题', '平均O(nlogn)且稳定的内部排序？', '["A. \\u5feb\\u901f\\u6392\\u5e8f", "B. \\u5f52\\u5e76\\u6392\\u5e8f", "C. \\u5806\\u6392\\u5e8f", "D. \\u5e0c\\u5c14"]', 'B', '归并排序等值元素不交换；快排、堆、希尔均不稳定。', '["\\u7b80\\u5355\\u63d2\\u5165\\u3001\\u5192\\u6ce1\\u7a33\\u5b9aO(n\\u00b2)"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (245, NULL, '数据结构', '排序', '简单', '选择题', '多路归并优化选取最小值使用？', '["A. \\u4e8c\\u53c9\\u641c\\u7d22\\u6811", "B. \\u8d25\\u8005\\u6811", "C. \\u6808", "D. \\u961f\\u5217"]', 'B', '败者树减少多路比较次数，降低磁盘IO。', '["\\u6d77\\u91cf\\u6570\\u636e\\u5206\\u5757\\u751f\\u6210\\u5f52\\u5e76\\u6bb5"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (246, NULL, '计算机组成原理', '计算机系统概述', '简单', '选择题', '四代计算机核心硬件依次是？', '["A. \\u7535\\u5b50\\u7ba1\\u3001\\u6676\\u4f53\\u7ba1\\u3001\\u4e2d\\u5c0f\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def\\u3001\\u8d85\\u5927\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def", "B. \\u6676\\u4f53\\u7ba1\\u3001\\u7535\\u5b50\\u7ba1\\u3001\\u96c6\\u6210\\u7535\\u8def\\u3001\\u8d85\\u5927\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def", "C. \\u7535\\u5b50\\u7ba1\\u3001\\u96c6\\u6210\\u7535\\u8def\\u3001\\u6676\\u4f53\\u7ba1\\u3001\\u8d85\\u5927\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def", "D. \\u6676\\u4f53\\u7ba1\\u3001\\u4e2d\\u5c0f\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def\\u3001\\u7535\\u5b50\\u7ba1\\u3001\\u8d85\\u5927\\u89c4\\u6a21\\u96c6\\u6210\\u7535\\u8def"]', 'B', '第一代电子管，第二代晶体管，第三代中小规模集成电路，第四代超大规模集成电路。', '["\\u8f6f\\u4ef6\\u4f34\\u968f\\u786c\\u4ef6\\u540c\\u6b65\\u8fed\\u4ee3\\u53d1\\u5c55"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (247, NULL, '计算机组成原理', '计算机系统概述', '简单', '选择题', '手工操作阶段计算机不存在以下哪项机制？', '["A. \\u7eb8\\u5e26\\u8f93\\u5165\\u8bbe\\u5907", "B. \\u4e2d\\u65ad\\u673a\\u5236", "C. \\u8fd0\\u7b97\\u5668", "D. \\u5b58\\u50a8\\u4ecb\\u8d28"]', 'B', '手工阶段无中断、调度程序，CPU与外设串行等待，资源利用率极低。', '"\\u5355\\u9053\\u6279\\u5904\\u7406\\u624d\\u6709\\u76d1\\u7763\\u8c03\\u5ea6\\u7a0b\\u5e8f"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (248, NULL, '计算机组成原理', '计算机系统概述', '中等', '简答题', '分别简述手工阶段、单道批处理、多道批处理系统的优缺点。', '[]', '1.手工阶段：无需软件调度，但CPU长时间等待外设，资源利用率极低；2.单道批：自动加载作业，消除人工开销，但同一时刻仅一道程序，IO时CPU空闲；3.多道批：内存驻留多道程序，IO阻塞时切换进程，大幅提升CPU、外设利用率，但无交互功能。', '多道批处理核心是进程并发调度。', '["\\u5206\\u65f6\\u7cfb\\u7edf\\u624d\\u652f\\u6301\\u4eba\\u673a\\u4ea4\\u4e92"]', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (249, NULL, '计算机组成原理', '计算机系统概述', '简单', '选择题', '计算机硬件五大核心部件不包含？', '["A. \\u8fd0\\u7b97\\u5668", "B. \\u63a7\\u5236\\u5668", "C. \\u64cd\\u4f5c\\u7cfb\\u7edf", "D. \\u5b58\\u50a8\\u5668"]', 'C', '五大硬件：运算器、控制器、存储器、输入设备、输出设备；操作系统属于系统软件。', '"\\u8fd0\\u7b97\\u5668+\\u63a7\\u5236\\u5668\\u5408\\u5e76\\u4e3aCPU"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (250, NULL, '计算机组成原理', '计算机系统概述', '简单', '选择题', '主机的标准组成范围是？', '["A. CPU+\\u5168\\u90e8\\u5916\\u8bbe", "B. CPU+\\u4e3b\\u5b58", "C. \\u8fd0\\u7b97\\u5668+\\u5916\\u8bbe", "D. \\u5b58\\u50a8\\u5668+\\u8f93\\u5165\\u8bbe\\u5907"]', 'B', '主机=CPU（运算器+控制器）+主存；键盘、显示器等属于外设。', '"\\u5916\\u8bbe\\u7edf\\u4e00\\u79f0\\u4e3a\\u8f93\\u5165\\u8f93\\u51fa\\u8bbe\\u5907"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (251, NULL, '计算机组成原理', '计算机系统概述', '中等', '填空题', '软件分层自上而下：机器语言、汇编语言、____、高级语言、应用程序。', '[]', '操作系统', '操作系统隔离底层硬件，为上层高级语言提供统一调用接口。', '"\\u4e0a\\u5c42\\u8f6f\\u4ef6\\u5c4f\\u853d\\u5e95\\u5c42\\u786c\\u4ef6\\u7ec6\\u8282"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (252, NULL, '计算机组成原理', '计算机系统概述', '中等', '简答题', '简述软硬件逻辑等价性，并举两个典型实例。', '[]', '软硬件逻辑等价性指同一功能既可用硬件电路直接实现，也可依靠软件程序模拟。实例1：乘法运算，硬件乘法器快速实现，软件可循环加法模拟；实例2：浮点数运算，带浮点单元CPU硬件加速，无浮点单元依靠软件库函数计算。', '硬件速度快成本高，软件灵活但执行速度慢。', '"\\u786c\\u4ef6\\u529f\\u80fd\\u56fa\\u5316\\u65e0\\u6cd5\\u4fee\\u6539\\uff0c\\u8f6f\\u4ef6\\u53ef\\u8fed\\u4ee3\\u66f4\\u65b0"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (253, NULL, '计算机组成原理', '计算机系统概述', '简单', '选择题', '以下不属于运算性能指标的是？', '["A. \\u4e3b\\u9891", "B. CPI", "C. \\u786c\\u76d8\\u5bb9\\u91cf", "D. MIPS"]', 'C', '硬盘属于存储容量指标，主频、CPI、FLOPS、MIPS均衡量运算速度。', '"CPI\\u4ee3\\u8868\\u6bcf\\u6761\\u6307\\u4ee4\\u5e73\\u5747\\u65f6\\u949f\\u5468\\u671f\\u6570"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (254, NULL, '计算机组成原理', '计算机系统概述', '中等', '选择题', '关于存储单位换算说法正确的是？', '["A. 1KB=1000B\\u4e8c\\u8fdb\\u5236\\u6807\\u51c6", "B. 1Byte=1bit", "C. \\u4e8c\\u8fdb\\u52361GB=2^30B", "D. \\u5382\\u5546\\u5b58\\u50a8\\u4f7f\\u75282\\u8fdb\\u5236\\u6362\\u7b97"]', 'C', '计算机二进制标准1KB=2^10B、1GB=2^30B；硬件厂商使用十进制1KB=1000B；1字节=8位。', '"bit\\u662f\\u4e8c\\u8fdb\\u5236\\u4f4d\\uff0cByte\\u662f\\u5b57\\u8282"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (255, NULL, '计算机组成原理', '计算机系统概述', '中等', '填空题', '衡量浮点运算能力的指标是____，衡量定点整数运算速度的是____。', '[]', 'FLOPS,MIPS', 'FLOPS每秒浮点运算次数，MIPS每秒百万条定点指令。', '"CPI\\u8d8a\\u4f4e\\uff0c\\u5355\\u6761\\u6307\\u4ee4\\u8017\\u65f6\\u8d8a\\u5c11"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (256, NULL, '计算机组成原理', '数据的表示和运算', '简单', '选择题', '十进制整数转换为R进制使用哪种运算？', '["A. \\u4e58\\u57fa\\u53d6\\u6574", "B. \\u9664\\u57fa\\u53d6\\u4f59", "C. \\u6309\\u6743\\u5c55\\u5f00", "D. \\u5206\\u7ec4\\u6620\\u5c04"]', 'B', '整数除基取余，小数乘基取整；任意进制转十进制采用按权展开求和。', '"\\u4e8c/\\u516b/\\u5341\\u516d\\u8fdb\\u5236\\u53ef4\\u4f4d\\u30013\\u4f4d\\u5206\\u7ec4\\u5feb\\u901f\\u8f6c\\u6362"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (257, NULL, '计算机组成原理', '数据的表示和运算', '中等', '选择题', 'n位二进制补码可表示的最小值为？', '["A. -2^n", "B. -2^{n-1}", "C. -2^{n-1}+1", "D. -2^n+1"]', 'B', '原码、反码范围：-(2^{n-1}-1) ~ 2^{n-1}-1；补码多出一个负数极值-2^{n-1}，消除正负0歧义。', '"\\u8ba1\\u7b97\\u673a\\u5185\\u90e8\\u5168\\u90e8\\u4f7f\\u7528\\u8865\\u7801\\u8fd0\\u7b97"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (258, NULL, '计算机组成原理', '数据的表示和运算', '中等', '选择题', '以下哪种编码用作浮点数阶码比较？', '["A. \\u539f\\u7801", "B. \\u53cd\\u7801", "C. \\u8865\\u7801", "D. \\u79fb\\u7801"]', 'D', '移码为补码偏移常量，大小对比无需判断符号位，专门用于阶码存储比较。', '"\\u79fb\\u7801\\u4e0e\\u8865\\u7801\\u4ec5\\u6700\\u9ad8\\u7b26\\u53f7\\u4f4d\\u76f8\\u53cd"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (259, NULL, '计算机组成原理', '数据的表示和运算', '困难', '简答题', '对比原码、反码、补码、移码的优缺点与适用场景。', '[]', '1.原码：直观可读，加减需区分符号，存在+0/-0；2.反码：负数逐位取反，仍存在正负0；3.补码：统一一套加减电路，无正负0，CPU定点运算标准；4.移码：补码偏移，阶码大小快速对比，仅用于浮点阶码。', '所有定点算术运算硬件层面均基于补码实现。', '"\\u79fb\\u7801\\u504f\\u79fb\\u503c\\u4e00\\u822c\\u4e3a2^{n-1}"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (260, NULL, '计算机组成原理', '数据的表示和运算', '简单', '选择题', 'CPU算术逻辑运算核心部件是？', '["A. MAR", "B. ALU", "C. PC", "D. IR"]', 'B', 'ALU由全加器阵列构成，负责加减、与或非等所有算术逻辑运算。', '"MAR\\u5b58\\u653e\\u5185\\u5b58\\u8bbf\\u95ee\\u5730\\u5740"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (261, NULL, '计算机组成原理', '数据的表示和运算', '中等', '选择题', '串行进位加法器缺点是？', '["A. \\u7535\\u8def\\u7b80\\u5355", "B. \\u8fdb\\u4f4d\\u9010\\u7ea7\\u4f20\\u9012\\u5ef6\\u8fdf\\u5927", "C. \\u5360\\u7528\\u95e8\\u7535\\u8def\\u5c11", "D. \\u6613\\u5b9e\\u73b0"]', 'B', '串行进位每一位必须等待低位进位，运算延迟高；先行进位并行计算进位，速度更快。', '"\\u73b0\\u4ee3CPU ALU\\u5168\\u90e8\\u91c7\\u7528\\u5148\\u884c\\u8fdb\\u4f4d"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (262, NULL, '计算机组成原理', '数据的表示和运算', '中等', '填空题', '负数补码算术右移高位补____；负数原码算术右移高位补____。', '[]', '1,0', '补码负数符号位不变，数值位右移填充1；原码符号不变，数值位填充0；逻辑移位统一补0。', '"\\u903b\\u8f91\\u79fb\\u4f4d\\u4e0d\\u533a\\u5206\\u6b63\\u8d1f\\u7b26\\u53f7"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (263, NULL, '计算机组成原理', '数据的表示和运算', '简单', '选择题', 'IEEE754单精度32位浮点数分段正确的是？', '["A. 1\\u7b26\\u53f7\\u4f4d\\uff0c8\\u9636\\u7801\\uff0c23\\u5c3e\\u6570", "B. 1\\u7b26\\u53f7\\u4f4d\\uff0c11\\u9636\\uff0c52\\u5c3e\\u6570", "C. 8\\u7b26\\u53f7\\uff0c1\\u9636\\uff0c23\\u5c3e\\u6570", "D. 1\\u7b26\\u53f7\\uff0c5\\u9636\\uff0c10\\u5c3e\\u6570"]', 'A', 'float单精度S=1,E=8,M=23；double双精度S=1,E=11,M=52。', '"\\u5c3e\\u6570\\u9ed8\\u8ba4\\u9690\\u85cf\\u6574\\u65701\\uff0c\\u4e0d\\u5360\\u7528\\u5b58\\u50a8\\u4f4d"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (264, NULL, '计算机组成原理', '数据的表示和运算', '中等', '选择题', '浮点加减运算第一步操作是？', '["A. \\u5c3e\\u6570\\u52a0\\u51cf", "B. \\u89c4\\u683c\\u5316", "C. \\u5bf9\\u9636", "D. \\u820d\\u5165"]', 'C', '浮点完整流程：对阶→尾数加减→规格化→舍入→溢出判断；对阶统一阶码，小阶向大阶看齐。', '"\\u5bf9\\u9636\\u4ec5\\u5c3e\\u6570\\u53f3\\u79fb\\uff0c\\u7981\\u6b62\\u5de6\\u79fb"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (265, NULL, '计算机组成原理', '数据的表示和运算', '中等', '填空题', 'float转double精度____，double转float会发生____丢失。', '[]', '无损,尾数', '双精度阶码、尾数位数更长，单精度转双精度无精度损耗；反向转换截断尾数产生精度损失。', '"\\u9636\\u7801\\u504f\\u79fb\\u91cf\\u5355\\u7cbe\\u5ea6127\\uff0c\\u53cc\\u7cbe\\u5ea61023"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (266, NULL, '计算机组成原理', '存储系统', '简单', '选择题', '断电完全丢失数据的存储器是？', '["A. Flash\\u95ea\\u5b58", "B. SRAM/DRAM", "C. \\u56fa\\u6001\\u786c\\u76d8", "D. \\u673a\\u68b0\\u78c1\\u76d8"]', 'B', 'RAM依靠晶体管/电容存储电荷，断电电荷消失；ROM、Flash、磁盘属于非易失存储。', '"SRAM\\u7528\\u4e8eCache\\uff0cDRAM\\u505a\\u4e3b\\u5b58"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (267, NULL, '计算机组成原理', '存储系统', '简单', '选择题', '存储层次自上而下速度变化规律是？', '["A. \\u8d8a\\u6765\\u8d8a\\u5feb", "B. \\u8d8a\\u6765\\u8d8a\\u6162", "C. \\u901f\\u5ea6\\u4e0d\\u53d8", "D. \\u65e0\\u56fa\\u5b9a\\u89c4\\u5f8b"]', 'B', '寄存器>Cache>主存>磁盘，速度逐级降低，容量、单位成本逐级升高。', '"\\u5c40\\u90e8\\u6027\\u539f\\u7406\\u662f\\u5206\\u5c42\\u5b58\\u50a8\\u8bbe\\u8ba1\\u57fa\\u7840"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (268, NULL, '计算机组成原理', '存储系统', '中等', '简答题', '简述时间局部性与空间局部性概念，举例说明。', '[]', '1.时间局部性：刚访问的数据短期内大概率重复访问，例循环变量；2.空间局部性：访问相邻地址数据概率极高，例数组顺序遍历；二者支撑Cache分层存储架构。', '无局部性程序无法依靠Cache提速。', '"\\u5757\\u9884\\u53d6\\u5229\\u7528\\u7a7a\\u95f4\\u5c40\\u90e8\\u6027"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (269, NULL, '计算机组成原理', '存储系统', '简单', '选择题', '需要定时刷新的存储芯片是？', '["A. SRAM", "B. DRAM", "C. MaskROM", "D. Flash"]', 'B', 'DRAM电容漏电，几毫秒必须刷新；SRAM触发器无需刷新，速度更快。', '"\\u5237\\u65b0\\u7531\\u5185\\u5b58\\u63a7\\u5236\\u5668\\u81ea\\u52a8\\u5b8c\\u6210"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (270, NULL, '计算机组成原理', '存储系统', '中等', '选择题', '多体交叉存储器核心目的是？', '["A. \\u964d\\u4f4e\\u5bb9\\u91cf", "B. \\u63d0\\u5347\\u4e3b\\u5b58\\u5e26\\u5bbd", "C. \\u51cf\\u5c11\\u5730\\u5740\\u4f4d", "D. \\u7b80\\u5316\\u8bd1\\u7801"]', 'B', '多个存储体分时并行读写，同时传输多组数据，解决CPU与主存带宽瓶颈。', '"\\u4ea4\\u53c9\\u7f16\\u5740\\u76f8\\u90bb\\u5730\\u5740\\u5206\\u5c5e\\u4e0d\\u540c\\u5b58\\u50a8\\u4f53"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (271, NULL, '计算机组成原理', '存储系统', '中等', '填空题', '位扩展增加存储____，字扩展增加存储单元数量。', '[]', '字长', '位扩展：多芯片并联拓宽单字bit宽度；字扩展串联增加存储条目。', '"\\u5b57\\u4f4d\\u6269\\u5c55\\u540c\\u65f6\\u5b8c\\u6210\\u5bbd\\u5ea6\\u4e0e\\u5bb9\\u91cf\\u6269\\u5bb9"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (272, NULL, '计算机组成原理', '存储系统', '简单', '选择题', 'Cache缺失时，以下操作正确的是？', '["A. \\u76f4\\u63a5\\u4e22\\u5f03\\u8bbf\\u95ee\\u8bf7\\u6c42", "B. \\u4ece\\u4e3b\\u5b58\\u8c03\\u5165\\u5bf9\\u5e94\\u5757\\u81f3Cache", "C. \\u76f4\\u63a5\\u8bbf\\u95ee\\u78c1\\u76d8", "D. \\u4fee\\u6539\\u5bc4\\u5b58\\u5668"]', 'B', 'Cache未命中触发缺失，读取主存完整块写入Cache后再返回数据。', '"\\u5757\\u5927\\u5c0f\\u4e0eCache\\u884c\\u3001\\u4e3b\\u5b58\\u5757\\u5b8c\\u5168\\u76f8\\u7b49"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (273, NULL, '计算机组成原理', '存储系统', '中等', '选择题', '直接映射Cache主要缺陷？', '["A. \\u786c\\u4ef6\\u590d\\u6742", "B. \\u7ec4\\u51b2\\u7a81\\u66ff\\u6362\\u9891\\u7e41", "C. \\u67e5\\u627e\\u901f\\u5ea6\\u6162", "D. \\u63a7\\u5236\\u903b\\u8f91\\u7e41\\u7410"]', 'B', '同一主存块只能映射固定Cache行，频繁访问同组地址会反复淘汰数据，冲突失效高。', '"\\u7ec4\\u76f8\\u8054\\u662f\\u76f4\\u63a5/\\u5168\\u76f8\\u8054\\u6298\\u4e2d\\u65b9\\u6848"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (274, NULL, '计算机组成原理', '存储系统', '中等', '填空题', 'Cache写____策略修改主存与Cache同步更新，写回仅淘汰时写盘。', '[]', '直达', '写直达（写穿）每次写操作同步更新主存；写回延迟写，仅块被替换时刷新。', '"\\u591a\\u6838\\u573a\\u666f\\u9700Cache\\u4e00\\u81f4\\u6027\\u534f\\u8bae"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (275, NULL, '计算机组成原理', '存储系统', '简单', '选择题', '页式虚拟存储加速地址转换部件是？', '["A. ALU", "B. TLB\\u5feb\\u8868", "C. \\u901a\\u7528\\u5bc4\\u5b58\\u5668", "D. \\u6307\\u4ee4\\u5bc4\\u5b58\\u5668"]', 'B', 'TLB缓存高频页表项，命中仅一次内存访问；无TLB需要两次内存读取页表。', '"\\u7f3a\\u9875\\u4e2d\\u65ad\\u89e6\\u53d1\\u78c1\\u76d8\\u9875\\u9762\\u8c03\\u5165"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (276, NULL, '计算机组成原理', '存储系统', '中等', '选择题', '抖动（颠簸）产生的直接原因是？', '["A. \\u9875\\u6846\\u5206\\u914d\\u8fc7\\u5c11", "B. Cache\\u5bb9\\u91cf\\u4e0d\\u8db3", "C. \\u78c1\\u76d8\\u901f\\u5ea6\\u6162", "D. \\u5730\\u5740\\u8fc7\\u957f"]', 'A', '分配页框远小于进程工作集，页面频繁换入换出，CPU利用率暴跌。', '"\\u5de5\\u4f5c\\u96c6\\u6a21\\u578b\\u6d88\\u9664\\u6296\\u52a8\\u95ee\\u9898"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (277, NULL, '计算机组成原理', '存储系统', '困难', '简答题', '对比Cache与虚拟存储器的管理层级、缺失代价、管理主体。', '[]', '1.层级：Cache是CPU-主存；虚拟存储主存-磁盘；2.管理：Cache硬件自动，虚拟存储操作系统软件；3.缺失代价：Cache缺失仅访问主存，缺页中断访问磁盘，延迟差百倍以上。', '二者均依靠局部性原理，但软硬件管控完全分离。', '"\\u865a\\u62df\\u5730\\u5740\\u2260\\u7269\\u7406\\u5185\\u5b58\\u5730\\u5740"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (278, NULL, '计算机组成原理', '指令系统', '简单', '选择题', '属于RISC架构典型特征的是？', '["A. \\u53d8\\u957f\\u6307\\u4ee4", "B. \\u786c\\u5e03\\u7ebf\\u63a7\\u5236\\u5668", "C. \\u5fae\\u7a0b\\u5e8f\\u63a7\\u5236", "D. \\u5355\\u6307\\u4ee4\\u529f\\u80fd\\u590d\\u6742"]', 'B', 'RISC：定长指令、简单操作、硬布线；CISC变长、微程序、复杂复合指令。', '"ARM/MIPS\\u4e3aRISC\\uff0cx86\\u4e3aCISC"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (279, NULL, '计算机组成原理', '指令系统', '中等', '选择题', '扩展操作码设计目的是？', '["A. \\u7f29\\u77ed\\u6307\\u4ee4\\u6267\\u884c\\u65f6\\u95f4", "B. \\u517c\\u5bb9\\u957f\\u77ed\\u6307\\u4ee4\\uff0c\\u6269\\u5c55\\u6307\\u4ee4\\u6570\\u91cf", "C. \\u7b80\\u5316\\u8bd1\\u7801\\u7535\\u8def", "D. \\u51cf\\u5c11\\u5185\\u5b58\\u5360\\u7528"]', 'B', '短指令使用短OP，长指令复用高位拓展操作码，在固定指令字长下支持更多指令。', '"CISC\\u666e\\u904d\\u91c7\\u7528\\u6269\\u5c55\\u64cd\\u4f5c\\u7801"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (280, NULL, '计算机组成原理', '指令系统', '简单', '选择题', '无需访问内存即可读取操作数的寻址方式？', '["A. \\u76f4\\u63a5\\u5bfb\\u5740", "B. \\u7acb\\u5373\\u5bfb\\u5740", "C. \\u95f4\\u63a5\\u5bfb\\u5740", "D. \\u57fa\\u5740\\u5bfb\\u5740"]', 'B', '立即数直接嵌入指令，译码时直接取出，无内存读取开销。', '"\\u5bc4\\u5b58\\u5668\\u5bfb\\u5740\\u4ec5\\u8bbf\\u95eeCPU\\u5185\\u90e8\\u5bc4\\u5b58\\u5668"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (281, NULL, '计算机组成原理', '指令系统', '中等', '填空题', '____寻址适合数组循环遍历，可自动增减偏移量。', '[]', '变址', '变址寄存器存放数组下标，基址存放数组首地址，循环自动修改变址值。', '"\\u57fa\\u5740\\u5bfb\\u5740\\u7528\\u4e8e\\u7a0b\\u5e8f\\u91cd\\u5b9a\\u4f4d"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (282, NULL, '计算机组成原理', '中央处理器', '简单', '选择题', '存放下一条指令地址的寄存器是？', '["A. IR", "B. PC", "C. MAR", "D. MDR"]', 'B', 'PC程序计数器存指令内存地址；IR保存当前译码指令。', '"\\u53d6\\u6307\\u5468\\u671fPC\\u81ea\\u52a8\\u81ea\\u589e"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (283, NULL, '计算机组成原理', '中央处理器', '中等', '选择题', 'PSW程序状态字不包含以下哪项？', '["A. \\u8fdb\\u4f4d\\u6807\\u5fd7", "B. \\u6ea2\\u51fa\\u6807\\u5fd7", "C. \\u6307\\u4ee4\\u64cd\\u4f5c\\u7801", "D. \\u6b63\\u8d1f\\u7b26\\u53f7\\u6807\\u5fd7"]', 'C', 'PSW存放运算状态：CF/SF/ZF/OF等；操作码存储在IR指令寄存器。', '"\\u6761\\u4ef6\\u8df3\\u8f6c\\u4f9d\\u8d56PSW\\u6807\\u5fd7\\u4f4d"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (284, NULL, '计算机组成原理', '中央处理器', '中等', '选择题', 'RISC处理器控制器采用哪种电路？', '["A. \\u5fae\\u7a0b\\u5e8f\\u63a7\\u5236\\u5668", "B. \\u786c\\u5e03\\u7ebf\\u7ec4\\u5408\\u903b\\u8f91", "C. \\u5b58\\u50a8\\u903b\\u8f91\\u63a7\\u5236\\u5668", "D. \\u5206\\u5c42\\u5fae\\u7801\\u63a7\\u5236\\u5668"]', 'B', '硬布线速度高适配定长简单RISC；微程序适配复杂变长CISC指令集。', '"\\u5fae\\u7a0b\\u5e8f\\u4fee\\u6539\\u6307\\u4ee4\\u53ea\\u9700\\u66f4\\u6362\\u5fae\\u4ee3\\u7801"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (285, NULL, '计算机组成原理', '中央处理器', '简单', '选择题', '流水线指令冲突统称为？', '["A. \\u4e2d\\u65ad", "B. \\u5192\\u9669", "C. \\u5f02\\u5e38", "D. \\u6ea2\\u51fa"]', 'B', '流水线三类冒险：结构资源冲突、数据依赖、分支控制冒险。', '"\\u65c1\\u8def\\u8f6c\\u53d1\\u89e3\\u51b3\\u6570\\u636e\\u5192\\u9669"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (286, NULL, '计算机组成原理', '中央处理器', '中等', '填空题', '流水线单条指令执行时间不变，但整体____大幅提升。', '[]', '吞吐率', '多指令重叠并行，单位时间完成指令数量提升，单条指令延迟不变。', '"\\u6d41\\u6c34\\u7ebf\\u6c14\\u6ce1\\u4f1a\\u964d\\u4f4e\\u541e\\u5410\\u7387"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (287, NULL, '计算机组成原理', '总线', '简单', '选择题', '系统总线不包含？', '["A. \\u5730\\u5740\\u603b\\u7ebf", "B. \\u6570\\u636e\\u603b\\u7ebf", "C. \\u63a7\\u5236\\u603b\\u7ebf", "D. \\u7535\\u6e90\\u603b\\u7ebf"]', 'D', '系统总线三类：单向地址、双向数据、双向控制总线。', '"\\u5730\\u5740\\u603b\\u7ebf\\u53ea\\u80fdCPU\\u5411\\u5916\\u8f93\\u51fa\\u5730\\u5740"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (288, NULL, '计算机组成原理', '总线', '中等', '选择题', '链式查询总线仲裁优先级规则是？', '["A. \\u8fdc\\u7aef\\u8bbe\\u5907\\u4f18\\u5148", "B. \\u9760\\u8fd1\\u603b\\u7ebf\\u63a7\\u5236\\u5668\\u4f18\\u5148\\u7ea7\\u9ad8", "C. \\u6240\\u6709\\u8bbe\\u5907\\u5e73\\u7b49", "D. \\u968f\\u673a\\u5206\\u914d"]', 'B', '总线请求信号串行传递，离仲裁器越近设备越早获得总线使用权。', '"\\u72ec\\u7acb\\u8bf7\\u6c42\\u4f18\\u5148\\u7ea7\\u53ef\\u8f6f\\u4ef6\\u914d\\u7f6e"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (289, NULL, '计算机组成原理', '输入输出系统', '简单', '选择题', '磁盘大批量数据传输最优IO方式？', '["A. \\u7a0b\\u5e8f\\u67e5\\u8be2", "B. \\u4e2d\\u65adIO", "C. DMA", "D. \\u8f6e\\u8be2"]', 'C', 'DMA控制器完成内存外设直传，CPU仅初始化与收尾中断，批量传输开销最低。', '"\\u5b57\\u7b26\\u8bbe\\u5907\\u4f18\\u5148\\u4f7f\\u7528\\u4e2d\\u65ad"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (290, NULL, '计算机组成原理', '输入输出系统', '中等', '选择题', '多重中断服务期间必须？', '["A. \\u5c4f\\u853d\\u6240\\u6709\\u4e2d\\u65ad", "B. \\u5f00\\u4e2d\\u65ad\\u5141\\u8bb8\\u9ad8\\u4f18\\u5148\\u7ea7\\u62a2\\u5360", "C. \\u5173\\u95edCPU", "D. \\u6e05\\u9664PSW"]', 'B', '多重中断服务流程开中断，高优先级中断可打断当前服务程序；单重中断全程关中断。', '"\\u4e2d\\u65ad\\u5411\\u91cf\\u5b58\\u50a8\\u670d\\u52a1\\u5165\\u53e3\\u5730\\u5740"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (291, NULL, '计算机组成原理', '输入输出系统', '困难', '简答题', '完整描述CPU响应外设中断的标准流程。', '[]', '1.外设发中断请求；2.当前指令执行完毕CPU响应；3.关中断；4.保存PC、PSW现场；5.查询中断向量跳转服务程序；6.执行外设处理逻辑；7.恢复寄存器现场；8.开中断返回原程序断点。', '关中断防止嵌套混乱，是响应阶段必要操作。', '"\\u4e0d\\u53ef\\u5728\\u6307\\u4ee4\\u4e2d\\u9014\\u6253\\u65ad\\u6267\\u884c"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (292, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '操作系统所属软件类型为？', '["A. \\u5e94\\u7528\\u8f6f\\u4ef6", "B. \\u7cfb\\u7edf\\u8f6f\\u4ef6", "C. \\u786c\\u4ef6\\u56fa\\u4ef6", "D. \\u7f16\\u7a0b\\u8bed\\u8a00"]', 'B', '操作系统是管理软硬件、衔接裸机与应用的底层系统软件，浏览器、办公软件属于应用软件。', '["\\u64cd\\u4f5c\\u7cfb\\u7edf\\u76f4\\u63a5\\u8fd0\\u884c\\u5728\\u88f8\\u673a\\u4e4b\\u4e0a"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (293, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '以下哪一项不属于操作系统四大核心管理模块？', '["A. \\u8fdb\\u7a0b\\u7ba1\\u7406", "B. \\u5185\\u5b58\\u7ba1\\u7406", "C. \\u6570\\u636e\\u5e93\\u7ba1\\u7406", "D. \\u6587\\u4ef6\\u7ba1\\u7406"]', 'C', 'OS四大核心功能：进程管理、内存管理、文件管理、IO设备管理，数据库属于上层应用软件。', '["IO\\u7ba1\\u7406\\u5305\\u542b\\u78c1\\u76d8\\u3001\\u663e\\u793a\\u5668\\u7b49\\u5916\\u8bbe\\u8c03\\u5ea6"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (294, NULL, '操作系统', '计算机系统概述', '中等', '选择题', '操作系统四大特征中最核心的基础特征是？', '["A. \\u5171\\u4eab", "B. \\u5e76\\u53d1", "C. \\u865a\\u62df", "D. \\u5f02\\u6b65"]', 'B', '并发是OS存在的前提，正是多程序并发运行才衍生共享、虚拟、异步特性。', '["\\u5e76\\u53d1\\u5b8f\\u89c2\\u540c\\u65f6\\u3001\\u5fae\\u89c2\\u4ea4\\u66ff\\uff0c\\u4e0d\\u7b49\\u540c\\u591a\\u6838\\u5e76\\u884c"]', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (295, NULL, '操作系统', '计算机系统概述', '中等', '填空题', '资源共享分为____共享和同时共享两类。', '[]', '互斥', '临界资源仅支持互斥共享，内存、磁盘等可多进程同时访问。', '"\\u6253\\u5370\\u673a\\u5c5e\\u4e8e\\u5178\\u578b\\u4e92\\u65a5\\u5171\\u4eab\\u8bbe\\u5907"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (296, NULL, '操作系统', '计算机系统概述', '困难', '简答题', '详细解释并发、共享、虚拟、异步四大特征的定义，说明四者之间的依存关系。', '[]', '1.并发：内存多程序宏观同时执行，微观交替占用CPU；2.共享：软硬件资源供多个进程共同使用；3.虚拟：时分/空分复用物理资源，抽象出多份逻辑资源；4.异步：进程以不可预测速度间断运行。依存关系：并发是基础，因并发产生资源共享需求，共享依托虚拟技术实现多用户隔离，并发调度直接导致进程异步推进。', '无并发则不存在资源争抢，虚拟、异步特征都会消失。', '"\\u5e76\\u884c\\u662f\\u591a\\u6838\\u786c\\u4ef6\\u540c\\u65f6\\u6267\\u884c\\uff0c\\u5e76\\u53d1\\u662f\\u5355\\u6838\\u4ea4\\u66ff\\u6a21\\u62df\\u540c\\u65f6\\u8fd0\\u884c"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (297, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '手工操作阶段不存在调度程序，其最大缺陷是？', '["A. \\u5185\\u5b58\\u8fc7\\u5c0f", "B. CPU\\u7b49\\u5f85\\u5916\\u8bbe\\u5168\\u7a0b\\u7a7a\\u95f2", "C. \\u65e0\\u6cd5\\u5b58\\u50a8\\u6570\\u636e", "D. \\u65e0\\u8f93\\u5165\\u8bbe\\u5907"]', 'B', '手工阶段程序串行执行，IO阻塞时CPU闲置，硬件资源利用率极低。', '"\\u5355\\u9053\\u6279\\u5904\\u7406\\u5f15\\u5165\\u76d1\\u7763\\u7a0b\\u5e8f\\u7f13\\u89e3\\u8be5\\u95ee\\u9898"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (298, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '单道批处理系统同一时刻内存中驻留进程数量为？', '["A. 0\\u4e2a", "B. 1\\u4e2a", "C. \\u591a\\u4e2a", "D. \\u7531\\u5185\\u5b58\\u51b3\\u5b9a"]', 'B', '单道批处理一次仅加载一道作业，该程序IO阻塞时CPU依然空闲。', '"\\u591a\\u9053\\u6279\\u5904\\u7406\\u53ef\\u540c\\u65f6\\u9a7b\\u7559\\u591a\\u9053\\u7a0b\\u5e8f"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (299, NULL, '操作系统', '计算机系统概述', '中等', '选择题', '多道批处理系统的核心优势是？', '["A. \\u652f\\u6301\\u4eba\\u673a\\u4ea4\\u4e92", "B. \\u5927\\u5e45\\u63d0\\u5347CPU\\u4e0e\\u5916\\u8bbe\\u5229\\u7528\\u7387", "C. \\u54cd\\u5e94\\u65f6\\u95f4\\u6781\\u77ed", "D. \\u5355\\u7528\\u6237\\u72ec\\u5360\\u5168\\u90e8\\u786c\\u4ef6"]', 'B', '多道程序并发调度，一道进程等待IO时CPU切换执行其他程序，消除空转损耗。', '"\\u5206\\u65f6\\u7cfb\\u7edf\\u624d\\u5177\\u5907\\u4ea4\\u4e92\\u5f0f\\u64cd\\u4f5c\\u80fd\\u529b"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (300, NULL, '操作系统', '计算机系统概述', '中等', '填空题', '____操作系统依靠时间片轮转调度，核心评价指标为响应时间。', '[]', '分时', '分时系统将CPU划分为微小时间片，轮流分配给多终端用户，兼顾公平与交互。', '"\\u5b9e\\u65f6\\u7cfb\\u7edf\\u6838\\u5fc3\\u6307\\u6807\\u662f\\u4efb\\u52a1\\u622a\\u6b62\\u65f6\\u95f4"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (301, NULL, '操作系统', '计算机系统概述', '困难', '简答题', '对比多道批处理、分时、实时三类操作系统的设计目标、适用场景与核心短板。', '[]', '1.多道批处理：目标高吞吐，适用于后台批量计算，无交互、响应时间不可控；2.分时系统：目标公平人机交互，适用于桌面多用户，无硬时间约束；3.实时系统：目标严格截止时间，硬实时用于工业控制，软实时用于音视频，吞吐与公平性优先级低。', '三类系统调度算法、资源分配策略完全不同。', '"\\u786c\\u5b9e\\u65f6\\u4efb\\u52a1\\u8d85\\u65f6\\u4f1a\\u4ea7\\u751f\\u707e\\u96be\\u6027\\u540e\\u679c"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (302, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '仅能在内核态执行的指令统称？', '["A. \\u7b97\\u672f\\u6307\\u4ee4", "B. \\u7279\\u6743\\u6307\\u4ee4", "C. \\u8df3\\u8f6c\\u6307\\u4ee4", "D. \\u903b\\u8f91\\u8fd0\\u7b97\\u6307\\u4ee4"]', 'B', '修改页表、操作硬件、中断控制等特权指令禁止用户态直接调用。', '"\\u7528\\u6237\\u6001\\u4ec5\\u53ef\\u6267\\u884c\\u666e\\u901a\\u8fd0\\u7b97\\u7c7b\\u6307\\u4ee4"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (303, NULL, '操作系统', '计算机系统概述', '简单', '选择题', '用户态切换至内核态的唯一正规入口是？', '["A. \\u51fd\\u6570\\u8c03\\u7528", "B. \\u7cfb\\u7edf\\u8c03\\u7528/\\u4e2d\\u65ad/\\u5f02\\u5e38", "C. \\u76f4\\u63a5\\u786c\\u4ef6\\u6307\\u4ee4", "D. \\u8fdb\\u7a0b\\u8df3\\u8f6c"]', 'B', '应用程序无法直接切换运行模式，必须通过陷阱指令发起系统调用触发模式切换。', '"\\u7cfb\\u7edf\\u8c03\\u7528\\u662f\\u7528\\u6237\\u8bbf\\u95ee\\u5185\\u6838\\u552f\\u4e00\\u63a5\\u53e3"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (304, NULL, '操作系统', '计算机系统概述', '中等', '选择题', '缺页中断属于哪一类事件？', '["A. \\u5916\\u90e8\\u786c\\u4ef6\\u4e2d\\u65ad", "B. CPU\\u5185\\u90e8\\u5f02\\u5e38", "C. \\u65f6\\u949f\\u4e2d\\u65ad", "D. \\u8bbe\\u5907IO\\u4e2d\\u65ad"]', 'B', '异常是指令执行时同步内部故障，中断是外设异步硬件信号。', '"\\u952e\\u76d8\\u3001\\u78c1\\u76d8\\u89e6\\u53d1\\u7684\\u662f\\u786c\\u4ef6\\u4e2d\\u65ad"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (305, NULL, '操作系统', '计算机系统概述', '中等', '填空题', '系统调用依靠____指令完成用户态到内核态切换。', '[]', '陷阱', '陷阱指令主动触发内核处理流程，区别于被动硬件中断。', '"Windows\\u4e3aint2e\\uff0cLinux\\u4e3asyscall"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (306, NULL, '操作系统', '计算机系统概述', '困难', '简答题', '区分中断与异常，从触发时机、触发来源、处理时机三个维度对比二者差异。', '[]', '1.触发来源：中断来自外部IO硬件；异常来自CPU指令内部故障；2.触发时机：中断异步，任意指令间隙到来；异常同步，执行对应指令瞬间触发；3.处理时机：中断可延迟，异常必须立刻停止当前指令处理。典型例子：磁盘中断=中断；除零、缺页=异常。', '二者都会保存现场并跳转内核处理程序。', '"\\u5f02\\u5e38\\u4e0d\\u53ef\\u5c4f\\u853d\\uff0c\\u90e8\\u5206\\u786c\\u4ef6\\u4e2d\\u65ad\\u53ef\\u5c4f\\u853d"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0);
INSERT INTO `question` (`id`, `session_id`, `subject`, `knowledge_point`, `difficulty`, `question_type`, `question_text`, `options_json`, `standard_answer`, `explanation`, `hints_json`, `recommend_reason`, `source`, `create_time`, `variant_type`, `sub_questions_json`, `is_deleted`) VALUES
  (307, NULL, '操作系统', '计算机系统概述', '简单', '选择题', 'Linux系统采用哪一类操作系统内核结构？', '["A. \\u5fae\\u5185\\u6838", "B. \\u5355\\u5185\\u6838", "C. \\u5206\\u5c42\\u7ed3\\u6784", "D. \\u6a21\\u5757\\u5316\\u7eaf\\u7528\\u6237\\u6001"]', 'B', '单内核所有核心功能运行在内核态，函数直接调用，执行效率高。', '"Windows NT\\u5c5e\\u4e8e\\u6df7\\u5408\\u5185\\u6838"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (308, NULL, '操作系统', '计算机系统概述', '中等', '选择题', '微内核操作系统中驱动程序运行在？', '["A. \\u5185\\u6838\\u6001", "B. \\u7528\\u6237\\u6001", "C. \\u56fa\\u4ef6\\u5c42", "D. \\u786c\\u4ef6\\u63a7\\u5236\\u5668"]', 'B', '微内核仅保留调度、通信基础逻辑，驱动、文件服务全部作为用户进程运行，崩溃不破坏内核。', '"\\u5355\\u5185\\u6838\\u9a71\\u52a8\\u76f4\\u63a5\\u8fd0\\u884c\\u5185\\u6838\\u6001"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (309, NULL, '操作系统', '计算机系统概述', '中等', '填空题', '分层式操作系统要求模块只能____调用底层模块。', '[]', '单向', '分层结构上层依赖下层，禁止反向调用，便于调试维护。', '"\\u6a21\\u5757\\u5316\\u7ed3\\u6784\\u5141\\u8bb8\\u6a21\\u5757\\u4e92\\u76f8\\u8c03\\u7528"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (310, NULL, '操作系统', '进程与线程', '简单', '选择题', '操作系统识别、调度进程的唯一核心数据结构是？', '["A. \\u7a0b\\u5e8f\\u4ee3\\u7801\\u6bb5", "B. PCB\\u8fdb\\u7a0b\\u63a7\\u5236\\u5757", "C. \\u6808\\u5185\\u5b58", "D. \\u5806\\u5185\\u5b58"]', 'B', 'PCB存储PID、状态、内存映射、寄存器现场等全部进程信息，无PCB则进程不存在。', '"\\u7a0b\\u5e8f\\u662f\\u9759\\u6001\\u6587\\u4ef6\\uff0c\\u8fdb\\u7a0b\\u662f\\u52a8\\u6001\\u8fd0\\u884c\\u5b9e\\u4f8b"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (311, NULL, '操作系统', '进程与线程', '简单', '选择题', '进程等待IO资源时所处状态为？', '["A. \\u8fd0\\u884c\\u6001", "B. \\u5c31\\u7eea\\u6001", "C. \\u963b\\u585e\\u6001", "D. \\u7ec8\\u6b62\\u6001"]', 'C', '阻塞进程不参与CPU调度，IO完成后转为就绪态才能竞争CPU。', '"\\u53ea\\u6709\\u5c31\\u7eea\\u961f\\u5217\\u5185\\u8fdb\\u7a0b\\u53ef\\u88ab\\u8c03\\u5ea6\\u6267\\u884c"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (312, NULL, '操作系统', '进程与线程', '中等', '选择题', '线程切换相比进程切换开销更小的根本原因是？', '["A. \\u7ebf\\u7a0b\\u4ee3\\u7801\\u66f4\\u77ed", "B. \\u7ebf\\u7a0b\\u5171\\u4eab\\u8fdb\\u7a0b\\u5730\\u5740\\u7a7a\\u95f4\\uff0c\\u65e0\\u9700\\u5237\\u65b0\\u9875\\u8868", "C. \\u7ebf\\u7a0b\\u65e0\\u5bc4\\u5b58\\u5668", "D. \\u7ebf\\u7a0b\\u4e0d\\u5360\\u7528CPU"]', 'B', '进程切换需要替换页表、刷新缓存；线程仅切换私有栈与寄存器，地址空间不变。', '"\\u7ebf\\u7a0b\\u5171\\u4eab\\u5168\\u5c40\\u53d8\\u91cf\\u3001\\u6587\\u4ef6\\u53e5\\u67c4\\u7b49\\u8d44\\u6e90"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (313, NULL, '操作系统', '进程与线程', '中等', '填空题', '线程私有资源为寄存器和____，共享进程全部地址空间。', '[]', '栈', '每个线程独立栈保存局部变量，堆、代码段、全局变量全部共享。', '"\\u591a\\u7ebf\\u7a0b\\u4fee\\u6539\\u5171\\u4eab\\u53d8\\u91cf\\u9700\\u8981\\u540c\\u6b65\\u4e92\\u65a5"', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0),
  (314, NULL, '操作系统', '进程与线程', '困难', '简答题', '从资源隔离、切换开销、调度单位、通信方式四方面对比进程与线程差异。', '[]', '1.资源：进程地址空间完全隔离；线程共享进程资源；2.切换：进程刷新页表开销极大，线程仅切换栈和寄存器；3.调度：线程是CPU最小调度单元；4.通信：进程依靠管道/套接字IPC；线程直接读写共享内存，需互斥保护。', '多线程适合计算密集并行，多进程适合独立隔离业务。', '"\\u4e00\\u4e2a\\u8fdb\\u7a0b\\u81f3\\u5c11\\u5305\\u542b\\u4e00\\u4e2a\\u4e3b\\u7ebf\\u7a0b"', '', 'seed', '2026-06-26 02:53:15.831757', 'essay', '[]', 0),
  (315, NULL, '操作系统', '进程与线程', '简单', '选择题', '分时操作系统标准调度算法是？', '["A. FCFS\\u5148\\u6765\\u5148\\u670d\\u52a1", "B. \\u65f6\\u95f4\\u7247\\u8f6e\\u8f6cRR", "C. SJF\\u77ed\\u4f5c\\u4e1a\\u4f18\\u5148", "D. \\u9ad8\\u54cd\\u5e94\\u6bd4HRRN"]', 'B', 'RR算法将CPU均等划分为时间片，轮流分配给所有就绪进程，保证交互公平。', '"\\u6279\\u5904\\u7406\\u7cfb\\u7edf\\u5e38\\u7528SJF\\u63d0\\u5347\\u541e\\u5410\\u7387"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (316, NULL, '操作系统', '进程与线程', '中等', '选择题', 'HRRN高响应比调度的响应比计算公式正确的是？', '["A. \\u670d\\u52a1\\u65f6\\u95f4/\\u7b49\\u5f85\\u65f6\\u957f", "B. (\\u7b49\\u5f85\\u65f6\\u95f4+\\u670d\\u52a1\\u65f6\\u95f4)/\\u670d\\u52a1\\u65f6\\u95f4", "C. \\u7b49\\u5f85\\u65f6\\u95f4", "D. \\u670d\\u52a1\\u65f6\\u957f"]', 'B', '等待越久响应比越高，避免短作业长期抢占导致长作业饥饿。', '"HRRN\\u5c5e\\u4e8e\\u975e\\u62a2\\u5360\\u8c03\\u5ea6\\u7b97\\u6cd5"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (317, NULL, '操作系统', '进程与线程', '中等', '选择题', '以下调度算法中会产生进程饥饿现象的是？', '["A. FCFS", "B. SSTF\\u78c1\\u76d8\\u8c03\\u5ea6", "C. \\u65f6\\u95f4\\u7247\\u8f6e\\u8f6c", "D. HRRN"]', 'B', '持续短任务不断到来，长任务永久无法获得资源即饥饿。', '"SCAN\\u7535\\u68af\\u7b97\\u6cd5\\u53ef\\u89e3\\u51b3\\u9965\\u997f\\u95ee\\u9898"', '', 'seed', '2026-06-26 02:53:15.831757', 'choice', '[]', 0),
  (318, NULL, '操作系统', '进程与线程', '中等', '填空题', '____调度算法优先选择当前运行时间最短的就绪进程。', '[]', '短作业优先(SJF)', 'SJF最小化平均等待时间，但存在饥饿缺陷。', '["\\u62a2\\u5360\\u5f0fSJF\\u53c8\\u79f0\\u6700\\u77ed\\u5269\\u4f59\\u65f6\\u95f4\\u4f18\\u5148"]', '', 'seed', '2026-06-26 02:53:15.831757', 'fill', '[]', 0);

-- ------------------------------------------------------------
-- Data for `question_generation_session`
-- ------------------------------------------------------------
INSERT INTO `question_generation_session` (`id`, `user_id`, `generation_mode`, `subject`, `knowledge_point`, `difficulty`, `question_type`, `question_count`, `reason`, `create_time`, `recommend_mode`, `is_deleted`) VALUES
  (1, 1, '自由选择', '????', '??????', '中等', '选择题', 1, '自由选择：围绕 ???? / ?????? 生成 1 道 中等 选择题。', '2026-06-23 03:21:04.545577', '', 0),
  (2, 1, '自由选择', '????', '??????', '中等', '选择题', 1, '自由选择：围绕 ???? / ?????? 生成 1 道 中等 选择题。', '2026-06-23 03:21:04.554509', '', 0),
  (3, 1, '自由选择', '数据结构', '树与二叉树', '中等', '选择题', 2, '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', '2026-06-23 03:21:29.012894', '', 0),
  (4, 1, '自由选择', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-23 03:21:29.056868', '', 0),
  (5, 1, '自由选择', '操作系统', '进程与线程', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 进程与线程 生成 1 道 中等 选择题。', '2026-06-23 03:26:39.206557', '', 0),
  (6, 1, '自由选择', '操作系统', '进程与线程', '中等', '选择题', 3, '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', '2026-06-23 03:26:47.041787', '', 0),
  (7, 1, '自由选择', '操作系统', '进程与线程', '中等', '填空题', 3, '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 填空题。', '2026-06-23 03:27:20.560256', '', 0),
  (8, 1, '自由选择', '操作系统', '进程与线程', '中等', '填空题', 1, '自由选择：围绕 操作系统 / 进程与线程 生成 1 道 中等 填空题。', '2026-06-23 03:47:23.592020', '', 0),
  (9, 1, '自由选择', '操作系统', '页面置换算法', '中等', '填空题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 填空题。', '2026-06-23 03:47:48.761473', '', 0),
  (10, 1, '自由选择', '操作系统', '进程与线程', '中等', '选择题', 3, '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', '2026-06-23 03:48:13.662585', '', 0),
  (11, 1, '自由选择', '操作系统', '进程与线程', '中等', '选择题', 3, '自由选择：围绕 操作系统 / 进程与线程 生成 3 道 中等 选择题。', '2026-06-23 03:48:37.949436', '', 0),
  (12, 1, '自由选择', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-23 03:54:22.762134', '', 0),
  (13, 1, '自由选择', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-23 04:01:04.168548', '', 0),
  (14, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 1, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-23 06:39:11.520575', '', 0),
  (15, 1, '自由选择', '操作系统', '进程与线程', '中等', '填空题', 1, '自由选择：围绕 操作系统 / 进程与线程 生成 1 道 中等 填空题。', '2026-06-23 06:43:01.353945', '', 0),
  (16, 1, '自由选择', '计算机网络', '文件系统', '中等', '选择题', 1, '自由选择：围绕 计算机网络 / 文件系统 生成 1 道 中等 选择题。', '2026-06-23 07:01:14.937299', '', 0),
  (17, 1, '自由选择', '计算机网络', '进程与线程', '中等', '综合题', 1, '自由选择：围绕 计算机网络 / 进程与线程 生成 1 道 中等 综合题。', '2026-06-23 07:01:48.400630', '', 0),
  (18, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', '2026-06-23 07:53:41.207840', '', 0),
  (19, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', '2026-06-23 07:54:04.174274', '', 0),
  (20, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', '2026-06-23 07:56:20.063020', '', 0),
  (21, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', '2026-06-23 07:57:39.050066', '', 0),
  (22, 1, '薄弱点强化', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点强化：围绕 操作系统 / 页面置换算法 生成 3 道 中等 选择题。', '2026-06-23 07:58:51.154513', '', 0),
  (23, 1, 'smart', '操作系统', '页面置换算法', '中等', '选择题', 3, '薄弱点 · 错 1 次 · 薄弱分 13，优先生成中等专项题。', '2026-06-23 12:52:33.403697', '薄弱点强化', 0),
  (24, 1, 'manual', '数据结构', '栈和队列', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 栈和队列 生成 1 道 中等 填空题。', '2026-06-23 13:21:19.715495', '', 0),
  (25, 1, 'manual', '数据结构', '线性表', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 线性表 生成 1 道 中等 填空题。', '2026-06-23 13:25:43.082055', '', 0),
  (26, 1, 'manual', '数据结构', '树与二叉树', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 树与二叉树 生成 1 道 中等 填空题。', '2026-06-23 13:30:23.610636', '', 0),
  (27, 1, 'manual', '数据结构', '线性表', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 线性表 生成 1 道 中等 填空题。', '2026-06-23 13:33:32.260140', '', 0),
  (28, 1, 'manual', '数据结构', '栈和队列', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 栈和队列 生成 1 道 中等 填空题。', '2026-06-23 13:33:59.368527', '', 0),
  (29, 1, 'manual', '计算机网络', '数据链路层', '中等', '填空题', 1, '自由选择：围绕 计算机网络 / 数据链路层 生成 1 道 中等 填空题。', '2026-06-23 13:34:23.323775', '', 0),
  (30, 1, 'manual', '数据结构', '图', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 图 生成 1 道 中等 填空题。', '2026-06-23 13:40:51.863702', '', 0),
  (31, 1, 'manual', '数据结构', '图的遍历', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 图的遍历 生成 1 道 中等 填空题。', '2026-06-23 13:51:46.414617', '', 0),
  (32, 1, 'manual', '数据结构', '图', '中等', '选择题', 1, '自由选择：围绕 数据结构 / 图 生成 1 道 中等 选择题。', '2026-06-23 13:53:44.208747', '', 0),
  (33, 1, 'manual', '数据结构', '图', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 图 生成 1 道 中等 填空题。', '2026-06-23 13:54:05.691316', '', 0),
  (34, 1, 'manual', '数据结构', '查找', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 查找 生成 1 道 中等 填空题。', '2026-06-23 13:55:08.380004', '', 0),
  (35, 1, 'manual', '数据结构', '栈和队列', '中等', '填空题', 1, '自由选择：围绕 数据结构 / 栈和队列 生成 1 道 中等 填空题。', '2026-06-23 13:55:47.013103', '', 0),
  (36, 1, 'smart', '????', '??????', '中等', '选择题', 1, '不熟 · 错 1 次 · 连续错 0 次，优先生成 选择题 专项题。', '2026-06-23 14:38:30.499531', '薄弱点强化', 0),
  (37, 1, 'smart', '操作系统', '页面置换算法', '简单', '简答题', 1, '最近错题来自「页面置换算法」（OCR 导入待确认），生成 5 道同类变式题检查是否真正理解错因。', '2026-06-23 14:40:40.668063', '最近错题复练', 0),
  (38, 1, 'manual', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-24 00:20:44.226737', '', 0),
  (39, 1, 'manual', '计算机组成原理', '指令系统', '真题难度', '选择题', 1, '自由选择：围绕 计算机组成原理 / 指令系统 生成 1 道 真题难度 选择题。', '2026-06-24 00:26:55.454109', '', 0),
  (40, 1, 'manual', '数据结构', '树与二叉树', '简单', '选择题', 1, '自由选择：围绕 数据结构 / 树与二叉树 生成 1 道 简单 选择题。', '2026-06-24 00:54:57.020416', '', 0),
  (41, 1, 'manual', '数据结构', '树与二叉树', '中等', '选择题', 2, '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', '2026-06-24 11:53:04.116035', '', 0),
  (42, 1, 'manual', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-24 11:53:38.747546', '', 0),
  (43, 1, 'manual', '数据结构', '树与二叉树', '中等', '选择题', 2, '自由选择：围绕 数据结构 / 树与二叉树 生成 2 道 中等 选择题。', '2026-06-24 11:56:50.602974', '', 0),
  (44, 1, 'manual', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-24 11:58:08.364329', '', 0),
  (45, 1, 'smart', '计算机网络', '数据链路层', '简单', '填空题', 5, '薄弱点 · 错 11 次 · 连续错 11 次，优先生成 填空题 专项题。', '2026-06-25 01:26:29.713212', '薄弱点强化', 0),
  (46, 1, 'manual', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-25 17:19:32.078815', '', 0),
  (47, 1, 'manual', '操作系统', '页面置换算法', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 页面置换算法 生成 1 道 中等 选择题。', '2026-06-25 17:21:03.968290', '', 0),
  (48, 1, 'smart', '操作系统', '进程同步', 'medium', '选择题', 1, 'practice：围绕 操作系统 / 进程同步 生成 1 道 medium 选择题。', '2026-06-25 17:29:42.700300', 'practice', 0),
  (49, 1, 'smart', '操作系统', '同步与互斥', 'medium', '选择题', 1, 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', '2026-06-25 17:31:23.666746', 'practice', 0),
  (50, 1, 'smart', '操作系统', '同步与互斥', 'medium', '选择题', 1, 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', '2026-06-25 17:31:58.888588', 'practice', 0),
  (51, 1, 'smart', '操作系统', '同步与互斥', 'medium', '选择题', 1, 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', '2026-06-25 17:33:23.987494', 'practice', 0),
  (52, 1, 'smart', '操作系统', '同步与互斥', 'medium', '选择题', 1, 'practice：围绕 操作系统 / 同步与互斥 生成 1 道 medium 选择题。', '2026-06-25 17:35:35.521362', 'practice', 0),
  (53, 1, 'smart', '计算机网络', '数据链路层', '简单', '填空题', 3, '薄弱点强化：围绕 计算机网络 / 数据链路层 生成 3 道 简单 填空题。', '2026-06-25 17:38:48.706089', '薄弱点强化', 0),
  (54, 1, 'manual', '数据结构', '绪论', '中等', '选择题', 1, '自由选择：围绕 数据结构 / 绪论 生成 1 道 中等 选择题。', '2026-06-25 17:55:05.717131', '', 0),
  (55, 1, 'manual', '数据结构', '图', '真题难度', '选择题', 1, '自由选择：围绕 数据结构 / 图 生成 1 道 真题难度 选择题。', '2026-06-25 17:55:36.447158', '', 0),
  (56, 1, 'smart', '计算机组成原理', '输入输出系统', '简单', '综合题', 2, '薄弱点强化：计算机组成原理 / 输入输出系统 fallback 生成 2 道。', '2026-06-25 18:01:50.007709', '薄弱点强化', 0),
  (57, 1, 'manual', '操作系统', '内存管理', '真题难度', '选择题', 1, '自由选择：围绕 操作系统 / 内存管理 生成 1 道 真题难度 选择题。', '2026-06-25 18:02:05.482543', '', 0),
  (58, 1, 'manual', '计算机网络', '计算机网络体系结构', '真题难度', '选择题', 1, '自由选择：围绕 计算机网络 / 计算机网络体系结构 生成 1 道 真题难度 选择题。', '2026-06-25 18:07:22.414116', '', 0),
  (59, 1, 'manual', '操作系统', '文件管理', '中等', '综合题', 1, '自由选择：操作系统 / 文件管理 fallback 生成 1 道。', '2026-06-25 18:11:18.063149', '', 0),
  (60, 1, 'manual', '操作系统', '文件管理', '中等', '综合题', 1, '自由选择：操作系统 / 文件管理 fallback 生成 1 道。', '2026-06-25 18:11:31.641271', '', 0),
  (61, 1, 'manual', '操作系统', '文件管理', '中等', '选择题', 1, '自由选择：围绕 操作系统 / 文件管理 生成 1 道 中等 选择题。', '2026-06-25 18:18:01.173170', '', 0),
  (62, 1, 'manual', '操作系统', '文件管理', '真题难度', '选择题', 1, '自由选择：围绕 操作系统 / 文件管理 生成 1 道 真题难度 选择题。', '2026-06-25 18:18:20.836155', '', 0),
  (63, 1, 'manual', '操作系统', '文件管理', '真题难度', '选择题', 1, '自由选择：围绕 操作系统 / 文件管理 生成 1 道 真题难度 选择题。', '2026-06-25 18:18:23.282418', '', 0),
  (64, 1, 'manual', '计算机组成原理', '存储系统', '真题难度', '选择题', 1, '自由选择：围绕 计算机组成原理 / 存储系统 生成 1 道 真题难度 选择题。', '2026-06-25 18:18:50.943351', '', 0),
  (65, 1, 'manual', '计算机组成原理', '存储系统', '真题难度', '选择题', 1, '自由选择：围绕 计算机组成原理 / 存储系统 生成 1 道 真题难度 选择题。', '2026-06-25 18:18:51.152187', '', 0),
  (66, 1, 'smart', '数据结构', '查找', '中等', '选择题', 3, '薄弱点强化：围绕 数据结构 / 查找 生成 3 道 中等 选择题。', '2026-06-25 18:19:48.080504', '薄弱点强化', 0),
  (67, 1, 'manual', '计算机组成原理', '指令系统', '真题难度', '选择题', 1, '自由选择：围绕 计算机组成原理 / 指令系统 生成 1 道 真题难度 选择题。', '2026-06-25 18:26:15.675555', '', 0),
  (68, 1, 'manual', '操作系统', '内存管理', '真题难度', '选择题', 3, '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', '2026-06-25 18:31:48.996048', '', 0),
  (69, 1, 'manual', '操作系统', '内存管理', '真题难度', '选择题', 3, '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', '2026-06-25 18:32:05.993538', '', 0),
  (70, 1, 'manual', '计算机组成原理', '中央处理器', '真题难度', '选择题', 1, '自由选择：围绕 计算机组成原理 / 中央处理器 生成 1 道 真题难度 选择题。', '2026-06-26 00:19:10.900050', '', 0),
  (71, 1, 'manual', '操作系统', '内存管理', '真题难度', '选择题', 3, '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', '2026-06-26 00:19:43.067048', '', 0),
  (72, 1, 'manual', '操作系统', '内存管理', '真题难度', '选择题', 3, '自由选择：围绕 操作系统 / 内存管理 生成 3 道 真题难度 选择题。', '2026-06-26 00:19:55.353877', '', 0),
  (73, 1, 'manual', '数据结构', '图', '真题难度', '选择题', 3, '自由选择：围绕 数据结构 / 图 生成 3 道 真题难度 选择题。', '2026-06-26 00:20:44.075407', '', 0),
  (74, 1, 'manual', '计算机组成原理', '计算机系统概述', '简单', '选择题', 1, '自由选择：围绕 计算机组成原理 / 计算机系统概述 生成 1 道 简单 选择题。', '2026-06-26 00:29:04.372053', '', 0);

-- ------------------------------------------------------------
-- Data for `report`
-- ------------------------------------------------------------
INSERT INTO `report` (`id`, `user_id`, `title`, `summary`, `weak_points`, `main_error_type`, `qa_focus`, `forum_focus`, `video_suggestion`, `plan_json`, `create_time`, `report_type`, `start_date`, `end_date`, `is_deleted`) VALUES
  (1, 1, 'Turing 408 阶段学习报告', '累计答题 1 道，正确 0 道，当前重点是 ??????。', '??????', 'OCR 导入待确认、????', '页面置换算法、TCP 连接释放', '操作系统与计算机网络高频讨论', '优先观看页面置换算法和 TCP 四次挥手专题', '["完成页面置换算法 3 道中等题", "复述 TCP TIME_WAIT 两个作用", "整理 1 条错因进入长期记忆"]', '2026-06-23 03:21:29.039825', 'stage', '', '', 0),
  (2, 1, 'Turing 408 阶段学习报告', '阶段总结', '线性表、栈和队列、图、查找、指令系统、页面置换算法、数据链路层、??????、待生成、输入输出系统、DMA与中断方式的时间计算', '概念理解错误', '输入输出系统、DMA与中断方式的时间计算', '页面置换算法、数据链路层', '输入输出系统工作原理、DMA与中断方式对比', '["校对OCR导入的错题文本", "针对输入输出系统进行专项复习", "生成DMA与中断方式时间计算的同类训练题"]', '2026-06-24 00:47:16.760574', 'stage', '', '', 0),
  (3, 1, 'Turing 408 阶段学习报告', '阶段学习显示，408科目中数据结构、计算机组成原理和操作系统的基础概念掌握不牢固，特别是在输入输出系统和DMA与中断方式的时间计算方面错误较多。正确率较低，需加强基础知识的理解和应用。', '线性表、栈和队列、图、查找、指令系统、页面置换算法、数据链路层、输入输出系统、DMA与中断方式的时间计算', '概念理解错误和知识混淆', '输入输出系统、DMA与中断方式的时间计算、指令系统', 'DMA与中断方式的性能比较、页面置换算法的实际应用、数据链路层的协议细节', 'DMA与中断方式的工作原理、输入输出系统的设计、页面置换算法的实现', '["重点复习输入输出系统和DMA与中断方式的时间计算", "针对指令系统进行专项练习", "校对并复盘OCR导入的错题，确保理解正确"]', '2026-06-24 00:51:18.030635', 'stage', '', '', 0),
  (4, 1, 'Turing 408 阶段学习报告', '阶段学习显示在408考试中表现有待提高，累计答题17道，正确率较低，仅为2道。薄弱环节主要集中在数据结构、计算机组成原理和操作系统等多个核心知识点上，特别是输入输出系统和DMA与中断方式的时间计算方面存在较多错误。', '线性表、栈和队列、图、查找、指令系统、页面置换算法、数据链路层、输入输出系统、DMA与中断方式的时间计算', '概念混淆与知识理解错误', '输入输出系统、DMA与中断方式的时间计算、指令系统', 'DMA与中断方式的性能比较、输入输出系统的工作原理、页面置换算法的实际应用', 'DMA与中断方式的时间计算详解、输入输出系统的工作原理、指令系统的设计与实现', '["重点复习输入输出系统相关知识点，特别是DMA与中断方式的时间计算", "针对指令系统进行专项练习，确保概念清晰", "通过模拟题加强对页面置换算法和数据链路层的理解与应用"]', '2026-06-24 00:53:34.545498', 'stage', '', '', 0),
  (5, 1, 'Turing 408 阶段学习报告', '阶段总结显示，累计答题17道，正确题数2道，正确率较低。薄弱知识点广泛分布于数据结构、计算机组成原理和操作系统等多个领域。最近错题主要集中在算法理解错误、概念混淆和知识理解错误等方面。长期记忆显示对DMA与中断方式的时间计算有反复的思考和纠正过程。', '线性表、栈和队列、树与二叉树、图、查找、指令系统、页面置换算法、数据链路层、输入输出系统、DMA与中断方式的时间计算', '概念混淆和知识理解错误', 'DMA与中断方式的时间计算、页面置换算法、输入输出系统', 'DMA与中断方式的性能比较、页面置换算法的实际应用、输入输出系统的优化策略', 'DMA与中断方式的工作原理、页面置换算法的详细讲解、输入输出系统的深入解析', '"[\\"\\u9488\\u5bf9DMA\\u4e0e\\u4e2d\\u65ad\\u65b9\\u5f0f\\u7684\\u65f6\\u95f4\\u8ba1\\u7b97\\u8fdb\\u884c\\u4e13\\u9879\\u7ec3\\u4e60\\", \\"\\u590d\\u4e60\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u7684\\u76f8\\u5173\\u77e5\\u8bc6\\u70b9\\u5e76\\u8fdb\\u884c\\u6a21\\u62df\\u9898\\u8bad\\u7ec3\\", \\"\\u6df1\\u5165\\u7406\\u89e3\\u8f93\\u5165\\u8f93\\u51fa\\u7cfb\\u7edf\\u7684\\u5de5\\u4f5c\\u539f\\u7406\\u5e76\\u5b8c\\u6210\\u76f8\\u5173\\u9898\\u76ee\\"]"', '2026-06-24 11:53:18.831930', 'stage', '', '', 0),
  (6, 1, 'Turing 408 阶段学习报告', '阶段总结显示，累计答题18道，正确率较低，仅为2道。薄弱知识点广泛分布于数据结构、计算机组成原理和操作系统等多个领域。最近错题主要集中在页面置换算法、树与二叉树、指令系统以及DMA与中断方式的时间计算上。长期记忆中的DMA传输和中断时间计算需要特别注意。', '线性表、栈和队列、树与二叉树、图、查找、指令系统、页面置换算法、数据链路层、输入输出系统、DMA与中断方式的时间计算', '概念混淆和理解偏差，特别是在页面置换算法和DMA与中断方式的时间计算上。', '应重点关注DMA与中断方式的时间计算、页面置换算法的具体实现和应用，以及树与二叉树的相关算法。', '适合在论坛关注或讨论的主题包括页面置换算法的优化、DMA传输与中断处理的性能比较，以及树与二叉树的实际应用案例。', '建议观看关于页面置换算法、DMA与中断方式的时间计算以及树与二叉树的详细讲解视频。', '"[\\"\\u9488\\u5bf9\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u8fdb\\u884c\\u4e13\\u9879\\u7ec3\\u4e60\\uff0c\\u7406\\u89e3\\u5404\\u79cd\\u7f6e\\u6362\\u7b56\\u7565\\u7684\\u4f18\\u7f3a\\u70b9\\", \\"\\u590d\\u4e60DMA\\u4e0e\\u4e2d\\u65ad\\u65b9\\u5f0f\\u7684\\u65f6\\u95f4\\u8ba1\\u7b97\\uff0c\\u901a\\u8fc7\\u4f8b\\u9898\\u52a0\\u6df1\\u7406\\u89e3\\", \\"\\u7ec3\\u4e60\\u6811\\u4e0e\\u4e8c\\u53c9\\u6811\\u7684\\u76f8\\u5173\\u7b97\\u6cd5\\uff0c\\u5305\\u62ec\\u904d\\u5386\\u548c\\u5e73\\u8861\\u4e8c\\u53c9\\u6811\\u7684\\u64cd\\u4f5c\\"]"', '2026-06-24 11:57:40.641311', 'stage', '', '', 0),
  (7, 1, 'Turing 408 阶段学习报告', '阶段总结显示，你在408考研学习中累计答题19道，正确题数2道，正确率较低。薄弱知识点广泛分布在数据结构、计算机组成原理、操作系统和计算机网络等多个核心领域。最近错题主要集中在页面置换算法、树与二叉树、指令系统以及DMA与中断方式的时间计算上，反映出对算法理解和概念辨析存在困难。长期记忆内容显示你对输入输出系统和DMA传输机制已有初步认识，但需要进一步巩固。', '线性表、栈和队列、树与二叉树、图、查找、指令系统、页面置换算法、数据链路层、输入输出系统、DMA与中断方式的时间计算', '算法理解偏差和概念混淆', '页面置换算法（如FIFO、LRU等）、DMA与中断方式的时间计算、树与二叉树的操作与性质、指令系统的设计与执行', '页面置换算法的实际应用与优化、DMA传输与中断处理的性能比较、树结构的遍历与平衡算法', '计算机组成原理中的DMA与中断机制、操作系统中的页面置换算法详解、数据结构中的树与二叉树专题', '"[\\"\\u9488\\u5bf9\\u9875\\u9762\\u7f6e\\u6362\\u7b97\\u6cd5\\u8fdb\\u884c\\u4e13\\u9879\\u7ec3\\u4e60\\uff0c\\u91cd\\u70b9\\u7406\\u89e3\\u5404\\u79cd\\u7b56\\u7565\\u7684\\u4f18\\u52a3\\u53ca\\u9002\\u7528\\u573a\\u666f\\", \\"\\u5b8c\\u6210DMA\\u4e0e\\u4e2d\\u65ad\\u65b9\\u5f0f\\u65f6\\u95f4\\u8ba1\\u7b97\\u7684\\u6a21\\u62df\\u9898\\uff0c\\u638c\\u63e1\\u516c\\u5f0f\\u5e94\\u7528\\u4e0e\\u5355\\u4f4d\\u6362\\u7b97\\", \\"\\u7cfb\\u7edf\\u590d\\u4e60\\u6811\\u4e0e\\u4e8c\\u53c9\\u6811\\u7684\\u57fa\\u672c\\u64cd\\u4f5c\\uff0c\\u5305\\u62ec\\u904d\\u5386\\u3001\\u63d2\\u5165\\u3001\\u5220\\u9664\\u7b49\\u7b97\\u6cd5\\u5b9e\\u73b0\\"]"', '2026-06-25 01:29:56.543861', 'stage', '', '', 0);

-- ------------------------------------------------------------
-- Data for `schema_migrations`
-- ------------------------------------------------------------
INSERT INTO `schema_migrations` (`version`, `name`, `checksum`, `applied_at`) VALUES
  ('001', '001_create_user_tables.sql', 'b9a4334e47e357c9e706aa35785ef7355faaa9b705e25f1ed8b1fc34119b3986', '2026-06-26 10:08:47'),
  ('002', '002_create_knowledge_tables.sql', 'de1fc28ce9907afe74c0d5f44171d8eeafaff4a2802d25b9d3161daae1dc2333', '2026-06-26 10:08:47'),
  ('003', '003_create_question_tables.sql', 'ad892321a190565cb0d270cf19947dabaaf1432839724b9ef87942978f0ccf68', '2026-06-26 10:08:47'),
  ('004', '004_create_mastery_tables.sql', 'b8104357f6f7a8ebe54d086dd176718fc82f21394bafe74da11b94b9c0fa1d60', '2026-06-26 10:08:47'),
  ('005', '005_create_forum_tables.sql', '0fa18434471265eae67794abead3a13dc6182d9b7a3f732010d0187081c58ec1', '2026-06-26 10:08:47'),
  ('006', '006_create_report_tables.sql', 'b1af26f264f9814a159e0607be8826932d2236c0310e65d4e802d9814ab59cae', '2026-06-26 10:08:47');

-- ------------------------------------------------------------
-- Data for `subject`
-- ------------------------------------------------------------
INSERT INTO `subject` (`id`, `name`, `description`, `sort_order`, `is_deleted`, `create_time`, `update_time`) VALUES
  (1, '数据结构', '408 数据结构 考纲知识体系', 1, 0, '2026-06-24 11:51:26', '2026-06-24 11:51:26'),
  (2, '计算机组成原理', '408 计算机组成原理 考纲知识体系', 2, 0, '2026-06-24 11:51:26', '2026-06-24 11:51:26'),
  (3, '操作系统', '408 操作系统 考纲知识体系', 3, 0, '2026-06-24 11:51:26', '2026-06-24 11:51:26'),
  (4, '计算机网络', '408 计算机网络 考纲知识体系', 4, 0, '2026-06-24 11:51:26', '2026-06-24 11:51:26');

-- ------------------------------------------------------------
-- Data for `user`
-- ------------------------------------------------------------
INSERT INTO `user` (`id`, `email`, `username`, `nickname`, `password_hash`, `avatar_url`, `status`, `create_time`, `update_time`, `is_deleted`, `delete_time`, `create_ip`) VALUES
  (1, 'demo@turing408.ai', 'demo', '林同学', 'pbkdf2_sha256$5ISWUKom-rbq3l6ik1iuyQ==$ol_qCoMyHsoq9UegHp0lEJuotJfcjGTQzOZniRvIeUM=', '', 'active', '2026-06-23 03:21:04.443109', '2026-06-23 03:21:04.443109', 0, NULL, '');

-- ------------------------------------------------------------
-- Data for `user_daily_activity`
-- ------------------------------------------------------------
-- user_daily_activity: 0 rows

-- ------------------------------------------------------------
-- Data for `user_memory`
-- ------------------------------------------------------------
INSERT INTO `user_memory` (`id`, `user_id`, `memory_type`, `subject`, `knowledge_point`, `content`, `evidence`, `status`, `create_time`, `update_time`, `is_deleted`) VALUES
  (1, 1, 'weak_point', '待生成', '待生成', 'OCR 导入错题涉及 待生成，可能错因为：概念理解错误、审题错误、规则混淆。建议：先校对 OCR 文本，再选择真实错因并生成同类训练。', 'ocr_mistake:3', 'active', '2026-06-23 15:59:37.013259', '2026-06-23 15:59:37.013259', 0),
  (2, 1, 'weak_point', '待生成', '待生成', 'OCR 导入错题涉及 待生成，可能错因为：概念理解错误、审题错误、规则混淆。建议：先校对 OCR 文本，再选择真实错因并生成同类训练。', 'ocr_mistake:4', 'active', '2026-06-23 15:59:44.927436', '2026-06-23 15:59:44.927436', 0),
  (3, 1, 'weak_point', '待生成', '待生成', 'OCR 导入错题涉及 待生成，需要校对题干并复盘自己的作答过程。', 'ocr_mistake:5', 'active', '2026-06-23 16:13:01.233632', '2026-06-23 16:13:01.233632', 0),
  (4, 1, 'weak_point', '计算机组成原理', '输入输出系统', 'OCR 导入错题涉及 输入输出系统，需要校对题干并复盘自己的作答过程。', 'ocr_mistake:6', 'active', '2026-06-23 16:15:52.368405', '2026-06-23 16:15:52.368405', 0),
  (5, 1, 'weak_point', '计算机组成原理', '输入输出系统', 'OCR 导入错题涉及 输入输出系统，需要校对题干并复盘自己的作答过程。', 'ocr_mistake:7', 'active', '2026-06-23 16:19:19.126039', '2026-06-23 16:19:19.126039', 0),
  (6, 1, 'weak_point', '计算机组成原理', '输入输出系统', 'DMA传输过程中，处理机是空闲的，不占用处理机时间。', 'ocr_mistake:8', 'active', '2026-06-23 16:24:37.352468', '2026-06-23 16:24:37.352468', 0),
  (7, 1, 'weak_point', '计算机组成原理', '输入输出系统', 'DMA传输过程中，处理机时间占用与传输速率和存储周期相关，需要正确计算每个字符的传输时间并乘以每秒传输的字符数。', 'ocr_mistake:9', 'active', '2026-06-23 16:26:48.528391', '2026-06-23 16:26:48.528391', 0),
  (8, 1, 'weak_point', '计算机组成原理', 'DMA与中断方式的时间计算', 'DMA批量传输时间=数据量×存储周期，中断时间=次数×单次开销；9600b/s=1200B/s', 'ocr_mistake:10', 'active', '2026-06-23 16:32:58.506331', '2026-06-23 16:32:58.506331', 0),
  (9, 1, 'weak_point', '操作系统', '页面置换算法', 'LRU缺页次数=初始空载缺页(1次)+置换次数，重复访问同一页面不计缺页', 'ocr_mistake:13', 'active', '2026-06-24 11:52:39.814777', '2026-06-24 11:52:39.814777', 0),
  (10, 1, 'weak_point', '操作系统', '页面置换算法', 'LRU缺页次数=初始全缺页+后续被置换页数，需严格按时间戳淘汰最久未用页', 'ocr_mistake:14', 'active', '2026-06-24 11:56:32.851344', '2026-06-24 11:56:32.851344', 0);

-- ------------------------------------------------------------
-- Data for `user_pending_recommendation`
-- ------------------------------------------------------------
-- user_pending_recommendation: 0 rows

-- ------------------------------------------------------------
-- Data for `user_profile`
-- ------------------------------------------------------------
INSERT INTO `user_profile` (`id`, `user_id`, `target_exam`, `target_date`, `daily_minutes`, `learning_stage`, `long_profile`, `update_time`) VALUES
  (1, 1, '考研 408', '2026-12-19', 90, '强化复习', '偏好结构化解释，适合用错题驱动复习。', '2026-06-24 11:51:26');

-- ------------------------------------------------------------
-- Data for `video_crawl_log`
-- ------------------------------------------------------------
INSERT INTO `video_crawl_log` (`id`, `subject`, `knowledge_point`, `section`, `url`, `platform`, `status`, `crawl_time`, `error_msg`) VALUES
  (1, '数据结构', '绪论', '数据结构的基本概念', 'https://www.bilibili.com/video/BV1tkQgY1Ekx', 'Bilibili', 'success', '2026-06-26 07:30:31.127588', ''),
  (2, '数据结构', '绪论', '数据结构的基本概念', 'https://www.bilibili.com/video/BV13wQqYZEC3', 'Bilibili', 'success', '2026-06-26 07:30:31.131378', ''),
  (3, '数据结构', '绪论', '数据结构的基本概念', 'https://www.bilibili.com/video/BV1xMQdYiEuK', 'Bilibili', 'success', '2026-06-26 07:30:31.131378', ''),
  (4, '数据结构', '绪论', '数据结构的基本概念', 'https://www.bilibili.com/video/BV1UwQdY6EeG', 'Bilibili', 'success', '2026-06-26 07:30:31.133403', ''),
  (5, '数据结构', '绪论', '数据结构的基本概念', 'https://www.bilibili.com/video/BV1si3VzxEJR', 'Bilibili', 'success', '2026-06-26 07:30:31.135416', ''),
  (6, '数据结构', '绪论', '数据结构三要素', 'https://www.bilibili.com/video/BV1De4y1s7wZ', 'Bilibili', 'success', '2026-06-26 07:30:32.312061', ''),
  (7, '数据结构', '绪论', '数据结构三要素', 'https://www.bilibili.com/video/BV1hrsbz5EJU', 'Bilibili', 'success', '2026-06-26 07:30:32.318396', ''),
  (8, '数据结构', '绪论', '数据结构三要素', 'https://www.bilibili.com/video/BV1gN4y1M7vW', 'Bilibili', 'success', '2026-06-26 07:30:32.320411', ''),
  (9, '数据结构', '绪论', '数据结构三要素', 'https://www.bilibili.com/video/BV1MG5xz3Ezb', 'Bilibili', 'success', '2026-06-26 07:30:32.320411', ''),
  (10, '数据结构', '绪论', '数据结构三要素', 'https://www.bilibili.com/video/BV1w3411c7Ug', 'Bilibili', 'success', '2026-06-26 07:30:32.320411', ''),
  (11, '数据结构', '绪论', '算法和算法评价', 'https://www.bilibili.com/video/BV1UU4y1z7hm', 'Bilibili', 'success', '2026-06-26 07:30:33.485211', ''),
  (12, '数据结构', '绪论', '算法和算法评价', 'https://www.bilibili.com/video/BV1ta4y1d7go', 'Bilibili', 'success', '2026-06-26 07:30:33.485211', ''),
  (13, '数据结构', '绪论', '算法和算法评价', 'https://www.bilibili.com/video/BV1jYKfz4EVF', 'Bilibili', 'success', '2026-06-26 07:30:33.485211', ''),
  (14, '数据结构', '绪论', '算法和算法评价', 'https://www.bilibili.com/video/BV1PS4DzKEqi', 'Bilibili', 'success', '2026-06-26 07:30:33.485211', ''),
  (15, '数据结构', '绪论', '算法和算法评价', 'https://www.bilibili.com/video/BV14i4vzfETe', 'Bilibili', 'success', '2026-06-26 07:30:33.485211', ''),
  (16, '数据结构', '线性表', '线性表的定义和基本操作', 'https://www.bilibili.com/video/BV1s3UNYDEnX', 'Bilibili', 'success', '2026-06-26 07:30:34.679759', ''),
  (17, '数据结构', '线性表', '线性表的定义和基本操作', 'https://www.bilibili.com/video/BV1c44y1T7Sw', 'Bilibili', 'success', '2026-06-26 07:30:34.679759', ''),
  (18, '数据结构', '线性表', '线性表的定义和基本操作', 'https://www.bilibili.com/video/BV18eCYBnE3u', 'Bilibili', 'success', '2026-06-26 07:30:34.679759', ''),
  (19, '数据结构', '线性表', '线性表的定义和基本操作', 'https://www.bilibili.com/video/BV1xSqaBfEAT', 'Bilibili', 'success', '2026-06-26 07:30:34.679759', ''),
  (20, '数据结构', '线性表', '线性表的定义和基本操作', 'https://www.bilibili.com/video/BV1sN4y1c7Cn', 'Bilibili', 'success', '2026-06-26 07:30:34.679759', ''),
  (21, '数据结构', '线性表', '顺序表示', 'https://www.bilibili.com/video/BV1g84y1W7Mq', 'Bilibili', 'success', '2026-06-26 07:30:35.864083', ''),
  (22, '数据结构', '线性表', '顺序表示', 'https://www.bilibili.com/video/BV16Ho1YyERW', 'Bilibili', 'success', '2026-06-26 07:30:35.864083', ''),
  (23, '数据结构', '线性表', '顺序表示', 'https://www.bilibili.com/video/BV1tM4y1U7gN', 'Bilibili', 'success', '2026-06-26 07:30:35.864083', ''),
  (24, '数据结构', '线性表', '顺序表示', 'https://www.bilibili.com/video/BV1jRE7z5Eo1', 'Bilibili', 'success', '2026-06-26 07:30:35.864083', ''),
  (25, '数据结构', '线性表', '顺序表示', 'https://www.bilibili.com/video/BV1rHo1YyETL', 'Bilibili', 'success', '2026-06-26 07:30:35.864083', ''),
  (26, '数据结构', '线性表', '链式表示', 'https://www.bilibili.com/video/BV1kWuBzXEZT', 'Bilibili', 'success', '2026-06-26 07:30:37.075577', ''),
  (27, '数据结构', '线性表', '链式表示', 'https://www.bilibili.com/video/BV1Y5udzXEfX', 'Bilibili', 'success', '2026-06-26 07:30:37.076976', ''),
  (28, '数据结构', '线性表', '链式表示', 'https://www.bilibili.com/video/BV1k34y1x7wM', 'Bilibili', 'success', '2026-06-26 07:30:37.078965', ''),
  (29, '数据结构', '线性表', '链式表示', 'https://www.bilibili.com/video/BV1QWoxYrEhf', 'Bilibili', 'success', '2026-06-26 07:30:37.079539', ''),
  (30, '数据结构', '线性表', '链式表示', 'https://www.bilibili.com/video/BV1GWoxYkEKD', 'Bilibili', 'success', '2026-06-26 07:30:37.080533', ''),
  (31, '数据结构', '线性表', '顺序表与链表的比较', 'https://www.bilibili.com/video/BV1z34y1d7JM', 'Bilibili', 'success', '2026-06-26 07:30:38.253270', ''),
  (32, '数据结构', '线性表', '顺序表与链表的比较', 'https://www.bilibili.com/video/BV1RZ42117ed', 'Bilibili', 'success', '2026-06-26 07:30:38.253270', ''),
  (33, '数据结构', '线性表', '顺序表与链表的比较', 'https://www.bilibili.com/video/BV1f24y1m7Ug', 'Bilibili', 'success', '2026-06-26 07:30:38.255285', ''),
  (34, '数据结构', '线性表', '顺序表与链表的比较', 'https://www.bilibili.com/video/BV1dM411C7vR', 'Bilibili', 'success', '2026-06-26 07:30:38.257308', ''),
  (35, '数据结构', '线性表', '顺序表与链表的比较', 'https://www.bilibili.com/video/BV1J8411n7Zk', 'Bilibili', 'success', '2026-06-26 07:30:38.259326', ''),
  (36, '数据结构', '栈、队列和数组', '栈', 'https://www.bilibili.com/video/BV17At5zRECe', 'Bilibili', 'success', '2026-06-26 07:30:39.434314', ''),
  (37, '数据结构', '栈、队列和数组', '栈', 'https://www.bilibili.com/video/BV1tT4nzpEyi', 'Bilibili', 'success', '2026-06-26 07:30:39.434314', ''),
  (38, '数据结构', '栈、队列和数组', '栈', 'https://www.bilibili.com/video/BV1Tr4y1s7Ka', 'Bilibili', 'success', '2026-06-26 07:30:39.434314', ''),
  (39, '数据结构', '栈、队列和数组', '栈', 'https://www.bilibili.com/video/BV1f4oeYrEW6', 'Bilibili', 'success', '2026-06-26 07:30:39.434314', ''),
  (40, '数据结构', '栈、队列和数组', '栈', 'https://www.bilibili.com/video/BV11oZgYoEoN', 'Bilibili', 'success', '2026-06-26 07:30:39.434314', ''),
  (41, '数据结构', '栈、队列和数组', '队列', 'https://www.bilibili.com/video/BV1z4oeYkEEj', 'Bilibili', 'success', '2026-06-26 07:30:40.615364', ''),
  (42, '数据结构', '栈、队列和数组', '队列', 'https://www.bilibili.com/video/BV1kNZ3YHE96', 'Bilibili', 'success', '2026-06-26 07:30:40.617387', ''),
  (43, '数据结构', '栈、队列和数组', '队列', 'https://www.bilibili.com/video/BV1z4oeYkEnF', 'Bilibili', 'success', '2026-06-26 07:30:40.619400', ''),
  (44, '数据结构', '栈、队列和数组', '队列', 'https://www.bilibili.com/video/BV12oZgYoE2u', 'Bilibili', 'success', '2026-06-26 07:30:40.619400', ''),
  (45, '数据结构', '栈、队列和数组', '队列', 'https://www.bilibili.com/video/BV1k26cB3EGa', 'Bilibili', 'success', '2026-06-26 07:30:40.621413', ''),
  (46, '数据结构', '栈、队列和数组', '栈和队列的应用', 'https://www.bilibili.com/video/BV16HHyzaEGx', 'Bilibili', 'success', '2026-06-26 07:30:41.834718', ''),
  (47, '数据结构', '栈、队列和数组', '数组和特殊矩阵', 'https://www.bilibili.com/video/BV1T54y1p7eH', 'Bilibili', 'success', '2026-06-26 07:30:43.003472', ''),
  (48, '数据结构', '栈、队列和数组', '数组和特殊矩阵', 'https://www.bilibili.com/video/BV1ys44zNE1t', 'Bilibili', 'success', '2026-06-26 07:30:43.003472', ''),
  (49, '数据结构', '栈、队列和数组', '数组和特殊矩阵', 'https://www.bilibili.com/video/BV1DWMKzzEkX', 'Bilibili', 'success', '2026-06-26 07:30:43.003472', ''),
  (50, '数据结构', '栈、队列和数组', '数组和特殊矩阵', 'https://www.bilibili.com/video/BV1MKrsBDESZ', 'Bilibili', 'success', '2026-06-26 07:30:43.019158', ''),
  (51, '数据结构', '栈、队列和数组', '数组和特殊矩阵', 'https://www.bilibili.com/video/BV1SULq6FEQ6', 'Bilibili', 'success', '2026-06-26 07:30:43.019158', ''),
  (52, '数据结构', '串', '串的定义和实现', 'https://www.bilibili.com/video/BV1VY4y1v76z', 'Bilibili', 'success', '2026-06-26 07:30:44.229862', ''),
  (53, '数据结构', '串', '串的定义和实现', 'https://www.bilibili.com/video/BV1BM4m1z767', 'Bilibili', 'success', '2026-06-26 07:30:44.230876', ''),
  (54, '数据结构', '串', '串的定义和实现', 'https://www.bilibili.com/video/BV1pBYPzUExL', 'Bilibili', 'success', '2026-06-26 07:30:44.232891', ''),
  (55, '数据结构', '串', '串的定义和实现', 'https://www.bilibili.com/video/BV1ZQRwY7Eah', 'Bilibili', 'success', '2026-06-26 07:30:44.232891', ''),
  (56, '数据结构', '串', '串的定义和实现', 'https://www.bilibili.com/video/BV1Pi7nzcEZ8', 'Bilibili', 'success', '2026-06-26 07:30:44.232891', ''),
  (57, '数据结构', '串', '串的模式匹配', 'https://www.bilibili.com/video/BV1NAMgz6EEX', 'Bilibili', 'success', '2026-06-26 07:30:45.438228', ''),
  (58, '数据结构', '串', '串的模式匹配', 'https://www.bilibili.com/video/BV1CaG4zbELZ', 'Bilibili', 'success', '2026-06-26 07:30:45.438228', ''),
  (59, '数据结构', '串', '串的模式匹配', 'https://www.bilibili.com/video/BV1MF5f6EE8m', 'Bilibili', 'success', '2026-06-26 07:30:45.438228', ''),
  (60, '数据结构', '串', '串的模式匹配', 'https://www.bilibili.com/video/BV1hu411r7gX', 'Bilibili', 'success', '2026-06-26 07:30:45.438228', ''),
  (61, '数据结构', '串', '串的模式匹配', 'https://www.bilibili.com/video/BV1o8hPzTErX', 'Bilibili', 'success', '2026-06-26 07:30:45.438228', ''),
  (62, '数据结构', '树与二叉树', '树的基本概念', 'https://www.bilibili.com/video/BV1QoFDzjELC', 'Bilibili', 'success', '2026-06-26 07:30:46.632397', ''),
  (63, '数据结构', '树与二叉树', '树的基本概念', 'https://www.bilibili.com/video/BV1uioDY6E4y', 'Bilibili', 'success', '2026-06-26 07:30:46.648480', ''),
  (64, '数据结构', '树与二叉树', '树的基本概念', 'https://www.bilibili.com/video/BV1MBoDYuEsf', 'Bilibili', 'success', '2026-06-26 07:30:46.648480', ''),
  (65, '数据结构', '树与二叉树', '树的基本概念', 'https://www.bilibili.com/video/BV1MBoDYuExG', 'Bilibili', 'success', '2026-06-26 07:30:46.648480', ''),
  (66, '数据结构', '树与二叉树', '树的基本概念', 'https://www.bilibili.com/video/BV1MBoDYgEDv', 'Bilibili', 'success', '2026-06-26 07:30:46.648480', ''),
  (67, '数据结构', '树与二叉树', '二叉树的概念', 'https://www.bilibili.com/video/BV1uioDY6EhM', 'Bilibili', 'success', '2026-06-26 07:30:47.843353', ''),
  (68, '数据结构', '树与二叉树', '二叉树的概念', 'https://www.bilibili.com/video/BV1YHZnYaEKd', 'Bilibili', 'success', '2026-06-26 07:30:47.843353', ''),
  (69, '数据结构', '树与二叉树', '二叉树的概念', 'https://www.bilibili.com/video/BV1VHZnYaE5s', 'Bilibili', 'success', '2026-06-26 07:30:47.843353', ''),
  (70, '数据结构', '树与二叉树', '二叉树的概念', 'https://www.bilibili.com/video/BV1MBoDYuEJn', 'Bilibili', 'success', '2026-06-26 07:30:47.843353', ''),
  (71, '数据结构', '树与二叉树', '二叉树的概念', 'https://www.bilibili.com/video/BV1VHZnYaEgk', 'Bilibili', 'success', '2026-06-26 07:30:47.843353', ''),
  (72, '数据结构', '树与二叉树', '二叉树的遍历', 'https://www.bilibili.com/video/BV1zBg2zuE74', 'Bilibili', 'success', '2026-06-26 07:30:49.034689', ''),
  (73, '数据结构', '树与二叉树', '二叉树的遍历', 'https://www.bilibili.com/video/BV1uioDY6EaT', 'Bilibili', 'success', '2026-06-26 07:30:49.034689', ''),
  (74, '数据结构', '树与二叉树', '二叉树的遍历', 'https://www.bilibili.com/video/BV1eT421U7vv', 'Bilibili', 'success', '2026-06-26 07:30:49.050421', ''),
  (75, '数据结构', '树与二叉树', '二叉树的遍历', 'https://www.bilibili.com/video/BV1irN1zSE3s', 'Bilibili', 'success', '2026-06-26 07:30:49.050421', ''),
  (76, '数据结构', '树与二叉树', '二叉树的遍历', 'https://www.bilibili.com/video/BV1RdM4zMEjW', 'Bilibili', 'success', '2026-06-26 07:30:49.050421', ''),
  (77, '数据结构', '树与二叉树', '线索二叉树', 'https://www.bilibili.com/video/BV1xb411A7NV', 'Bilibili', 'success', '2026-06-26 07:30:50.280301', ''),
  (78, '数据结构', '树与二叉树', '线索二叉树', 'https://www.bilibili.com/video/BV1jW2pYUE35', 'Bilibili', 'success', '2026-06-26 07:30:50.284502', ''),
  (79, '数据结构', '树与二叉树', '线索二叉树', 'https://www.bilibili.com/video/BV1J44y1B7Kk', 'Bilibili', 'success', '2026-06-26 07:30:50.287595', ''),
  (80, '数据结构', '树与二叉树', '线索二叉树', 'https://www.bilibili.com/video/BV1q84y1a7Pp', 'Bilibili', 'success', '2026-06-26 07:30:50.289602', ''),
  (81, '数据结构', '树与二叉树', '线索二叉树', 'https://www.bilibili.com/video/BV1bd4y1m7gr', 'Bilibili', 'success', '2026-06-26 07:30:50.290552', ''),
  (82, '数据结构', '树与二叉树', '树、森林', 'https://www.bilibili.com/video/BV1VHZnYaEgt', 'Bilibili', 'success', '2026-06-26 07:30:51.471077', ''),
  (83, '数据结构', '树与二叉树', '树、森林', 'https://www.bilibili.com/video/BV13jm7BpEWW', 'Bilibili', 'success', '2026-06-26 07:30:51.471077', ''),
  (84, '数据结构', '树与二叉树', '树、森林', 'https://www.bilibili.com/video/BV1pKSjYmEkE', 'Bilibili', 'success', '2026-06-26 07:30:51.471077', ''),
  (85, '数据结构', '树与二叉树', '树、森林', 'https://www.bilibili.com/video/BV1nj421Z711', 'Bilibili', 'success', '2026-06-26 07:30:51.471077', ''),
  (86, '数据结构', '树与二叉树', '树、森林', 'https://www.bilibili.com/video/BV1ht421j7DA', 'Bilibili', 'success', '2026-06-26 07:30:51.471077', ''),
  (87, '数据结构', '树与二叉树', '树与二叉树的应用', 'https://www.bilibili.com/video/BV1v64y1W7DW', 'Bilibili', 'success', '2026-06-26 07:30:52.680443', ''),
  (88, '数据结构', '树与二叉树', '树与二叉树的应用', 'https://www.bilibili.com/video/BV1tz4y137Dv', 'Bilibili', 'success', '2026-06-26 07:30:52.680443', ''),
  (89, '数据结构', '树与二叉树', '树与二叉树的应用', 'https://www.bilibili.com/video/BV1bTLx6tEaZ', 'Bilibili', 'success', '2026-06-26 07:30:52.696341', ''),
  (90, '数据结构', '树与二叉树', '树与二叉树的应用', 'https://www.bilibili.com/video/BV1d4Ly64EDC', 'Bilibili', 'success', '2026-06-26 07:30:52.696341', ''),
  (91, '数据结构', '树与二叉树', '树与二叉树的应用', 'https://www.bilibili.com/video/BV1JW2vB2EB7', 'Bilibili', 'success', '2026-06-26 07:30:52.696341', ''),
  (92, '数据结构', '图', '图的基本概念', 'https://www.bilibili.com/video/BV1cdWrz8EEq', 'Bilibili', 'success', '2026-06-26 07:30:53.880351', ''),
  (93, '数据结构', '图', '图的基本概念', 'https://www.bilibili.com/video/BV1DJKWzEEqZ', 'Bilibili', 'success', '2026-06-26 07:30:53.882361', ''),
  (94, '数据结构', '图', '图的基本概念', 'https://www.bilibili.com/video/BV1rPVA65Eyc', 'Bilibili', 'success', '2026-06-26 07:30:53.884371', ''),
  (95, '数据结构', '图', '图的基本概念', 'https://www.bilibili.com/video/BV157VA6vEaa', 'Bilibili', 'success', '2026-06-26 07:30:53.886124', ''),
  (96, '数据结构', '图', '图的基本概念', 'https://www.bilibili.com/video/BV1B2CLBEEyM', 'Bilibili', 'success', '2026-06-26 07:30:53.888135', ''),
  (97, '数据结构', '图', '图的存储及基本操作', 'https://www.bilibili.com/video/BV1Bz4y1L7kr', 'Bilibili', 'success', '2026-06-26 07:30:55.094804', ''),
  (98, '数据结构', '图', '图的存储及基本操作', 'https://www.bilibili.com/video/BV1GS6eBEEFu', 'Bilibili', 'success', '2026-06-26 07:30:55.096817', ''),
  (99, '数据结构', '图', '图的存储及基本操作', 'https://www.bilibili.com/video/BV1YfanzLER4', 'Bilibili', 'success', '2026-06-26 07:30:55.098830', ''),
  (100, '数据结构', '图', '图的存储及基本操作', 'https://www.bilibili.com/video/BV1aqdAY6EAg', 'Bilibili', 'success', '2026-06-26 07:30:55.100843', '');
INSERT INTO `video_crawl_log` (`id`, `subject`, `knowledge_point`, `section`, `url`, `platform`, `status`, `crawl_time`, `error_msg`) VALUES
  (101, '数据结构', '图', '图的遍历', 'https://www.bilibili.com/video/BV1Mf421q7bH', 'Bilibili', 'success', '2026-06-26 07:30:56.294884', ''),
  (102, '数据结构', '图', '图的遍历', 'https://www.bilibili.com/video/BV16nSYBQEdg', 'Bilibili', 'success', '2026-06-26 07:30:56.294884', ''),
  (103, '数据结构', '图', '图的遍历', 'https://www.bilibili.com/video/BV1RGNueWEb1', 'Bilibili', 'success', '2026-06-26 07:30:56.294884', ''),
  (104, '数据结构', '图', '图的遍历', 'https://www.bilibili.com/video/BV1a6dNYjEsX', 'Bilibili', 'success', '2026-06-26 07:30:56.294884', ''),
  (105, '数据结构', '图', '图的遍历', 'https://www.bilibili.com/video/BV1vmdoYYEsD', 'Bilibili', 'success', '2026-06-26 07:30:56.294884', ''),
  (106, '数据结构', '图', '图的应用', 'https://www.bilibili.com/video/BV1Vp4y1E73j', 'Bilibili', 'success', '2026-06-26 07:30:57.487790', ''),
  (107, '数据结构', '图', '图的应用', 'https://www.bilibili.com/video/BV1w8Vb6pE4j', 'Bilibili', 'success', '2026-06-26 07:30:57.487790', ''),
  (108, '数据结构', '图', '图的应用', 'https://www.bilibili.com/video/BV1k1qPYEEpn', 'Bilibili', 'success', '2026-06-26 07:30:57.487790', ''),
  (109, '数据结构', '图', '图的应用', 'https://www.bilibili.com/video/BV1C14y12711', 'Bilibili', 'success', '2026-06-26 07:30:57.503774', ''),
  (110, '数据结构', '图', '图的应用', 'https://www.bilibili.com/video/BV1KQ5kzUENv', 'Bilibili', 'success', '2026-06-26 07:30:57.503774', ''),
  (111, '数据结构', '查找', '查找的基本概念', 'https://www.bilibili.com/video/BV1ETWWzuEsr', 'Bilibili', 'success', '2026-06-26 07:30:58.698206', ''),
  (112, '数据结构', '查找', '查找的基本概念', 'https://www.bilibili.com/video/BV1ChM1zMEic', 'Bilibili', 'success', '2026-06-26 07:30:58.698206', ''),
  (113, '数据结构', '查找', '查找的基本概念', 'https://www.bilibili.com/video/BV1quxfzrEr2', 'Bilibili', 'success', '2026-06-26 07:30:58.698206', ''),
  (114, '数据结构', '查找', '查找的基本概念', 'https://www.bilibili.com/video/BV1ki4JzCEhA', 'Bilibili', 'success', '2026-06-26 07:30:58.698206', ''),
  (115, '数据结构', '查找', '查找的基本概念', 'https://www.bilibili.com/video/BV1Xa411P7XN', 'Bilibili', 'success', '2026-06-26 07:30:58.714383', ''),
  (116, '数据结构', '查找', '顺序查找和折半查找', 'https://www.bilibili.com/video/BV1AkG9zqE3K', 'Bilibili', 'success', '2026-06-26 07:30:59.907452', ''),
  (117, '数据结构', '查找', '顺序查找和折半查找', 'https://www.bilibili.com/video/BV1zYSLYgE8Q', 'Bilibili', 'success', '2026-06-26 07:30:59.907452', ''),
  (118, '数据结构', '查找', '顺序查找和折半查找', 'https://www.bilibili.com/video/BV14HXjBoEDT', 'Bilibili', 'success', '2026-06-26 07:30:59.907452', ''),
  (119, '数据结构', '查找', '顺序查找和折半查找', 'https://www.bilibili.com/video/BV1Ex4y1Q7f4', 'Bilibili', 'success', '2026-06-26 07:30:59.907452', ''),
  (120, '数据结构', '查找', '顺序查找和折半查找', 'https://www.bilibili.com/video/BV1NXquBbE9z', 'Bilibili', 'success', '2026-06-26 07:30:59.907452', ''),
  (121, '数据结构', '查找', '树型查找', 'https://www.bilibili.com/video/BV1mU4y1w7XM', 'Bilibili', 'success', '2026-06-26 07:31:01.130326', ''),
  (122, '数据结构', '查找', '树型查找', 'https://www.bilibili.com/video/BV168sHzzEE1', 'Bilibili', 'success', '2026-06-26 07:31:01.132056', ''),
  (123, '数据结构', '查找', '树型查找', 'https://www.bilibili.com/video/BV1cb4y1T7aV', 'Bilibili', 'success', '2026-06-26 07:31:01.134071', ''),
  (124, '数据结构', '查找', '树型查找', 'https://www.bilibili.com/video/BV1yP41157gV', 'Bilibili', 'success', '2026-06-26 07:31:01.136087', ''),
  (125, '数据结构', '查找', '树型查找', 'https://www.bilibili.com/video/BV1kd4y1d7Tu', 'Bilibili', 'success', '2026-06-26 07:31:01.138101', ''),
  (126, '数据结构', '查找', '散列查找', 'https://www.bilibili.com/video/BV1k7LG65Eh5', 'Bilibili', 'success', '2026-06-26 07:31:02.277498', ''),
  (127, '数据结构', '查找', '散列查找', 'https://www.bilibili.com/video/BV1vA8VzXEBL', 'Bilibili', 'success', '2026-06-26 07:31:02.277498', ''),
  (128, '数据结构', '查找', '散列查找', 'https://www.bilibili.com/video/BV1D2Nde2EWk', 'Bilibili', 'success', '2026-06-26 07:31:02.277498', ''),
  (129, '数据结构', '查找', '散列查找', 'https://www.bilibili.com/video/BV1X2K7ziErK', 'Bilibili', 'success', '2026-06-26 07:31:02.277498', ''),
  (130, '数据结构', '查找', '散列查找', 'https://www.bilibili.com/video/BV1BT4y1P795', 'Bilibili', 'success', '2026-06-26 07:31:02.277498', ''),
  (131, '数据结构', '排序', '排序的基本概念', 'https://www.bilibili.com/video/BV1fxCxBCEEF', 'Bilibili', 'success', '2026-06-26 07:31:03.472333', ''),
  (132, '数据结构', '排序', '排序的基本概念', 'https://www.bilibili.com/video/BV17c41187Us', 'Bilibili', 'success', '2026-06-26 07:31:03.472333', ''),
  (133, '数据结构', '排序', '排序的基本概念', 'https://www.bilibili.com/video/BV1afTrzzEri', 'Bilibili', 'success', '2026-06-26 07:31:03.472333', ''),
  (134, '数据结构', '排序', '排序的基本概念', 'https://www.bilibili.com/video/BV155h2zEEx3', 'Bilibili', 'success', '2026-06-26 07:31:03.472333', ''),
  (135, '数据结构', '排序', '排序的基本概念', 'https://www.bilibili.com/video/BV1dAj7zwEaL', 'Bilibili', 'success', '2026-06-26 07:31:03.472333', ''),
  (136, '数据结构', '排序', '内部排序', 'https://www.bilibili.com/video/BV1iy2aBvE7F', 'Bilibili', 'success', '2026-06-26 07:31:04.626878', ''),
  (137, '数据结构', '排序', '内部排序', 'https://www.bilibili.com/video/BV1XtgozdEoj', 'Bilibili', 'success', '2026-06-26 07:31:04.626878', ''),
  (138, '数据结构', '排序', '内部排序', 'https://www.bilibili.com/video/BV1gEstz3EWi', 'Bilibili', 'success', '2026-06-26 07:31:04.628891', ''),
  (139, '数据结构', '排序', '内部排序', 'https://www.bilibili.com/video/BV1YqKNeyEQr', 'Bilibili', 'success', '2026-06-26 07:31:04.630901', ''),
  (140, '数据结构', '排序', '内部排序', 'https://www.bilibili.com/video/BV1qxK1z9EhD', 'Bilibili', 'success', '2026-06-26 07:31:04.631913', ''),
  (141, '数据结构', '排序', '外部排序', 'https://www.bilibili.com/video/BV1vG4y1G7JL', 'Bilibili', 'success', '2026-06-26 07:31:05.779334', ''),
  (142, '数据结构', '排序', '外部排序', 'https://www.bilibili.com/video/BV1jf4y1i7LQ', 'Bilibili', 'success', '2026-06-26 07:31:05.779334', ''),
  (143, '数据结构', '排序', '外部排序', 'https://www.bilibili.com/video/BV18bEs6NEDJ', 'Bilibili', 'success', '2026-06-26 07:31:05.779334', ''),
  (144, '数据结构', '排序', '外部排序', 'https://www.bilibili.com/video/BV1MX1uYbEA4', 'Bilibili', 'success', '2026-06-26 07:31:05.795315', ''),
  (145, '数据结构', '排序', '外部排序', 'https://www.bilibili.com/video/BV1tYzzYwEt3', 'Bilibili', 'success', '2026-06-26 07:31:05.797906', ''),
  (146, '计算机组成原理', '计算机系统概述', '计算机发展历程', 'https://www.bilibili.com/video/BV1e94y1T75M', 'Bilibili', 'success', '2026-06-26 07:31:06.977731', ''),
  (147, '计算机组成原理', '计算机系统概述', '计算机发展历程', 'https://www.bilibili.com/video/BV1EY4y1K72K', 'Bilibili', 'success', '2026-06-26 07:31:06.979748', ''),
  (148, '计算机组成原理', '计算机系统概述', '计算机发展历程', 'https://www.bilibili.com/video/BV1EK411a74G', 'Bilibili', 'success', '2026-06-26 07:31:06.981764', ''),
  (149, '计算机组成原理', '计算机系统概述', '计算机发展历程', 'https://www.bilibili.com/video/BV1X4yzBVEeP', 'Bilibili', 'success', '2026-06-26 07:31:06.983776', ''),
  (150, '计算机组成原理', '计算机系统概述', '计算机发展历程', 'https://www.bilibili.com/video/BV1Nc2rY7Ecm', 'Bilibili', 'success', '2026-06-26 07:31:06.986135', ''),
  (151, '计算机组成原理', '计算机系统概述', '计算机系统层次结构', 'https://www.bilibili.com/video/BV1J14y147CL', 'Bilibili', 'success', '2026-06-26 07:31:08.162327', ''),
  (152, '计算机组成原理', '计算机系统概述', '计算机系统层次结构', 'https://www.bilibili.com/video/BV14m4y1e7KE', 'Bilibili', 'success', '2026-06-26 07:31:08.168907', ''),
  (153, '计算机组成原理', '计算机系统概述', '计算机系统层次结构', 'https://www.bilibili.com/video/BV1EyX6YSEFb', 'Bilibili', 'success', '2026-06-26 07:31:08.170922', ''),
  (154, '计算机组成原理', '计算机系统概述', '计算机系统层次结构', 'https://www.bilibili.com/video/BV199pzeUE7z', 'Bilibili', 'success', '2026-06-26 07:31:08.170922', ''),
  (155, '计算机组成原理', '计算机系统概述', '计算机系统层次结构', 'https://www.bilibili.com/video/BV1gDrTY7Esi', 'Bilibili', 'success', '2026-06-26 07:31:08.172938', ''),
  (156, '计算机组成原理', '计算机系统概述', '计算机的性能指标', 'https://www.bilibili.com/video/BV1CfdBBQEJa', 'Bilibili', 'success', '2026-06-26 07:31:09.369465', ''),
  (157, '计算机组成原理', '计算机系统概述', '计算机的性能指标', 'https://www.bilibili.com/video/BV1YH4y1W7cL', 'Bilibili', 'success', '2026-06-26 07:31:09.372526', ''),
  (158, '计算机组成原理', '计算机系统概述', '计算机的性能指标', 'https://www.bilibili.com/video/BV1cc4HzjEw2', 'Bilibili', 'success', '2026-06-26 07:31:09.373517', ''),
  (159, '计算机组成原理', '计算机系统概述', '计算机的性能指标', 'https://www.bilibili.com/video/BV1gxAJeBELp', 'Bilibili', 'success', '2026-06-26 07:31:09.375416', ''),
  (160, '计算机组成原理', '计算机系统概述', '计算机的性能指标', 'https://www.bilibili.com/video/BV1wA1CBgEdU', 'Bilibili', 'success', '2026-06-26 07:31:09.375416', ''),
  (161, '计算机组成原理', '数据的表示和运算', '数制与编码', 'https://www.bilibili.com/video/BV1Ed4y1A7iP', 'Bilibili', 'success', '2026-06-26 07:31:10.526308', ''),
  (162, '计算机组成原理', '数据的表示和运算', '数制与编码', 'https://www.bilibili.com/video/BV1W6SUYyEZ9', 'Bilibili', 'success', '2026-06-26 07:31:10.526308', ''),
  (163, '计算机组成原理', '数据的表示和运算', '数制与编码', 'https://www.bilibili.com/video/BV1FH2VYFEAK', 'Bilibili', 'success', '2026-06-26 07:31:10.526308', ''),
  (164, '计算机组成原理', '数据的表示和运算', '数制与编码', 'https://www.bilibili.com/video/BV1og4y127TA', 'Bilibili', 'success', '2026-06-26 07:31:10.526308', ''),
  (165, '计算机组成原理', '数据的表示和运算', '数制与编码', 'https://www.bilibili.com/video/BV1C6yZBjE3v', 'Bilibili', 'success', '2026-06-26 07:31:10.538323', ''),
  (166, '计算机组成原理', '数据的表示和运算', '运算方法和运算电路', 'https://www.bilibili.com/video/BV1FTWqz2EXL', 'Bilibili', 'success', '2026-06-26 07:31:11.715156', ''),
  (167, '计算机组成原理', '数据的表示和运算', '运算方法和运算电路', 'https://www.bilibili.com/video/BV1aCoVYgEtX', 'Bilibili', 'success', '2026-06-26 07:31:11.715156', ''),
  (168, '计算机组成原理', '数据的表示和运算', '运算方法和运算电路', 'https://www.bilibili.com/video/BV1bwEk62ELV', 'Bilibili', 'success', '2026-06-26 07:31:11.715156', ''),
  (169, '计算机组成原理', '数据的表示和运算', '运算方法和运算电路', 'https://www.bilibili.com/video/BV1NueXzoEqp', 'Bilibili', 'success', '2026-06-26 07:31:11.715156', ''),
  (170, '计算机组成原理', '数据的表示和运算', '运算方法和运算电路', 'https://www.bilibili.com/video/BV1mBLQ6AEiR', 'Bilibili', 'success', '2026-06-26 07:31:11.715156', ''),
  (171, '计算机组成原理', '数据的表示和运算', '浮点数的表示与运算', 'https://www.bilibili.com/video/BV1Ks4y1E7qo', 'Bilibili', 'success', '2026-06-26 07:31:12.878356', ''),
  (172, '计算机组成原理', '数据的表示和运算', '浮点数的表示与运算', 'https://www.bilibili.com/video/BV1unVWzPEXP', 'Bilibili', 'success', '2026-06-26 07:31:12.878356', ''),
  (173, '计算机组成原理', '数据的表示和运算', '浮点数的表示与运算', 'https://www.bilibili.com/video/BV14x4y1z78r', 'Bilibili', 'success', '2026-06-26 07:31:12.878356', ''),
  (174, '计算机组成原理', '数据的表示和运算', '浮点数的表示与运算', 'https://www.bilibili.com/video/BV1m6NxzUEB4', 'Bilibili', 'success', '2026-06-26 07:31:12.878356', ''),
  (175, '计算机组成原理', '数据的表示和运算', '浮点数的表示与运算', 'https://www.bilibili.com/video/BV1WaPnzdEkR', 'Bilibili', 'success', '2026-06-26 07:31:12.878356', ''),
  (176, '计算机组成原理', '存储系统', '存储器概述', 'https://www.bilibili.com/video/BV1VG411b7e3', 'Bilibili', 'success', '2026-06-26 07:31:14.040266', ''),
  (177, '计算机组成原理', '存储系统', '存储器概述', 'https://www.bilibili.com/video/BV1Mr4y1Z7Zo', 'Bilibili', 'success', '2026-06-26 07:31:14.040266', ''),
  (178, '计算机组成原理', '存储系统', '存储器概述', 'https://www.bilibili.com/video/BV1yP411W7wW', 'Bilibili', 'success', '2026-06-26 07:31:14.040266', ''),
  (179, '计算机组成原理', '存储系统', '存储器概述', 'https://www.bilibili.com/video/BV1FR4y1E7gN', 'Bilibili', 'success', '2026-06-26 07:31:14.040266', ''),
  (180, '计算机组成原理', '存储系统', '存储器概述', 'https://www.bilibili.com/video/BV1smK3zrEjP', 'Bilibili', 'success', '2026-06-26 07:31:14.040266', ''),
  (181, '计算机组成原理', '存储系统', '主存储器', 'https://www.bilibili.com/video/BV1gW2UYyE5F', 'Bilibili', 'success', '2026-06-26 07:31:15.232623', ''),
  (182, '计算机组成原理', '存储系统', '主存储器', 'https://www.bilibili.com/video/BV1U18tznEBs', 'Bilibili', 'success', '2026-06-26 07:31:15.232623', ''),
  (183, '计算机组成原理', '存储系统', '主存储器', 'https://www.bilibili.com/video/BV1qw411J7MQ', 'Bilibili', 'success', '2026-06-26 07:31:15.248561', ''),
  (184, '计算机组成原理', '存储系统', '主存储器', 'https://www.bilibili.com/video/BV1JzzdYwEbP', 'Bilibili', 'success', '2026-06-26 07:31:15.248561', ''),
  (185, '计算机组成原理', '存储系统', '主存储器', 'https://www.bilibili.com/video/BV19D42177yt', 'Bilibili', 'success', '2026-06-26 07:31:15.248561', ''),
  (186, '计算机组成原理', '存储系统', '主存储器与CPU的连接', 'https://www.bilibili.com/video/BV1dMZLBLE2V', 'Bilibili', 'success', '2026-06-26 07:31:16.442012', ''),
  (187, '计算机组成原理', '存储系统', '外部存储器', 'https://www.bilibili.com/video/BV1tAU1BZEBQ', 'Bilibili', 'success', '2026-06-26 07:31:17.613059', ''),
  (188, '计算机组成原理', '存储系统', '外部存储器', 'https://www.bilibili.com/video/BV1AW1gB2EKk', 'Bilibili', 'success', '2026-06-26 07:31:17.617089', ''),
  (189, '计算机组成原理', '存储系统', '高速缓冲存储器', 'https://www.bilibili.com/video/BV1B6tdz6EwN', 'Bilibili', 'success', '2026-06-26 07:31:18.807191', ''),
  (190, '计算机组成原理', '存储系统', '高速缓冲存储器', 'https://www.bilibili.com/video/BV1S8RZBJE7W', 'Bilibili', 'success', '2026-06-26 07:31:18.807191', ''),
  (191, '计算机组成原理', '存储系统', '虚拟存储器', 'https://www.bilibili.com/video/BV1yRj3zAEbc', 'Bilibili', 'success', '2026-06-26 07:31:19.979312', ''),
  (192, '计算机组成原理', '存储系统', '虚拟存储器', 'https://www.bilibili.com/video/BV1Et411E7D6', 'Bilibili', 'success', '2026-06-26 07:31:19.979312', ''),
  (193, '计算机组成原理', '存储系统', '虚拟存储器', 'https://www.bilibili.com/video/BV1UCmMYaELX', 'Bilibili', 'success', '2026-06-26 07:31:19.993914', ''),
  (194, '计算机组成原理', '指令系统', '指令集体系结构', 'https://www.bilibili.com/video/BV1yn4y1Q7GZ', 'Bilibili', 'success', '2026-06-26 07:31:21.198670', ''),
  (195, '计算机组成原理', '指令系统', '指令集体系结构', 'https://www.bilibili.com/video/BV1VVEF6uEvp', 'Bilibili', 'success', '2026-06-26 07:31:21.200681', ''),
  (196, '计算机组成原理', '指令系统', '指令集体系结构', 'https://www.bilibili.com/video/BV16bu4zDEdm', 'Bilibili', 'success', '2026-06-26 07:31:21.201689', ''),
  (197, '计算机组成原理', '指令系统', '指令集体系结构', 'https://www.bilibili.com/video/BV17MA7eGEgW', 'Bilibili', 'success', '2026-06-26 07:31:21.201689', ''),
  (198, '计算机组成原理', '指令系统', '指令集体系结构', 'https://www.bilibili.com/video/BV1sFRsYpEVW', 'Bilibili', 'success', '2026-06-26 07:31:21.205111', ''),
  (199, '计算机组成原理', '指令系统', '寻址方式', 'https://www.bilibili.com/video/BV1tq4y1z78E', 'Bilibili', 'success', '2026-06-26 07:31:22.331533', ''),
  (200, '计算机组成原理', '指令系统', '寻址方式', 'https://www.bilibili.com/video/BV1ZN41127UB', 'Bilibili', 'success', '2026-06-26 07:31:22.331533', '');
INSERT INTO `video_crawl_log` (`id`, `subject`, `knowledge_point`, `section`, `url`, `platform`, `status`, `crawl_time`, `error_msg`) VALUES
  (201, '计算机组成原理', '指令系统', '寻址方式', 'https://www.bilibili.com/video/BV1zg28YrEdw', 'Bilibili', 'success', '2026-06-26 07:31:22.331533', ''),
  (202, '计算机组成原理', '指令系统', '寻址方式', 'https://www.bilibili.com/video/BV12PtmzAEvb', 'Bilibili', 'success', '2026-06-26 07:31:22.331533', ''),
  (203, '计算机组成原理', '指令系统', '寻址方式', 'https://www.bilibili.com/video/BV1dukXBLEVh', 'Bilibili', 'success', '2026-06-26 07:31:22.331533', ''),
  (204, '计算机组成原理', '指令系统', '程序的机器级代码表示', 'https://www.bilibili.com/video/BV1e5USY4E2R', 'Bilibili', 'success', '2026-06-26 07:31:23.548238', ''),
  (205, '计算机组成原理', '指令系统', '程序的机器级代码表示', 'https://www.bilibili.com/video/BV12q1aBjEAN', 'Bilibili', 'success', '2026-06-26 07:31:23.549900', ''),
  (206, '计算机组成原理', '指令系统', '程序的机器级代码表示', 'https://www.bilibili.com/video/BV1pSBeBhEoR', 'Bilibili', 'success', '2026-06-26 07:31:23.551557', ''),
  (207, '计算机组成原理', '指令系统', '程序的机器级代码表示', 'https://www.bilibili.com/video/BV1A9p4ewEJR', 'Bilibili', 'success', '2026-06-26 07:31:23.553215', ''),
  (208, '计算机组成原理', '指令系统', '程序的机器级代码表示', 'https://www.bilibili.com/video/BV1FX4y1E7kR', 'Bilibili', 'success', '2026-06-26 07:31:23.554869', ''),
  (209, '计算机组成原理', '指令系统', 'CISC和RISC的基本概念', 'https://www.bilibili.com/video/BV1Ex4y1B7sv', 'Bilibili', 'success', '2026-06-26 07:31:24.688769', ''),
  (210, '计算机组成原理', '指令系统', 'CISC和RISC的基本概念', 'https://www.bilibili.com/video/BV1YFumzcEtp', 'Bilibili', 'success', '2026-06-26 07:31:24.688769', ''),
  (211, '计算机组成原理', '指令系统', 'CISC和RISC的基本概念', 'https://www.bilibili.com/video/BV1BHYserEn1', 'Bilibili', 'success', '2026-06-26 07:31:24.702377', ''),
  (212, '计算机组成原理', '指令系统', 'CISC和RISC的基本概念', 'https://www.bilibili.com/video/BV19pPLztERJ', 'Bilibili', 'success', '2026-06-26 07:31:24.704430', ''),
  (213, '计算机组成原理', '指令系统', 'CISC和RISC的基本概念', 'https://www.bilibili.com/video/BV1EYpFzgE48', 'Bilibili', 'success', '2026-06-26 07:31:24.704430', ''),
  (214, '计算机组成原理', '中央处理器', 'CPU的功能和基本结构', 'https://www.bilibili.com/video/BV1cu4y1S7HR', 'Bilibili', 'success', '2026-06-26 07:31:25.905404', ''),
  (215, '计算机组成原理', '中央处理器', 'CPU的功能和基本结构', 'https://www.bilibili.com/video/BV1M1421z72p', 'Bilibili', 'success', '2026-06-26 07:31:25.905404', ''),
  (216, '计算机组成原理', '中央处理器', 'CPU的功能和基本结构', 'https://www.bilibili.com/video/BV1mf4y1E7ad', 'Bilibili', 'success', '2026-06-26 07:31:25.905404', ''),
  (217, '计算机组成原理', '中央处理器', 'CPU的功能和基本结构', 'https://www.bilibili.com/video/BV1x7421f7HZ', 'Bilibili', 'success', '2026-06-26 07:31:25.913155', ''),
  (218, '计算机组成原理', '中央处理器', 'CPU的功能和基本结构', 'https://www.bilibili.com/video/BV18QqxY9E5T', 'Bilibili', 'success', '2026-06-26 07:31:25.913155', ''),
  (219, '计算机组成原理', '中央处理器', '指令执行过程', 'https://www.bilibili.com/video/BV1pAsez1Emm', 'Bilibili', 'success', '2026-06-26 07:31:27.092064', ''),
  (220, '计算机组成原理', '中央处理器', '指令执行过程', 'https://www.bilibili.com/video/BV1PD8zz2ESP', 'Bilibili', 'success', '2026-06-26 07:31:27.092064', ''),
  (221, '计算机组成原理', '中央处理器', '数据通路的功能和基本结构', 'https://www.bilibili.com/video/BV16Z4y197Vr', 'Bilibili', 'success', '2026-06-26 07:31:28.253283', ''),
  (222, '计算机组成原理', '中央处理器', '数据通路的功能和基本结构', 'https://www.bilibili.com/video/BV1VUNszsEig', 'Bilibili', 'success', '2026-06-26 07:31:28.253283', ''),
  (223, '计算机组成原理', '中央处理器', '数据通路的功能和基本结构', 'https://www.bilibili.com/video/BV1aajU6YEGm', 'Bilibili', 'success', '2026-06-26 07:31:28.260358', ''),
  (224, '计算机组成原理', '中央处理器', '数据通路的功能和基本结构', 'https://www.bilibili.com/video/BV1YgxCzdEvq', 'Bilibili', 'success', '2026-06-26 07:31:28.262372', ''),
  (225, '计算机组成原理', '中央处理器', '数据通路的功能和基本结构', 'https://www.bilibili.com/video/BV1yBiKB7E9Z', 'Bilibili', 'success', '2026-06-26 07:31:28.264384', ''),
  (226, '计算机组成原理', '中央处理器', '控制器的功能和工作原理', NULL, 'Bilibili', 'failed', '2026-06-26 07:31:29.481832', 'no video found even with fallback search'),
  (227, '计算机组成原理', '中央处理器', '异常和中断机制', NULL, 'Bilibili', 'failed', '2026-06-26 07:31:30.686254', 'no video found even with fallback search'),
  (228, '计算机组成原理', '中央处理器', '指令流水线', 'https://www.bilibili.com/video/BV1Tx4y1a7zm', 'Bilibili', 'success', '2026-06-26 07:31:31.864851', ''),
  (229, '计算机组成原理', '中央处理器', '指令流水线', 'https://www.bilibili.com/video/BV18k4y1p7dA', 'Bilibili', 'success', '2026-06-26 07:31:31.864851', ''),
  (230, '计算机组成原理', '中央处理器', '指令流水线', 'https://www.bilibili.com/video/BV1x9yVBfEXU', 'Bilibili', 'success', '2026-06-26 07:31:31.880717', ''),
  (231, '计算机组成原理', '中央处理器', '指令流水线', 'https://www.bilibili.com/video/BV1jFzQYVEeV', 'Bilibili', 'success', '2026-06-26 07:31:31.880717', ''),
  (232, '计算机组成原理', '中央处理器', '指令流水线', 'https://www.bilibili.com/video/BV1zHenztEmu', 'Bilibili', 'success', '2026-06-26 07:31:31.880717', ''),
  (233, '计算机组成原理', '总线', '总线概述', 'https://www.bilibili.com/video/BV1Lr421x7TK', 'Bilibili', 'success', '2026-06-26 07:31:33.075348', ''),
  (234, '计算机组成原理', '总线', '总线概述', 'https://www.bilibili.com/video/BV172X6YEEYP', 'Bilibili', 'success', '2026-06-26 07:31:33.075348', ''),
  (235, '计算机组成原理', '总线', '总线概述', 'https://www.bilibili.com/video/BV17yX6YSE9j', 'Bilibili', 'success', '2026-06-26 07:31:33.075348', ''),
  (236, '计算机组成原理', '总线', '总线概述', 'https://www.bilibili.com/video/BV1Dk4y1T76F', 'Bilibili', 'success', '2026-06-26 07:31:33.075348', ''),
  (237, '计算机组成原理', '总线', '总线仲裁', 'https://www.bilibili.com/video/BV1QP4y1n7j6', 'Bilibili', 'success', '2026-06-26 07:31:34.233256', ''),
  (238, '计算机组成原理', '总线', '总线仲裁', 'https://www.bilibili.com/video/BV1DU4y1v7DK', 'Bilibili', 'success', '2026-06-26 07:31:34.233256', ''),
  (239, '计算机组成原理', '总线', '总线操作和定时', 'https://www.bilibili.com/video/BV1Mni2YkEx4', 'Bilibili', 'success', '2026-06-26 07:31:35.443884', ''),
  (240, '计算机组成原理', '总线', '总线操作和定时', 'https://www.bilibili.com/video/BV1JeGVzDETs', 'Bilibili', 'success', '2026-06-26 07:31:35.445901', ''),
  (241, '计算机组成原理', '总线', '总线操作和定时', 'https://www.bilibili.com/video/BV1qm1UByEGy', 'Bilibili', 'success', '2026-06-26 07:31:35.445901', ''),
  (242, '计算机组成原理', '总线', '总线操作和定时', 'https://www.bilibili.com/video/BV1LBje6AE8V', 'Bilibili', 'success', '2026-06-26 07:31:35.445901', ''),
  (243, '计算机组成原理', '总线', '总线操作和定时', 'https://www.bilibili.com/video/BV13wjC6UEHS', 'Bilibili', 'success', '2026-06-26 07:31:35.445901', ''),
  (244, '计算机组成原理', '总线', '总线标准', 'https://www.bilibili.com/video/BV1Aw4m1D7cS', 'Bilibili', 'success', '2026-06-26 07:31:36.639879', ''),
  (245, '计算机组成原理', '输入输出系统', 'I/O系统概述', 'https://www.bilibili.com/video/BV1U94izKEG9', 'Bilibili', 'success', '2026-06-26 07:31:37.817366', ''),
  (246, '计算机组成原理', '输入输出系统', 'I/O系统概述', 'https://www.bilibili.com/video/BV1MXewzsEtf', 'Bilibili', 'success', '2026-06-26 07:31:37.817366', ''),
  (247, '计算机组成原理', '输入输出系统', 'I/O系统概述', 'https://www.bilibili.com/video/BV1kzpEeBEco', 'Bilibili', 'success', '2026-06-26 07:31:37.831092', ''),
  (248, '计算机组成原理', '输入输出系统', 'I/O系统概述', 'https://www.bilibili.com/video/BV1QTyTY4Ezp', 'Bilibili', 'success', '2026-06-26 07:31:37.833111', ''),
  (249, '计算机组成原理', '输入输出系统', 'I/O系统概述', 'https://www.bilibili.com/video/BV1dG411v7no', 'Bilibili', 'success', '2026-06-26 07:31:37.833111', ''),
  (250, '计算机组成原理', '输入输出系统', '外部设备', 'https://www.bilibili.com/video/BV1Tj411U7wn', 'Bilibili', 'success', '2026-06-26 07:31:38.995005', ''),
  (251, '计算机组成原理', '输入输出系统', 'I/O控制方式', 'https://www.bilibili.com/video/BV1qw411271W', 'Bilibili', 'success', '2026-06-26 07:31:40.172434', ''),
  (252, '计算机组成原理', '输入输出系统', 'I/O控制方式', 'https://www.bilibili.com/video/BV1WH3TzrER8', 'Bilibili', 'success', '2026-06-26 07:31:40.172434', ''),
  (253, '计算机组成原理', '输入输出系统', 'I/O控制方式', 'https://www.bilibili.com/video/BV1sduezLEqj', 'Bilibili', 'success', '2026-06-26 07:31:40.172434', ''),
  (254, '计算机组成原理', '输入输出系统', 'I/O控制方式', 'https://www.bilibili.com/video/BV1bCRrBiET9', 'Bilibili', 'success', '2026-06-26 07:31:40.172434', ''),
  (255, '计算机组成原理', '输入输出系统', 'I/O控制方式', 'https://www.bilibili.com/video/BV1Nn4izfEa2', 'Bilibili', 'success', '2026-06-26 07:31:40.172434', ''),
  (256, '计算机组成原理', '输入输出系统', '中断机制', 'https://www.bilibili.com/video/BV19p421X7Pj', 'Bilibili', 'success', '2026-06-26 07:31:41.330830', ''),
  (257, '计算机组成原理', '输入输出系统', 'DMA方式', 'https://www.bilibili.com/video/BV1Ks421A7Lr', 'Bilibili', 'success', '2026-06-26 07:31:42.763211', ''),
  (258, '计算机组成原理', '输入输出系统', 'DMA方式', 'https://www.bilibili.com/video/BV1RG4y1N7dT', 'Bilibili', 'success', '2026-06-26 07:31:42.765260', ''),
  (259, '计算机组成原理', '输入输出系统', '通道方式', 'https://www.bilibili.com/video/BV13jbXzWENC', 'Bilibili', 'success', '2026-06-26 07:31:43.958669', ''),
  (260, '计算机组成原理', '输入输出系统', '通道方式', 'https://www.bilibili.com/video/BV1S1trehE7q', 'Bilibili', 'success', '2026-06-26 07:31:43.961036', ''),
  (261, '计算机组成原理', '输入输出系统', '通道方式', 'https://www.bilibili.com/video/BV12Z421T7b8', 'Bilibili', 'success', '2026-06-26 07:31:43.961036', ''),
  (262, '计算机组成原理', '输入输出系统', '通道方式', 'https://www.bilibili.com/video/BV1qy411e7RY', 'Bilibili', 'success', '2026-06-26 07:31:43.961036', ''),
  (263, '操作系统', '计算机系统概述', '操作系统的基本概念', 'https://www.bilibili.com/video/BV1augczaE4A', 'Bilibili', 'success', '2026-06-26 07:31:45.137112', ''),
  (264, '操作系统', '计算机系统概述', '操作系统的基本概念', 'https://www.bilibili.com/video/BV1DuXvBmEKF', 'Bilibili', 'success', '2026-06-26 07:31:45.149136', ''),
  (265, '操作系统', '计算机系统概述', '操作系统发展历程', 'https://www.bilibili.com/video/BV1584y1C7yr', 'Bilibili', 'success', '2026-06-26 07:31:46.333439', ''),
  (266, '操作系统', '计算机系统概述', '操作系统发展历程', 'https://www.bilibili.com/video/BV1fWx4eaE9g', 'Bilibili', 'success', '2026-06-26 07:31:46.333439', ''),
  (267, '操作系统', '计算机系统概述', '操作系统发展历程', 'https://www.bilibili.com/video/BV1iwDwB4EbS', 'Bilibili', 'success', '2026-06-26 07:31:46.354313', ''),
  (268, '操作系统', '计算机系统概述', '操作系统的运行环境', 'https://www.bilibili.com/video/BV17vsHzKEGG', 'Bilibili', 'success', '2026-06-26 07:31:47.550260', ''),
  (269, '操作系统', '计算机系统概述', '操作系统的运行环境', 'https://www.bilibili.com/video/BV1q9BEBkED9', 'Bilibili', 'success', '2026-06-26 07:31:47.554830', ''),
  (270, '操作系统', '计算机系统概述', '操作系统的运行环境', 'https://www.bilibili.com/video/BV1JA4m1c7f3', 'Bilibili', 'success', '2026-06-26 07:31:47.554830', ''),
  (271, '操作系统', '计算机系统概述', '操作系统的运行环境', 'https://www.bilibili.com/video/BV1P24y1m7ja', 'Bilibili', 'success', '2026-06-26 07:31:47.560154', ''),
  (272, '操作系统', '计算机系统概述', '操作系统的运行环境', 'https://www.bilibili.com/video/BV1Z7UHYDEPV', 'Bilibili', 'success', '2026-06-26 07:31:47.560154', ''),
  (273, '操作系统', '计算机系统概述', '操作系统结构', 'https://www.bilibili.com/video/BV1V5nqzcErH', 'Bilibili', 'success', '2026-06-26 07:31:48.719751', ''),
  (274, '操作系统', '计算机系统概述', '操作系统结构', 'https://www.bilibili.com/video/BV1ku411E7HK', 'Bilibili', 'success', '2026-06-26 07:31:48.719751', ''),
  (275, '操作系统', '计算机系统概述', '操作系统结构', 'https://www.bilibili.com/video/BV1N14y127Mi', 'Bilibili', 'success', '2026-06-26 07:31:48.719751', ''),
  (276, '操作系统', '计算机系统概述', '操作系统结构', 'https://www.bilibili.com/video/BV1bF411X7fm', 'Bilibili', 'success', '2026-06-26 07:31:48.719751', ''),
  (277, '操作系统', '计算机系统概述', '操作系统结构', 'https://www.bilibili.com/video/BV1ZuqGBsETv', 'Bilibili', 'success', '2026-06-26 07:31:48.719751', ''),
  (278, '操作系统', '计算机系统概述', '操作系统引导', 'https://www.bilibili.com/video/BV1R14y1q7eE', 'Bilibili', 'success', '2026-06-26 07:31:49.898203', ''),
  (279, '操作系统', '计算机系统概述', '操作系统引导', 'https://www.bilibili.com/video/BV1ovsHzNEkK', 'Bilibili', 'success', '2026-06-26 07:31:49.898203', ''),
  (280, '操作系统', '计算机系统概述', '操作系统引导', 'https://www.bilibili.com/video/BV17fTLzCEbQ', 'Bilibili', 'success', '2026-06-26 07:31:49.898203', ''),
  (281, '操作系统', '计算机系统概述', '操作系统引导', 'https://www.bilibili.com/video/BV1Uh4y1F7CP', 'Bilibili', 'success', '2026-06-26 07:31:49.898203', ''),
  (282, '操作系统', '计算机系统概述', '操作系统引导', 'https://www.bilibili.com/video/BV1hX4y1x73W', 'Bilibili', 'success', '2026-06-26 07:31:49.898203', ''),
  (283, '操作系统', '计算机系统概述', '虚拟机', 'https://www.bilibili.com/video/BV1FT8kzCEBb', 'Bilibili', 'success', '2026-06-26 07:31:51.062430', ''),
  (284, '操作系统', '计算机系统概述', '虚拟机', 'https://www.bilibili.com/video/BV1PUkBBpEjW', 'Bilibili', 'success', '2026-06-26 07:31:51.062430', ''),
  (285, '操作系统', '计算机系统概述', '虚拟机', 'https://www.bilibili.com/video/BV1Bw4m1C7XW', 'Bilibili', 'success', '2026-06-26 07:31:51.062430', ''),
  (286, '操作系统', '计算机系统概述', '本章疑难点', 'https://www.bilibili.com/video/BV1Ry421q7EA', 'Bilibili', 'success', '2026-06-26 07:31:52.269656', ''),
  (287, '操作系统', '计算机系统概述', '本章疑难点', 'https://www.bilibili.com/video/BV1YG4y137vs', 'Bilibili', 'success', '2026-06-26 07:31:52.269656', ''),
  (288, '操作系统', '计算机系统概述', '本章疑难点', 'https://www.bilibili.com/video/BV1zWSgBnEEn', 'Bilibili', 'success', '2026-06-26 07:31:52.269656', ''),
  (289, '操作系统', '计算机系统概述', '本章疑难点', 'https://www.bilibili.com/video/BV1H2421P7PP', 'Bilibili', 'success', '2026-06-26 07:31:52.269656', ''),
  (290, '操作系统', '计算机系统概述', '本章疑难点', 'https://www.bilibili.com/video/BV17A4m1P7oN', 'Bilibili', 'success', '2026-06-26 07:31:52.269656', ''),
  (291, '操作系统', '进程与线程', '进程与线程简介', 'https://www.bilibili.com/video/BV1ATuUzLEgF', 'Bilibili', 'success', '2026-06-26 07:31:53.464496', ''),
  (292, '操作系统', '进程与线程', '进程与线程简介', 'https://www.bilibili.com/video/BV1WN1wBoE7a', 'Bilibili', 'success', '2026-06-26 07:31:53.466513', ''),
  (293, '操作系统', '进程与线程', '进程与线程简介', 'https://www.bilibili.com/video/BV1RW4y1x7fT', 'Bilibili', 'success', '2026-06-26 07:31:53.468575', ''),
  (294, '操作系统', '进程与线程', '进程与线程简介', 'https://www.bilibili.com/video/BV1hdg5zqEdg', 'Bilibili', 'success', '2026-06-26 07:31:53.468575', ''),
  (295, '操作系统', '进程与线程', '进程与线程简介', 'https://www.bilibili.com/video/BV1FVkmBMELf', 'Bilibili', 'success', '2026-06-26 07:31:53.468575', ''),
  (296, '操作系统', '进程与线程', 'CPU调度', 'https://www.bilibili.com/video/BV1LNgvzAEpp', 'Bilibili', 'success', '2026-06-26 07:31:54.632341', ''),
  (297, '操作系统', '进程与线程', 'CPU调度', 'https://www.bilibili.com/video/BV1J72oYDECZ', 'Bilibili', 'success', '2026-06-26 07:31:54.632341', ''),
  (298, '操作系统', '进程与线程', 'CPU调度', 'https://www.bilibili.com/video/BV1NstVeGEex', 'Bilibili', 'success', '2026-06-26 07:31:54.637810', ''),
  (299, '操作系统', '进程与线程', 'CPU调度', 'https://www.bilibili.com/video/BV18pdqBtEBx', 'Bilibili', 'success', '2026-06-26 07:31:54.639553', ''),
  (300, '操作系统', '进程与线程', 'CPU调度', 'https://www.bilibili.com/video/BV1S81dYfEMR', 'Bilibili', 'success', '2026-06-26 07:31:54.643576', '');
INSERT INTO `video_crawl_log` (`id`, `subject`, `knowledge_point`, `section`, `url`, `platform`, `status`, `crawl_time`, `error_msg`) VALUES
  (301, '操作系统', '进程与线程', '同步与互斥', 'https://www.bilibili.com/video/BV1kwqmYqEjw', 'Bilibili', 'success', '2026-06-26 07:31:55.802884', ''),
  (302, '操作系统', '进程与线程', '同步与互斥', 'https://www.bilibili.com/video/BV1XkBuYSEwm', 'Bilibili', 'success', '2026-06-26 07:31:55.802884', ''),
  (303, '操作系统', '进程与线程', '同步与互斥', 'https://www.bilibili.com/video/BV1UCDAB7EcB', 'Bilibili', 'success', '2026-06-26 07:31:55.802884', ''),
  (304, '操作系统', '进程与线程', '同步与互斥', 'https://www.bilibili.com/video/BV1Vc1gBaEZX', 'Bilibili', 'success', '2026-06-26 07:31:55.802884', ''),
  (305, '操作系统', '进程与线程', '同步与互斥', 'https://www.bilibili.com/video/BV19RGJz8EyG', 'Bilibili', 'success', '2026-06-26 07:31:55.802884', ''),
  (306, '操作系统', '进程与线程', '死锁', 'https://www.bilibili.com/video/BV18x4y147AG', 'Bilibili', 'success', '2026-06-26 07:31:56.982726', ''),
  (307, '操作系统', '进程与线程', '死锁', 'https://www.bilibili.com/video/BV1Hg8cz8Esn', 'Bilibili', 'success', '2026-06-26 07:31:56.982726', ''),
  (308, '操作系统', '进程与线程', '死锁', 'https://www.bilibili.com/video/BV1Cs4y117AT', 'Bilibili', 'success', '2026-06-26 07:31:56.982726', ''),
  (309, '操作系统', '进程与线程', '死锁', 'https://www.bilibili.com/video/BV1J1YSzrEHw', 'Bilibili', 'success', '2026-06-26 07:31:56.982726', ''),
  (310, '操作系统', '进程与线程', '死锁', 'https://www.bilibili.com/video/BV11w411z75G', 'Bilibili', 'success', '2026-06-26 07:31:56.982726', ''),
  (311, '操作系统', '内存管理', '内存管理概念', 'https://www.bilibili.com/video/BV1zh4y1i7iD', 'Bilibili', 'success', '2026-06-26 07:31:58.140881', ''),
  (312, '操作系统', '内存管理', '内存管理概念', 'https://www.bilibili.com/video/BV17r6NYQE4h', 'Bilibili', 'success', '2026-06-26 07:31:58.140881', ''),
  (313, '操作系统', '内存管理', '内存管理概念', 'https://www.bilibili.com/video/BV1j9XyYFEem', 'Bilibili', 'success', '2026-06-26 07:31:58.140881', ''),
  (314, '操作系统', '内存管理', '内存管理概念', 'https://www.bilibili.com/video/BV1i84y1y7Kc', 'Bilibili', 'success', '2026-06-26 07:31:58.140881', ''),
  (315, '操作系统', '内存管理', '内存管理概念', 'https://www.bilibili.com/video/BV1aw411b7LX', 'Bilibili', 'success', '2026-06-26 07:31:58.140881', ''),
  (316, '操作系统', '内存管理', '虚拟内存管理', 'https://www.bilibili.com/video/BV1pZ17BiEnA', 'Bilibili', 'success', '2026-06-26 07:31:59.304866', ''),
  (317, '操作系统', '内存管理', '虚拟内存管理', 'https://www.bilibili.com/video/BV1S14y1H7qq', 'Bilibili', 'success', '2026-06-26 07:31:59.304866', ''),
  (318, '操作系统', '文件管理', '文件系统基础', 'https://www.bilibili.com/video/BV1FN2iBUEEM', 'Bilibili', 'success', '2026-06-26 07:32:00.501137', ''),
  (319, '操作系统', '文件管理', '文件系统基础', 'https://www.bilibili.com/video/BV1j84y1f7st', 'Bilibili', 'success', '2026-06-26 07:32:00.503154', ''),
  (320, '操作系统', '文件管理', '文件系统基础', 'https://www.bilibili.com/video/BV1fT4Hz3E1P', 'Bilibili', 'success', '2026-06-26 07:32:00.505169', ''),
  (321, '操作系统', '文件管理', '文件系统基础', 'https://www.bilibili.com/video/BV1q9XyYFEyb', 'Bilibili', 'success', '2026-06-26 07:32:00.509195', ''),
  (322, '操作系统', '文件管理', '文件系统基础', 'https://www.bilibili.com/video/BV1bcmMYwEih', 'Bilibili', 'success', '2026-06-26 07:32:00.509195', ''),
  (323, '操作系统', '文件管理', '目录与文件', 'https://www.bilibili.com/video/BV1Jm421V7e7', 'Bilibili', 'success', '2026-06-26 07:32:01.693457', ''),
  (324, '操作系统', '文件管理', '目录与文件', 'https://www.bilibili.com/video/BV1De411d7NG', 'Bilibili', 'success', '2026-06-26 07:32:01.695441', ''),
  (325, '操作系统', '文件管理', '目录与文件', 'https://www.bilibili.com/video/BV1cC4y1X7Ev', 'Bilibili', 'success', '2026-06-26 07:32:01.697441', ''),
  (326, '操作系统', '文件管理', '目录与文件', 'https://www.bilibili.com/video/BV17KH1zaEXb', 'Bilibili', 'success', '2026-06-26 07:32:01.699052', ''),
  (327, '操作系统', '文件管理', '文件系统', 'https://www.bilibili.com/video/BV1Zk1xBUEKC', 'Bilibili', 'success', '2026-06-26 07:32:03.139844', ''),
  (328, '操作系统', '输入输出管理', 'I/O管理概述', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:04.352225', 'no video found even with fallback search'),
  (329, '操作系统', '输入输出管理', '设备独立性软件', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:05.519809', 'no video found even with fallback search'),
  (330, '操作系统', '输入输出管理', '磁盘和固态硬盘', 'https://www.bilibili.com/video/BV1tb411f7Sm', 'Bilibili', 'success', '2026-06-26 07:32:06.681218', ''),
  (331, '操作系统', '输入输出管理', '磁盘和固态硬盘', 'https://www.bilibili.com/video/BV1N146eUENZ', 'Bilibili', 'success', '2026-06-26 07:32:06.681218', ''),
  (332, '操作系统', '输入输出管理', '磁盘和固态硬盘', 'https://www.bilibili.com/video/BV1Wf421D7cx', 'Bilibili', 'success', '2026-06-26 07:32:06.681218', ''),
  (333, '操作系统', '输入输出管理', '磁盘和固态硬盘', 'https://www.bilibili.com/video/BV1nw9tY9EY1', 'Bilibili', 'success', '2026-06-26 07:32:06.681218', ''),
  (334, '计算机网络', '计算机网络体系结构', '计算机网络概述', 'https://www.bilibili.com/video/BV1bdh9zYEob', 'Bilibili', 'success', '2026-06-26 07:32:07.858207', ''),
  (335, '计算机网络', '计算机网络体系结构', '计算机网络概述', 'https://www.bilibili.com/video/BV1iNxozqEd2', 'Bilibili', 'success', '2026-06-26 07:32:07.858207', ''),
  (336, '计算机网络', '计算机网络体系结构', '计算机网络概述', 'https://www.bilibili.com/video/BV19ZmkB8EHR', 'Bilibili', 'success', '2026-06-26 07:32:07.858207', ''),
  (337, '计算机网络', '计算机网络体系结构', '计算机网络概述', 'https://www.bilibili.com/video/BV1LS23BrESn', 'Bilibili', 'success', '2026-06-26 07:32:07.858207', ''),
  (338, '计算机网络', '计算机网络体系结构', '计算机网络概述', 'https://www.bilibili.com/video/BV19d2oBPE9D', 'Bilibili', 'success', '2026-06-26 07:32:07.858207', ''),
  (339, '计算机网络', '计算机网络体系结构', '计算机网络体系结构与参考模型', 'https://www.bilibili.com/video/BV1cdYyz8EXX', 'Bilibili', 'success', '2026-06-26 07:32:09.021584', ''),
  (340, '计算机网络', '计算机网络体系结构', '计算机网络体系结构与参考模型', 'https://www.bilibili.com/video/BV1XZ421T7fR', 'Bilibili', 'success', '2026-06-26 07:32:09.037540', ''),
  (341, '计算机网络', '计算机网络体系结构', '计算机网络体系结构与参考模型', 'https://www.bilibili.com/video/BV1ASUnBnEBW', 'Bilibili', 'success', '2026-06-26 07:32:09.037540', ''),
  (342, '计算机网络', '计算机网络体系结构', '计算机网络体系结构与参考模型', 'https://www.bilibili.com/video/BV1ZHXzY1EGa', 'Bilibili', 'success', '2026-06-26 07:32:09.037540', ''),
  (343, '计算机网络', '物理层', '通信基础', 'https://www.bilibili.com/video/BV1TwpUzdEBi', 'Bilibili', 'success', '2026-06-26 07:32:10.215570', ''),
  (344, '计算机网络', '物理层', '通信基础', 'https://www.bilibili.com/video/BV1hPJCzuESR', 'Bilibili', 'success', '2026-06-26 07:32:10.215570', ''),
  (345, '计算机网络', '物理层', '通信基础', 'https://www.bilibili.com/video/BV1yr421s7rS', 'Bilibili', 'success', '2026-06-26 07:32:10.215570', ''),
  (346, '计算机网络', '物理层', '通信基础', 'https://www.bilibili.com/video/BV1mWnWz2EDD', 'Bilibili', 'success', '2026-06-26 07:32:10.215570', ''),
  (347, '计算机网络', '物理层', '通信基础', 'https://www.bilibili.com/video/BV1kpvHBSEWd', 'Bilibili', 'success', '2026-06-26 07:32:10.231395', ''),
  (348, '计算机网络', '物理层', '传输介质', 'https://www.bilibili.com/video/BV19LC4BuEZi', 'Bilibili', 'success', '2026-06-26 07:32:11.393842', ''),
  (349, '计算机网络', '物理层', '传输介质', 'https://www.bilibili.com/video/BV116poeHENo', 'Bilibili', 'success', '2026-06-26 07:32:11.405296', ''),
  (350, '计算机网络', '物理层', '传输介质', 'https://www.bilibili.com/video/BV1Gu411V7pN', 'Bilibili', 'success', '2026-06-26 07:32:11.405296', ''),
  (351, '计算机网络', '物理层', '传输介质', 'https://www.bilibili.com/video/BV1yP11BjEiv', 'Bilibili', 'success', '2026-06-26 07:32:11.407319', ''),
  (352, '计算机网络', '物理层', '物理层设备', 'https://www.bilibili.com/video/BV1id4y117E9', 'Bilibili', 'success', '2026-06-26 07:32:12.569104', ''),
  (353, '计算机网络', '物理层', '物理层设备', 'https://www.bilibili.com/video/BV1fa4y147Q8', 'Bilibili', 'success', '2026-06-26 07:32:12.569104', ''),
  (354, '计算机网络', '物理层', '物理层设备', 'https://www.bilibili.com/video/BV1Gz411b79P', 'Bilibili', 'success', '2026-06-26 07:32:12.569104', ''),
  (355, '计算机网络', '物理层', '物理层设备', 'https://www.bilibili.com/video/BV1KwtFzFEt6', 'Bilibili', 'success', '2026-06-26 07:32:12.569104', ''),
  (356, '计算机网络', '物理层', '物理层设备', 'https://www.bilibili.com/video/BV1Vmn9zCE3e', 'Bilibili', 'success', '2026-06-26 07:32:12.569104', ''),
  (357, '计算机网络', '数据链路层', '数据链路层的功能', 'https://www.bilibili.com/video/BV1JzNteUEj9', 'Bilibili', 'success', '2026-06-26 07:32:13.748007', ''),
  (358, '计算机网络', '数据链路层', '数据链路层的功能', 'https://www.bilibili.com/video/BV1hLtvzTEmd', 'Bilibili', 'success', '2026-06-26 07:32:13.748007', ''),
  (359, '计算机网络', '数据链路层', '数据链路层的功能', 'https://www.bilibili.com/video/BV14q4y1m7Nu', 'Bilibili', 'success', '2026-06-26 07:32:13.748007', ''),
  (360, '计算机网络', '数据链路层', '数据链路层的功能', 'https://www.bilibili.com/video/BV1oHXzY1EBZ', 'Bilibili', 'success', '2026-06-26 07:32:13.748007', ''),
  (361, '计算机网络', '数据链路层', '数据链路层的功能', 'https://www.bilibili.com/video/BV1G5Vh63EMq', 'Bilibili', 'success', '2026-06-26 07:32:13.748007', ''),
  (362, '计算机网络', '数据链路层', '组帧', 'https://www.bilibili.com/video/BV1hs4y1C7M7', 'Bilibili', 'success', '2026-06-26 07:32:14.909258', ''),
  (363, '计算机网络', '数据链路层', '组帧', 'https://www.bilibili.com/video/BV1zF411d7Gn', 'Bilibili', 'success', '2026-06-26 07:32:14.910378', ''),
  (364, '计算机网络', '数据链路层', '组帧', 'https://www.bilibili.com/video/BV1oHXzY1E6a', 'Bilibili', 'success', '2026-06-26 07:32:14.912376', ''),
  (365, '计算机网络', '数据链路层', '差错控制', 'https://www.bilibili.com/video/BV18bxbzjEoG', 'Bilibili', 'success', '2026-06-26 07:32:16.079233', ''),
  (366, '计算机网络', '数据链路层', '差错控制', 'https://www.bilibili.com/video/BV1Qm4y1e75R', 'Bilibili', 'success', '2026-06-26 07:32:16.079233', ''),
  (367, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'https://www.bilibili.com/video/BV1kJY7efEPX', 'Bilibili', 'success', '2026-06-26 07:32:17.301014', ''),
  (368, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'https://www.bilibili.com/video/BV171421f7aw', 'Bilibili', 'success', '2026-06-26 07:32:17.301014', ''),
  (369, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'https://www.bilibili.com/video/BV159WGzMEKE', 'Bilibili', 'success', '2026-06-26 07:32:17.301014', ''),
  (370, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'https://www.bilibili.com/video/BV1YK411X7UQ', 'Bilibili', 'success', '2026-06-26 07:32:17.308954', ''),
  (371, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'https://www.bilibili.com/video/BV1tFeTzKE12', 'Bilibili', 'success', '2026-06-26 07:32:17.308954', ''),
  (372, '计算机网络', '数据链路层', '介质访问控制', 'https://www.bilibili.com/video/BV1Q9eEeEEc2', 'Bilibili', 'success', '2026-06-26 07:32:18.498994', ''),
  (373, '计算机网络', '数据链路层', '局域网', 'https://www.bilibili.com/video/BV1UM41167sP', 'Bilibili', 'success', '2026-06-26 07:32:19.653127', ''),
  (374, '计算机网络', '数据链路层', '广域网', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:20.807597', 'no video found even with fallback search'),
  (375, '计算机网络', '数据链路层', '数据链路层设备', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:21.997348', 'no video found even with fallback search'),
  (376, '计算机网络', '网络层', '网络层的功能', 'https://www.bilibili.com/video/BV1xwNSeWEoH', 'Bilibili', 'success', '2026-06-26 07:32:23.163349', ''),
  (377, '计算机网络', '网络层', '网络层的功能', 'https://www.bilibili.com/video/BV18S42197eG', 'Bilibili', 'success', '2026-06-26 07:32:23.167378', ''),
  (378, '计算机网络', '网络层', '网络层的功能', 'https://www.bilibili.com/video/BV1QJqeYmEru', 'Bilibili', 'success', '2026-06-26 07:32:23.169390', ''),
  (379, '计算机网络', '网络层', '网络层的功能', 'https://www.bilibili.com/video/BV1LASNB8EVG', 'Bilibili', 'success', '2026-06-26 07:32:23.171403', ''),
  (380, '计算机网络', '网络层', '网络层的功能', 'https://www.bilibili.com/video/BV11BWzzAEkd', 'Bilibili', 'success', '2026-06-26 07:32:23.173414', ''),
  (381, '计算机网络', '网络层', 'IPv4', 'https://www.bilibili.com/video/BV1vD4QzWEYi', 'Bilibili', 'success', '2026-06-26 07:32:24.330989', ''),
  (382, '计算机网络', '网络层', 'IPv4', 'https://www.bilibili.com/video/BV1Rw4NecEez', 'Bilibili', 'success', '2026-06-26 07:32:24.330989', ''),
  (383, '计算机网络', '网络层', 'IPv4', 'https://www.bilibili.com/video/BV1bz4y1a7D8', 'Bilibili', 'success', '2026-06-26 07:32:24.330989', ''),
  (384, '计算机网络', '网络层', 'IPv4', 'https://www.bilibili.com/video/BV1ren2zMEf2', 'Bilibili', 'success', '2026-06-26 07:32:24.339073', ''),
  (385, '计算机网络', '网络层', 'IPv4', 'https://www.bilibili.com/video/BV19C4115788', 'Bilibili', 'success', '2026-06-26 07:32:24.339073', ''),
  (386, '计算机网络', '网络层', 'IPv6', 'https://www.bilibili.com/video/BV1dJ411R7dc', 'Bilibili', 'success', '2026-06-26 07:32:26.590348', ''),
  (387, '计算机网络', '网络层', 'IPv6', 'https://www.bilibili.com/video/BV1n841157Zc', 'Bilibili', 'success', '2026-06-26 07:32:26.593513', ''),
  (388, '计算机网络', '网络层', 'IPv6', 'https://www.bilibili.com/video/BV1Nv4y1o7fV', 'Bilibili', 'success', '2026-06-26 07:32:26.594586', ''),
  (389, '计算机网络', '网络层', 'IPv6', 'https://www.bilibili.com/video/BV1oJ411R7AW', 'Bilibili', 'success', '2026-06-26 07:32:26.595578', ''),
  (390, '计算机网络', '网络层', 'IPv6', 'https://www.bilibili.com/video/BV1dJ411R7Xf', 'Bilibili', 'success', '2026-06-26 07:32:26.597627', ''),
  (391, '计算机网络', '网络层', '路由算法与路由协议', 'https://www.bilibili.com/video/BV1ydUmBcETy', 'Bilibili', 'success', '2026-06-26 07:32:27.744091', ''),
  (392, '计算机网络', '网络层', '路由算法与路由协议', 'https://www.bilibili.com/video/BV1vzH5zBEYo', 'Bilibili', 'success', '2026-06-26 07:32:27.746090', ''),
  (393, '计算机网络', '网络层', 'IP多播', 'https://www.bilibili.com/video/BV18SSGB3Ewz', 'Bilibili', 'success', '2026-06-26 07:32:28.921675', ''),
  (394, '计算机网络', '网络层', 'IP多播', 'https://www.bilibili.com/video/BV1d8yuBfE52', 'Bilibili', 'success', '2026-06-26 07:32:28.923581', ''),
  (395, '计算机网络', '网络层', '移动IP', 'https://www.bilibili.com/video/BV1bbx4zzEBv', 'Bilibili', 'success', '2026-06-26 07:32:30.096580', ''),
  (396, '计算机网络', '网络层', '移动IP', 'https://www.bilibili.com/video/BV1QZ4y127DU', 'Bilibili', 'success', '2026-06-26 07:32:30.096580', ''),
  (397, '计算机网络', '网络层', '网络层设备', 'https://www.bilibili.com/video/BV1XR4y1y72o', 'Bilibili', 'success', '2026-06-26 07:32:31.275246', ''),
  (398, '计算机网络', '传输层', '传输层提供的服务', 'https://www.bilibili.com/video/BV1A24y117CM', 'Bilibili', 'success', '2026-06-26 07:32:32.487234', ''),
  (399, '计算机网络', '传输层', '传输层提供的服务', 'https://www.bilibili.com/video/BV1Tp1KYHEz2', 'Bilibili', 'success', '2026-06-26 07:32:32.489748', ''),
  (400, '计算机网络', '传输层', '传输层提供的服务', 'https://www.bilibili.com/video/BV1G841157gd', 'Bilibili', 'success', '2026-06-26 07:32:32.492536', '');
INSERT INTO `video_crawl_log` (`id`, `subject`, `knowledge_point`, `section`, `url`, `platform`, `status`, `crawl_time`, `error_msg`) VALUES
  (401, '计算机网络', '传输层', '传输层提供的服务', 'https://www.bilibili.com/video/BV1ve411N7k5', 'Bilibili', 'success', '2026-06-26 07:32:32.495537', ''),
  (402, '计算机网络', '传输层', '传输层提供的服务', 'https://www.bilibili.com/video/BV1ki421o7Gc', 'Bilibili', 'success', '2026-06-26 07:32:32.497539', ''),
  (403, '计算机网络', '传输层', 'UDP', 'https://www.bilibili.com/video/BV1V5YszdEqS', 'Bilibili', 'success', '2026-06-26 07:32:33.661552', ''),
  (404, '计算机网络', '传输层', 'UDP', 'https://www.bilibili.com/video/BV1y8ypYoE2D', 'Bilibili', 'success', '2026-06-26 07:32:33.663666', ''),
  (405, '计算机网络', '传输层', 'UDP', 'https://www.bilibili.com/video/BV1tA411C7cq', 'Bilibili', 'success', '2026-06-26 07:32:33.664658', ''),
  (406, '计算机网络', '传输层', 'UDP', 'https://www.bilibili.com/video/BV12Vs3ecEpq', 'Bilibili', 'success', '2026-06-26 07:32:33.666667', ''),
  (407, '计算机网络', '传输层', 'UDP', 'https://www.bilibili.com/video/BV12pGDeVE4b', 'Bilibili', 'success', '2026-06-26 07:32:33.667660', ''),
  (408, '计算机网络', '传输层', 'TCP', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:34.813206', 'no video found even with fallback search'),
  (409, '计算机网络', '应用层', '网络应用模型', 'https://www.bilibili.com/video/BV1fG4y1G7Uc', 'Bilibili', 'success', '2026-06-26 07:32:36.275111', ''),
  (410, '计算机网络', '应用层', '网络应用模型', 'https://www.bilibili.com/video/BV1westzcE3h', 'Bilibili', 'success', '2026-06-26 07:32:36.275111', ''),
  (411, '计算机网络', '应用层', '网络应用模型', 'https://www.bilibili.com/video/BV1s24DzME2W', 'Bilibili', 'success', '2026-06-26 07:32:36.275111', ''),
  (412, '计算机网络', '应用层', '网络应用模型', 'https://www.bilibili.com/video/BV1WW4y1G73S', 'Bilibili', 'success', '2026-06-26 07:32:36.275111', ''),
  (413, '计算机网络', '应用层', 'DNS域名系统', 'https://www.bilibili.com/video/BV1DE4m1R7BG', 'Bilibili', 'success', '2026-06-26 07:32:37.433711', ''),
  (414, '计算机网络', '应用层', 'DNS域名系统', 'https://www.bilibili.com/video/BV12Hatz9Esa', 'Bilibili', 'success', '2026-06-26 07:32:37.433711', ''),
  (415, '计算机网络', '应用层', 'DNS域名系统', 'https://www.bilibili.com/video/BV1sw5LzMETb', 'Bilibili', 'success', '2026-06-26 07:32:37.433711', ''),
  (416, '计算机网络', '应用层', 'DNS域名系统', 'https://www.bilibili.com/video/BV1DHjZz3Efd', 'Bilibili', 'success', '2026-06-26 07:32:37.433711', ''),
  (417, '计算机网络', '应用层', 'DNS域名系统', 'https://www.bilibili.com/video/BV1tm4y1z7RB', 'Bilibili', 'success', '2026-06-26 07:32:37.433711', ''),
  (418, '计算机网络', '应用层', '文件传输协议', 'https://www.bilibili.com/video/BV1H9etzSEJy', 'Bilibili', 'success', '2026-06-26 07:32:38.648257', ''),
  (419, '计算机网络', '应用层', '电子邮件', 'https://www.bilibili.com/video/BV1Q5411N7Vs', 'Bilibili', 'success', '2026-06-26 07:32:39.810406', ''),
  (420, '计算机网络', '应用层', '万维网', NULL, 'Bilibili', 'failed', '2026-06-26 07:32:40.972369', 'no video found even with fallback search'),
  (421, '计算机组成原理', '输入输出系统', 'IO系统概述', 'https://www.bilibili.com/video/BV12z4y1J78H', 'Bilibili', 'success', '2026-06-26 07:32:42.134580', ''),
  (422, '计算机组成原理', '输入输出系统', 'IO系统概述', 'https://www.bilibili.com/video/BV13mtMzhEb7', 'Bilibili', 'success', '2026-06-26 07:32:42.134580', ''),
  (423, '计算机组成原理', '输入输出系统', 'IO系统概述', 'https://www.bilibili.com/video/BV1h715BTET6', 'Bilibili', 'success', '2026-06-26 07:32:42.139091', ''),
  (424, '计算机组成原理', '输入输出系统', 'IO系统概述', 'https://www.bilibili.com/video/BV1UjUkBHE2y', 'Bilibili', 'success', '2026-06-26 07:32:42.140089', ''),
  (425, '计算机组成原理', '输入输出系统', 'IO系统概述', 'https://www.bilibili.com/video/BV12dpXzNERT', 'Bilibili', 'success', '2026-06-26 07:32:42.142087', ''),
  (426, '计算机组成原理', '输入输出系统', 'IO控制方式', 'https://www.bilibili.com/video/BV1LwdHBoES6', 'Bilibili', 'success', '2026-06-26 07:32:43.300621', ''),
  (427, '计算机组成原理', '输入输出系统', 'IO控制方式', 'https://www.bilibili.com/video/BV1NfAMzdEJe', 'Bilibili', 'success', '2026-06-26 07:32:43.308122', ''),
  (428, '计算机组成原理', '输入输出系统', 'IO控制方式', 'https://www.bilibili.com/video/BV1j9XyYFEvc', 'Bilibili', 'success', '2026-06-26 07:32:43.308802', ''),
  (429, '操作系统', '输入输出管理', 'IO管理概述', 'https://www.bilibili.com/video/BV1xo4y1k78k', 'Bilibili', 'success', '2026-06-26 07:32:44.480001', ''),
  (430, '操作系统', '输入输出管理', 'IO管理概述', 'https://www.bilibili.com/video/BV1MtSvYLEtM', 'Bilibili', 'success', '2026-06-26 07:32:44.489271', ''),
  (431, '计算机组成原理', '中央处理器', '控制器的功能和工作原理', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:05.449838', 'no video found even with fallback search'),
  (432, '计算机组成原理', '中央处理器', '异常和中断机制', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:06.707857', 'no video found even with fallback search'),
  (433, '操作系统', '输入输出管理', 'I/O管理概述', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:07.934335', 'no video found even with fallback search'),
  (434, '操作系统', '输入输出管理', '设备独立性软件', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:09.148949', 'no video found even with fallback search'),
  (435, '计算机网络', '数据链路层', '广域网', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:10.369705', 'no video found even with fallback search'),
  (436, '计算机网络', '数据链路层', '数据链路层设备', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:11.583001', 'no video found even with fallback search'),
  (437, '计算机网络', '传输层', 'TCP', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:12.791807', 'no video found even with fallback search'),
  (438, '计算机网络', '应用层', '万维网', NULL, 'Bilibili', 'failed', '2026-06-26 07:49:13.982378', 'no video found even with fallback search');

-- ------------------------------------------------------------
-- Data for `video_resource`
-- ------------------------------------------------------------
INSERT INTO `video_resource` (`id`, `subject`, `knowledge_point`, `title`, `platform`, `url`, `reason`, `cover_url`, `duration`, `is_deleted`, `quality_score`, `author`, `crawl_source`, `section`) VALUES
  (1, '数据结构', '线性表', '线性表顺序存储与链式存储对比', 'Bilibili', 'https://www.bilibili.com/video/BV1dWbQzfEDd', '结合历年 408 真题讲解 线性表，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/2fec6071d7efd0202e825caaa98144325612c59e.jpg', '16:48', 0, 80, '蓝不过海呀', 'seed', ''),
  (2, '数据结构', '线性表', '单链表反转与双指针技巧', 'Bilibili', 'https://www.bilibili.com/video/BV1nB4y1i7eL', '线性表 基础入门到进阶系统讲解。', 'https://i0.hdslb.com/bfs/archive/73b3de70832be9364f24622a791feb802b1030c8.jpg', '16:15', 0, 76, '代码随想录', 'seed', ''),
  (3, '数据结构', '线性表', '408 线性表高频算法题精讲', 'Bilibili', 'https://www.bilibili.com/video/BV1Pq4y1R7Gm', '以例题驱动讲解 线性表，配合动画演示清晰易懂。', 'https://i1.hdslb.com/bfs/archive/dccc3fcd58983bcb6948c91c35b93992fd0cd648.jpg', '12:59', 0, 76, '站长数据结构', 'seed', ''),
  (4, '数据结构', '栈和队列', '栈与队列的相互模拟实现', 'Bilibili', 'https://www.bilibili.com/video/BV12d3jzuEZP', '栈和队列 基础入门到进阶系统讲解。', 'https://i1.hdslb.com/bfs/archive/b43cf8122dab31db3698fcd90d21ae51ee5baf02.jpg', '15:39', 0, 66, '小熊学长x', 'seed', ''),
  (5, '数据结构', '栈和队列', '中缀表达式转后缀表达式', 'Bilibili', 'https://www.bilibili.com/video/BV1hxKDzFEzJ', '从真题角度剖析 栈和队列 解题思路与易错点。', 'https://i1.hdslb.com/bfs/archive/be753988cf5110519e572c242c4467b61e9dfe2d.jpg', '12:28', 0, 60, '小熊学长x', 'seed', ''),
  (6, '数据结构', '树与二叉树', '二叉树前中后序遍历递归与迭代', 'Bilibili', 'https://www.bilibili.com/video/BV15f4y1W7i2', '动画演示 树与二叉树 底层原理，帮助理解记忆。', 'https://i0.hdslb.com/bfs/archive/397255bdf86a0500444c5a7b07d678ccd4c4635b.jpg', '18:33', 0, 74, '代码随想录', 'seed', ''),
  (7, '数据结构', '树与二叉树', '二叉搜索树与平衡二叉树', 'Bilibili', 'https://www.bilibili.com/video/BV1GDWMz9EXU', '动画演示 树与二叉树 底层原理，帮助理解记忆。', 'https://i2.hdslb.com/bfs/archive/e17a16d56af6f9acb90c995bc3ae837e3007e529.jpg', '19:49', 0, 68, '蓝不过海呀', 'seed', ''),
  (8, '数据结构', '树与二叉树', '树与二叉树的转换方法', 'Bilibili', 'https://www.bilibili.com/video/BV1xBqZBAE12', '以例题驱动讲解 树与二叉树，配合动画演示清晰易懂。', 'https://i1.hdslb.com/bfs/archive/2100fc28f0067b7c2acd722678b040206ebb9785.jpg', '19:24', 0, 80, '蓝不过海呀', 'seed', ''),
  (9, '数据结构', '树与二叉树', '哈夫曼树与哈夫曼编码', 'Bilibili', 'https://www.bilibili.com/video/BV1qu411F7Zs', '通过代码实现加深对 树与二叉树 的理解。', 'https://i2.hdslb.com/bfs/archive/1573e073d40442c5b5b651eaef64c6a2ff0b4e04.jpg', '21:56', 0, 78, '蓝不过海呀', 'seed', ''),
  (10, '数据结构', '图', '图的邻接矩阵与邻接表存储', 'Bilibili', 'https://www.bilibili.com/video/BV1bj411Z7dc', '以例题驱动讲解 图，配合动画演示清晰易懂。', 'https://i0.hdslb.com/bfs/archive/081453244ac0587e97c1466efaa44341a6209b46.jpg', '11:14', 0, 84, '吃葡萄不吐葡萄皮ooc', 'seed', ''),
  (11, '数据结构', '图', 'DFS与BFS遍历算法', 'Bilibili', 'https://www.bilibili.com/video/BV1hd4y1R7Ka', '动画演示 图 底层原理，帮助理解记忆。', 'https://i0.hdslb.com/bfs/archive/1b2b940397842936dca423843c1f6ad347d9fd7f.jpg', '14:27', 0, 76, '站长数据结构', 'seed', ''),
  (12, '数据结构', '图', '最短路径Dijkstra与Floyd', 'Bilibili', 'https://www.bilibili.com/video/BV1Us421T7nq', '结合历年 408 真题讲解 图，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/41b0dd3534d433fffa80419641e041ec0837e147.jpg', '18:29', 0, 74, '向小园_', 'seed', ''),
  (13, '数据结构', '图', '最小生成树Prim与Kruskal', 'Bilibili', 'https://www.bilibili.com/video/BV1wG411z79G', '从真题角度剖析 图 解题思路与易错点。', 'https://i0.hdslb.com/bfs/archive/49b0a509c6258d1a0c934b71263040485d7b23d1.jpg', '16:59', 0, 94, '蓝不过海呀', 'seed', ''),
  (14, '数据结构', '查找', '二叉排序树查找与平衡', 'Bilibili', 'https://www.bilibili.com/video/BV1dA411f7ne', '覆盖 查找 核心概念与常见 408 考法，适合系统学习。', 'https://i1.hdslb.com/bfs/archive/9cff7bdd8049e8b0f92b3c8389c8fef4d9d01d28.jpg', '21:33', 0, 74, '彭彭学编程', 'seed', ''),
  (15, '数据结构', '查找', '散列表与冲突处理方法', 'Bilibili', 'https://www.bilibili.com/video/BV13NwveLE1D', '通过代码实现加深对 查找 的理解。', 'https://i1.hdslb.com/bfs/archive/cdc9d501e90f44c5fafc85b55199c806069d8953.jpg', '29:51', 0, 96, '蓝不过海呀', 'seed', ''),
  (16, '数据结构', '排序', '快速排序与归并排序详解', 'Bilibili', 'https://www.bilibili.com/video/BV1V94y1q7cC', '用思维导图串联 排序 知识网络，适合快速回顾。', 'https://i0.hdslb.com/bfs/archive/058945cec8f2a538a8de33dca09617994fb0401c.jpg', '24:43', 0, 84, '吃葡萄不吐葡萄皮ooc', 'seed', ''),
  (17, '数据结构', '排序', '插入排序与选择排序对比', 'Bilibili', 'https://www.bilibili.com/video/BV1tf421Q7eh', '排序 基础入门到进阶系统讲解。', 'https://i2.hdslb.com/bfs/archive/3ec02fe6e19bc0a2cfbde7825b81e06b361d660b.jpg', '10:24', 0, 96, '蓝不过海呀', 'seed', ''),
  (18, '数据结构', '排序', '堆排序与基数排序', 'Bilibili', 'https://www.bilibili.com/video/BV1KrzrYeEDw', '通过代码实现加深对 排序 的理解。', 'https://i0.hdslb.com/bfs/archive/caafb30d2f5fc6424a013da9ad020a692bdf2f5c.jpg', '12:5', 0, 96, '蓝不过海呀', 'seed', ''),
  (19, '数据结构', '排序', '各种排序算法复杂度总结', 'Bilibili', 'https://www.bilibili.com/video/BV1NcDYBbE5P', '用思维导图串联 排序 知识网络，适合快速回顾。', 'https://i0.hdslb.com/bfs/archive/cb87871c0c32d36d98da96f67143e7d4d16d52aa.jpg', '15:22', 0, 76, '图码', 'seed', ''),
  (20, '计算机组成原理', '数据表示与运算', '原码反码补码与移码', 'Bilibili', 'https://www.bilibili.com/video/BV1Mr4y1V7af', '梳理 数据表示与运算 知识体系与高频考点，适合考前复盘。', 'https://i1.hdslb.com/bfs/archive/c8dd3fd7b89a7d026d4ec64bb67e447f9814536d.jpg', '26:20', 0, 60, 'Gavin一路向前', 'seed', ''),
  (21, '计算机组成原理', '数据表示与运算', '定点数与浮点数IEEE754', 'Bilibili', 'https://www.bilibili.com/video/BV1mp4y1V79U', '通过代码实现加深对 数据表示与运算 的理解。', 'https://i1.hdslb.com/bfs/archive/36d9c71731fc3be250d75df59f44229d8804a10a.jpg', '21:44', 0, 60, '就是氧气11', 'seed', ''),
  (22, '计算机组成原理', '数据表示与运算', 'ALU算术逻辑单元工作原理', 'Bilibili', 'https://www.bilibili.com/video/BV13p4y1V7gA', '覆盖 数据表示与运算 核心概念与常见 408 考法，适合系统学习。', 'https://i1.hdslb.com/bfs/archive/0c09e190bbf2304e674f1c86351f819e64f2c513.jpg', '26:4', 0, 60, '就是氧气11', 'seed', ''),
  (23, '计算机组成原理', '存储系统', 'Cache映射方式与替换算法', 'Bilibili', 'https://www.bilibili.com/video/BV1zN4y1P7PY', '动画演示 存储系统 底层原理，帮助理解记忆。', 'https://i1.hdslb.com/bfs/archive/63273d68e9c75e17d8316c27fcb7dc89693a3ee9.jpg', '24:22', 0, 66, '神秘人出海了', 'seed', ''),
  (24, '计算机组成原理', '存储系统', '虚拟存储器与页式管理', 'Bilibili', 'https://www.bilibili.com/video/BV1yt4y1J7ta', '以例题驱动讲解 存储系统，配合动画演示清晰易懂。', 'https://i1.hdslb.com/bfs/archive/7f18487fc695d04d8975da5bac4478496a1e4fee.jpg', '15:48', 0, 80, '意识流的鱼大师', 'seed', ''),
  (25, '计算机组成原理', '存储系统', '磁盘调度算法与RAID', 'Bilibili', 'https://www.bilibili.com/video/BV1wp4y1n7h4', '从真题角度剖析 存储系统 解题思路与易错点。', 'https://i1.hdslb.com/bfs/archive/e83f32d9e559aa0a58f5592b11399ffbb404f6d5.jpg', '16:0', 0, 48, '就是氧气11', 'seed', ''),
  (26, '计算机组成原理', '指令系统', '指令格式与寻址方式', 'Bilibili', 'https://www.bilibili.com/video/BV1Z24y1m7gp', '指令系统 基础入门到进阶系统讲解。', 'https://i0.hdslb.com/bfs/archive/7719d91aa5e58c392e760a8fcf0703876689ca59.jpg', '14:4', 0, 66, '彭彭学编程', 'seed', ''),
  (27, '计算机组成原理', '指令系统', 'CISC与RISC对比', 'Bilibili', 'https://www.bilibili.com/video/BV1ro4y1W7xN', '以例题驱动讲解 指令系统，配合动画演示清晰易懂。', 'https://i2.hdslb.com/bfs/archive/3901efe7d5bb47ab8a7309aa825e92966b94d7e0.jpg', '13:45', 0, 44, 'ZOMI酱', 'seed', ''),
  (28, '计算机组成原理', '指令系统', '指令流水线与数据冒险', 'Bilibili', 'https://www.bilibili.com/video/BV1cV4y1q7ca', '覆盖 指令系统 核心概念与常见 408 考法，适合系统学习。', 'https://i2.hdslb.com/bfs/archive/4c71d3deaa8986d4e8befad459e361f09508c730.jpg', '16:51', 0, 70, '就是氧气11', 'seed', ''),
  (29, '计算机组成原理', '中央处理器', 'CPU数据通路与控制器', 'Bilibili', 'https://www.bilibili.com/video/BV1WU421Z7Fb', '用思维导图串联 中央处理器 知识网络，适合快速回顾。', 'https://i2.hdslb.com/bfs/archive/453c8a33e7fc05e46912060f3bdfa83d11377fef.jpg', '18:10', 0, 62, '账号已注销', 'seed', ''),
  (30, '计算机组成原理', '总线与 I/O', '总线仲裁与控制方式', 'Bilibili', 'https://www.bilibili.com/video/BV1vW4y1B7jq', '从真题角度剖析 总线与 I/O 解题思路与易错点。', 'https://i1.hdslb.com/bfs/archive/15d4f0eccc229a2d30bd5f582f7bb47ecbba482c.jpg', '10:48', 0, 70, '意识流的鱼大师', 'seed', ''),
  (31, '计算机组成原理', '总线与 I/O', '程序查询中断DMA方式', 'Bilibili', 'https://www.bilibili.com/video/BV1rq4y137kt', '总线与 I/O 基础入门到进阶系统讲解。', 'https://i0.hdslb.com/bfs/archive/5746e4748acd5d93267b66094645208eca85deed.jpg', '11:11', 0, 60, '计算机考研大师兄', 'seed', ''),
  (32, '计算机组成原理', '总线与 I/O', 'I/O接口与端口编址', 'Bilibili', 'https://www.bilibili.com/video/BV1g94izTEu2', '覆盖 总线与 I/O 核心概念与常见 408 考法，适合系统学习。', 'https://i1.hdslb.com/bfs/archive/eac395f3e9c9aa0e68c7076db0a4ed16aad79f7f.jpg', '24:34', 0, 44, '赛博门外憨', 'seed', ''),
  (33, '操作系统', '进程与线程', '进程状态转换与PCB', 'Bilibili', 'https://www.bilibili.com/video/BV14z4y1R7t6', '进程与线程 基础入门到进阶系统讲解。', 'https://i2.hdslb.com/bfs/archive/4a4ee559b51f22d6249117bae1819eb542d2dfab.jpg', '12:4', 0, 60, '托儿所所长亚索', 'seed', ''),
  (34, '操作系统', '进程与线程', '线程与进程对比及实现', 'Bilibili', 'https://www.bilibili.com/video/BV1bN411a7MX', '从真题角度剖析 进程与线程 解题思路与易错点。', 'https://i2.hdslb.com/bfs/archive/3f5593f90d3bb8554fa5e79de9831ea4e6fe59a8.jpg', '25:49', 0, 76, '就是氧气11', 'seed', ''),
  (35, '操作系统', '进程与线程', '进程调度算法详解', 'Bilibili', 'https://www.bilibili.com/video/BV1CK411R7iJ', '以例题驱动讲解 进程与线程，配合动画演示清晰易懂。', 'https://i0.hdslb.com/bfs/archive/ce0b68d47a2f43dd649a062d5cd1c56b142bab59.jpg', '11:6', 0, 80, '-Myles-', 'seed', ''),
  (36, '操作系统', '同步与互斥', 'PV操作与信号量机制', 'Bilibili', 'https://www.bilibili.com/video/BV1Ph4y1w7Dx', '覆盖 同步与互斥 核心概念与常见 408 考法，适合系统学习。', 'https://i2.hdslb.com/bfs/archive/6e667d80829de4b721fb0e8c720969415733caf7.jpg', '22:52', 0, 70, '就是氧气11', 'seed', ''),
  (37, '操作系统', '同步与互斥', '生产者消费者问题', 'Bilibili', 'https://www.bilibili.com/video/BV1Ei4y1u7qy', '以例题驱动讲解 同步与互斥，配合动画演示清晰易懂。', 'https://i2.hdslb.com/bfs/archive/21cb1be31be463dfb7b170cb4e87881d599eb277.jpg', '25:13', 0, 66, 'oc999', 'seed', ''),
  (38, '操作系统', '同步与互斥', '读者写者问题与哲学家就餐', 'Bilibili', 'https://www.bilibili.com/video/BV12m421G7Lc', '梳理 同步与互斥 知识体系与高频考点，适合考前复盘。', 'https://i0.hdslb.com/bfs/archive/06f0ef7254c3ca6ae789490840fa00bc52d020e6.jpg', '27:2', 0, 76, '图灵讲计组', 'seed', ''),
  (39, '操作系统', '死锁', '死锁四个必要条件', 'Bilibili', 'https://www.bilibili.com/video/BV1Pk4y1G7b6', '覆盖 死锁 核心概念与常见 408 考法，适合系统学习。', 'https://i1.hdslb.com/bfs/archive/454553a7ff5d6faadcc0dd339c0fe6afe26b2886.jpg', '22:30', 0, 76, '就是氧气11', 'seed', ''),
  (40, '操作系统', '死锁', '银行家算法避免死锁', 'Bilibili', 'https://www.bilibili.com/video/BV1A24y1X7x7', '对比分析 死锁 不同考法，归纳总结解题模板。', 'https://i0.hdslb.com/bfs/archive/05d2f776a193f092a83cae1ba6b3e6a07d91cc22.jpg', '11:23', 0, 76, '彭彭学编程', 'seed', ''),
  (41, '操作系统', '内存管理', '分页与分段存储管理', 'Bilibili', 'https://www.bilibili.com/video/BV14G411P7mU', '用思维导图串联 内存管理 知识网络，适合快速回顾。', 'https://i0.hdslb.com/bfs/archive/05d2f776a193f092a83cae1ba6b3e6a07d91cc22.jpg', '11:6', 0, 66, '彭彭学编程', 'seed', ''),
  (42, '操作系统', '内存管理', 'TLB快表与页表结构', 'Bilibili', 'https://www.bilibili.com/video/BV16x4y1x7ie', '通过代码实现加深对 内存管理 的理解。', 'https://i2.hdslb.com/bfs/archive/d6fe8c40f03a79ce3d5c4572946b9f1519082c1d.jpg', '23:22', 0, 66, '图灵讲计组', 'seed', ''),
  (43, '操作系统', '页面置换算法', 'FIFO LRU OPT页面置换对比', 'Bilibili', 'https://www.bilibili.com/video/BV1WA411J7Dw', '覆盖 页面置换算法 核心概念与常见 408 考法，适合系统学习。', 'https://i2.hdslb.com/bfs/archive/d1591316d8d555e7008d42f202d1da6d0cd575c2.jpg', '13:36', 0, 66, 'oc999', 'seed', ''),
  (44, '操作系统', '页面置换算法', 'LRU实现与命中率分析', 'Bilibili', 'https://www.bilibili.com/video/BV1k54y1D7RB', '以例题驱动讲解 页面置换算法，配合动画演示清晰易懂。', 'https://i0.hdslb.com/bfs/archive/e8b87d4736bf6b576d1e2328cc1def4eaea9a3d4.jpg', '14:50', 0, 80, '这个东东有点野', 'seed', ''),
  (45, '操作系统', '文件系统', '文件目录结构与FCB', 'Bilibili', 'https://www.bilibili.com/video/BV1RT5j6kEVr', '动画演示 文件系统 底层原理，帮助理解记忆。', 'https://i0.hdslb.com/bfs/archive/1b11f8bf0032e755b6f75476d1c5ff5ae5a16b13.jpg', '11:13', 0, 20, 'FCB拍卖', 'seed', ''),
  (46, '操作系统', '文件系统', '文件分配方式与空闲管理', 'Bilibili', 'https://www.bilibili.com/video/BV1d84y147o8', '结合历年 408 真题讲解 文件系统，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/05d2f776a193f092a83cae1ba6b3e6a07d91cc22.jpg', '11:17', 0, 66, '彭彭学编程', 'seed', ''),
  (47, '操作系统', '文件系统', '磁盘空间管理与调度', 'Bilibili', 'https://www.bilibili.com/video/BV17nH7zEEHk', '用思维导图串联 文件系统 知识网络，适合快速回顾。', 'https://i0.hdslb.com/bfs/archive/c06132f83dd9eec0bf391dfb8da47737cbe98136.jpg', '15:11', 0, 64, '22408练习生', 'seed', ''),
  (48, '操作系统', '文件系统', '文件系统层次结构', 'Bilibili', 'https://www.bilibili.com/video/BV1TT4y1u7K6', '结合历年 408 真题讲解 文件系统，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/30eb4a3eb8d8e5b2cb799578010ef46b7b533792.jpg', '14:1', 0, 68, '熊哥保佑你', 'seed', ''),
  (49, '计算机网络', '体系结构', 'OSI七层与TCP/IP四层模型', 'Bilibili', 'https://www.bilibili.com/video/BV1SK41157Pf', '从真题角度剖析 体系结构 解题思路与易错点。', 'https://i0.hdslb.com/bfs/archive/d9d423d46feb61a6003e84387621a73209525a82.jpg', '29:20', 0, 76, '湖科大教书匠', 'seed', ''),
  (50, '计算机网络', '体系结构', '协议与服务数据单元', 'Bilibili', 'https://www.bilibili.com/video/BV1EB4y1p7Rm', '体系结构 基础入门到进阶系统讲解。', 'https://i1.hdslb.com/bfs/archive/9cc8f6c99cad5964585f79643164b13118ab0517.jpg', '25:26', 0, 60, '老鸟又尔东', 'seed', ''),
  (51, '计算机网络', '数据链路层', 'CSMA/CD与以太网帧格式', 'Bilibili', 'https://www.bilibili.com/video/BV1SG411M7qz', '梳理 数据链路层 知识体系与高频考点，适合考前复盘。', 'https://i0.hdslb.com/bfs/archive/58901d42e78422a25a2396f8799faa027cf8774e.jpg', '21:35', 0, 66, '彭彭学编程', 'seed', ''),
  (52, '计算机网络', '数据链路层', '流量控制与可靠传输机制', 'Bilibili', 'https://www.bilibili.com/video/BV1sP411u7CZ', '结合历年 408 真题讲解 数据链路层，含详细推导过程。', 'https://i2.hdslb.com/bfs/archive/72846a5af31c5522b1cfbdb6ffbdf3159f708921.jpg', '27:23', 0, 62, '卡布达kaak', 'seed', ''),
  (53, '计算机网络', '数据链路层', 'MAC地址与ARP协议', 'Bilibili', 'https://www.bilibili.com/video/BV1we4y137ab', '结合历年 408 真题讲解 数据链路层，含详细推导过程。', 'https://i2.hdslb.com/bfs/archive/713b6200547bcb1ad1aba230a3cd11d2f41964bf.jpg', '21:3', 0, 76, '彭彭学编程', 'seed', ''),
  (54, '计算机网络', '数据链路层', '交换机自学习与VLAN', 'Bilibili', 'https://www.bilibili.com/video/BV1o24y1S7U9', '对比分析 数据链路层 不同考法，归纳总结解题模板。', 'https://i0.hdslb.com/bfs/archive/3cd2bef759f152fe2522fc3743e3db3c0fb0e156.jpg', '28:27', 0, 64, '费棍', 'seed', ''),
  (55, '计算机网络', '网络层', 'IP地址分类与CIDR', 'Bilibili', 'https://www.bilibili.com/video/BV1WP4y197im', '梳理 网络层 知识体系与高频考点，适合考前复盘。', 'https://i1.hdslb.com/bfs/archive/fdc8f308a45846e9d6b0047fcf5b444890256ba9.jpg', '22:50', 0, 66, '彭彭学编程', 'seed', ''),
  (56, '计算机网络', '网络层', '子网划分与路由聚合', 'Bilibili', 'https://www.bilibili.com/video/BV1344y1S7nr', '对比分析 网络层 不同考法，归纳总结解题模板。', 'https://i2.hdslb.com/bfs/archive/2b2fc378bd1fa47f0d84a6c16e0d2f9688db4d70.jpg', '17:47', 0, 66, '彭彭学编程', 'seed', ''),
  (57, '计算机网络', '网络层', '路由算法RIP OSPF BGP', 'Bilibili', 'https://www.bilibili.com/video/BV1rD4y1Y7vD', '覆盖 网络层 核心概念与常见 408 考法，适合系统学习。', 'https://i0.hdslb.com/bfs/archive/58901d42e78422a25a2396f8799faa027cf8774e.jpg', '23:42', 0, 66, '彭彭学编程', 'seed', ''),
  (58, '计算机网络', '网络层', 'IPv4分组首部与分片', 'Bilibili', 'https://www.bilibili.com/video/BV1KP411M7YN', '梳理 网络层 知识体系与高频考点，适合考前复盘。', 'https://i0.hdslb.com/bfs/archive/74902abaf9b6aa0ae5959dc1f4d7f7f78260821d.jpg', '21:7', 0, 66, '彭彭学编程', 'seed', ''),
  (59, '计算机网络', '网络层', 'IPv6与过渡技术', 'Bilibili', 'https://www.bilibili.com/video/BV1G84y16763', '动画演示 网络层 底层原理，帮助理解记忆。', 'https://i0.hdslb.com/bfs/archive/58901d42e78422a25a2396f8799faa027cf8774e.jpg', '11:8', 0, 66, '彭彭学编程', 'seed', ''),
  (60, '计算机网络', '传输层', 'TCP三次握手与四次挥手', 'Bilibili', 'https://www.bilibili.com/video/BV19e4y117Zc', '动画演示 传输层 底层原理，帮助理解记忆。', 'https://i1.hdslb.com/bfs/archive/a9ffb5f6c9caccf85727a70ad962018ed135d102.jpg', '28:54', 0, 74, 'Please907', 'seed', ''),
  (61, '计算机网络', '传输层', 'TCP流量控制与拥塞控制', 'Bilibili', 'https://www.bilibili.com/video/BV1ND4y1Y7f8', '从真题角度剖析 传输层 解题思路与易错点。', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '25:23', 0, 66, '彭彭学编程', 'seed', ''),
  (62, '计算机网络', '应用层', 'DNS域名解析过程', 'Bilibili', 'https://www.bilibili.com/video/BV1u14y1J7gT', '覆盖 应用层 核心概念与常见 408 考法，适合系统学习。', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '15:4', 0, 66, '彭彭学编程', 'seed', ''),
  (63, '计算机网络', '应用层', 'HTTP协议与HTTPS区别', 'Bilibili', 'https://www.bilibili.com/video/BV1Xv4y197yb', '结合历年 408 真题讲解 应用层，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '22:42', 0, 66, '彭彭学编程', 'seed', ''),
  (64, '计算机网络', '应用层', 'FTP文件传输与控制连接', 'Bilibili', 'https://www.bilibili.com/video/BV1zM411671o', '对比分析 应用层 不同考法，归纳总结解题模板。', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '26:5', 0, 66, '彭彭学编程', 'seed', ''),
  (65, '计算机网络', '应用层', '电子邮件SMTP POP3 IMAP', 'Bilibili', 'https://www.bilibili.com/video/BV1iV4y1T7eG', '结合历年 408 真题讲解 应用层，含详细推导过程。', 'https://i0.hdslb.com/bfs/archive/2e5aec6ed389706defae16e6c4db1e2cfb4dcce9.jpg', '22:3', 0, 74, '湖科大教书匠', 'seed', ''),
  (66, '数据结构', '绪论', '计算机考研408|《数据结构》第一章 绪论 1.1基本概念01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1tkQgY1Ekx', '计算机考研408羊驼老师 讲解 · 播放 2389 次 · 覆盖 绪论 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '48:50', 0, 61, '计算机考研408羊驼老师', 'seed', '数据结构的基本概念'),
  (67, '数据结构', '绪论', '计算机考研408|《数据结构》第一章 绪论 1.1基本概念02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV13wQqYZEC3', '计算机考研408羊驼老师 讲解 · 播放 694 次 · 覆盖 绪论 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '45:38', 0, 51, '计算机考研408羊驼老师', 'seed', '数据结构的基本概念'),
  (68, '数据结构', '绪论', '计算机考研408|《数据结构》第一章 绪论 1.3算法评价|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1xMQdYiEuK', '计算机考研408羊驼老师 讲解 · 播放 440 次 · 覆盖 绪论 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '42:31', 0, 51, '计算机考研408羊驼老师', 'seed', '数据结构的基本概念'),
  (69, '数据结构', '绪论', '计算机考研408|《数据结构》第一章 绪论 1.2算法概念|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1UwQdY6EeG', '计算机考研408羊驼老师 讲解 · 播放 417 次 · 覆盖 绪论 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '38:1', 0, 51, '计算机考研408羊驼老师', 'seed', '数据结构的基本概念'),
  (70, '数据结构', '绪论', '强化1000题数据结构-基本概念与时间复杂度', 'Bilibili', 'https://www.bilibili.com/video/BV1si3VzxEJR', '就是氧气11 讲解 · 播放 5606 次 · 覆盖 绪论 相关内容', 'https://i1.hdslb.com/bfs/archive/e1edb413bdd3a73569156c304a040e4a6a93c0ca.jpg', '59:56', 0, 41, '就是氧气11', 'seed', '数据结构的基本概念'),
  (71, '数据结构', '绪论', '40分钟理清数据结构，期末、考研必备，至少节约一半复习时间', 'Bilibili', 'https://www.bilibili.com/video/BV1De4y1s7wZ', '优质推荐 · 乐智教学 制作 · 播放 86477 次 · 与 绪论 高度相关', 'https://i2.hdslb.com/bfs/archive/4df3a2c889d973e97438e4fae3103ecd5f1b0ac8.jpg', '47:3', 0, 71, '乐智教学', 'seed', '数据结构三要素'),
  (72, '数据结构', '绪论', '【408真题速通】时间复杂度：真题共考察8次，一套方法全秒杀', 'Bilibili', 'https://www.bilibili.com/video/BV1hrsbz5EJU', '优质推荐 · 王道计算机教育 制作 · 播放 68090 次 · 与 绪论 高度相关', 'https://i2.hdslb.com/bfs/archive/b062b72311b597d5e113a2a6070508dfcbb05c54.jpg', '45:57', 0, 47, '王道计算机教育', 'seed', '数据结构三要素'),
  (73, '数据结构', '绪论', '【一学就会】考研数据结构代码保姆级讲解！手把手带大家从代码小白到能轻松应对考试', 'Bilibili', 'https://www.bilibili.com/video/BV1gN4y1M7vW', '优质推荐 · 阿辉不会敲代码 制作 · 播放 51910 次 · 与 绪论 高度相关', 'https://i1.hdslb.com/bfs/archive/e7b9834f3b1e1975d47c2efd95ac9566537f42cc.jpg', '58:30', 0, 61, '阿辉不会敲代码', 'seed', '数据结构三要素'),
  (74, '数据结构', '绪论', '数据结构第一讲——绪论', 'Bilibili', 'https://www.bilibili.com/video/BV1MG5xz3Ezb', '铁柱学长Piccolo 讲解 · 播放 2472 次 · 覆盖 绪论 相关内容', 'https://i2.hdslb.com/bfs/archive/d79b4aeddc111dcfd377825af333b1d951e1a282.jpg', '41:10', 0, 55, '铁柱学长Piccolo', 'seed', '数据结构三要素'),
  (75, '数据结构', '绪论', '23王道408-数据结构-课后习题选择题讲解-第三章3.1', 'Bilibili', 'https://www.bilibili.com/video/BV1w3411c7Ug', '光怪陆离的陆离_ 讲解 · 播放 14113 次 · 覆盖 绪论 相关内容', 'https://i2.hdslb.com/bfs/archive/c06dba49609fe08fbf3ac1afbbe2927226cea18d.jpg', '31:5', 0, 51, '光怪陆离的陆离_', 'seed', '数据结构三要素'),
  (76, '数据结构', '绪论', '王道408数据结构第一章绪论总结', 'Bilibili', 'https://www.bilibili.com/video/BV1UU4y1z7hm', '程序猿辅导 讲解 · 播放 110 次 · 覆盖 绪论 相关内容', 'https://i2.hdslb.com/bfs/archive/80181a93462f4c9513aa320cdf3f9c26cce29a3e.jpg', '46:46', 0, 47, '程序猿辅导', 'seed', '算法和算法评价'),
  (77, '数据结构', '绪论', '【考研431】408数据结构押题-链表', 'Bilibili', 'https://www.bilibili.com/video/BV1ta4y1d7go', '小熊学长x 讲解 · 播放 3032 次 · 覆盖 绪论 相关内容', 'https://i2.hdslb.com/bfs/archive/995e07b4e587ada1ff5d3f6e6b2d628a8c75c924.jpg', '54:32', 0, 43, '小熊学长x', 'seed', '算法和算法评价'),
  (78, '数据结构', '绪论', '数据结构强化专题-B树与B+树', 'Bilibili', 'https://www.bilibili.com/video/BV1jYKfz4EVF', '就是氧气11 讲解 · 播放 2924 次 · 覆盖 绪论 相关内容', 'https://i2.hdslb.com/bfs/archive/e9204ccb9ae00641e58b09dbed1ef8d2c5ef35c6.jpg', '36:46', 0, 41, '就是氧气11', 'seed', '算法和算法评价'),
  (79, '数据结构', '绪论', '数据结构冲刺-Huffman树与并查集', 'Bilibili', 'https://www.bilibili.com/video/BV1PS4DzKEqi', '就是氧气11 讲解 · 播放 2633 次 · 覆盖 绪论 相关内容', 'https://i0.hdslb.com/bfs/archive/0c3cf01ad98906fe13ec715a9b0425970b017887.jpg', '32:34', 0, 41, '就是氧气11', 'seed', '算法和算法评价'),
  (80, '数据结构', '绪论', '数据结构冲刺-图及图的存储与遍历', 'Bilibili', 'https://www.bilibili.com/video/BV14i4vzfETe', '就是氧气11 讲解 · 播放 2626 次 · 覆盖 绪论 相关内容', 'https://i1.hdslb.com/bfs/archive/0d305738065cde08cd2a50fdee2c498a0e190120.jpg', '37:34', 0, 41, '就是氧气11', 'seed', '算法和算法评价'),
  (81, '数据结构', '线性表', '数据结构代码二，线性表的基本操作，你已经学会了，现在请准备开始代码这场游戏吧！', 'Bilibili', 'https://www.bilibili.com/video/BV1s3UNYDEnX', '李哥考研 讲解 · 播放 1572 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/fa3b4d523845e98f9124f64e89cdf89f34b2c8a8.jpg', '33:43', 0, 55, '李哥考研', 'seed', '线性表的定义和基本操作'),
  (82, '数据结构', '线性表', '《王道408数据结构考研》第二章线性表—重点知识与课后题点播', 'Bilibili', 'https://www.bilibili.com/video/BV1c44y1T7Sw', '生活必知必会 讲解 · 播放 1515 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/373baeb9d110001c019aa33696f5b635ac27508f.jpg', '33:52', 0, 61, '生活必知必会', 'seed', '线性表的定义和基本操作'),
  (83, '数据结构', '线性表', '35数据结构第六章2二叉树&amp;完全二叉树的定义和性质', 'Bilibili', 'https://www.bilibili.com/video/BV18eCYBnE3u', '小贱课堂 讲解 · 播放 1184 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/b1f5276addf0f392217f2912b7bf76275719e962.jpg', '35:52', 0, 41, '小贱课堂', 'seed', '线性表的定义和基本操作'),
  (84, '数据结构', '线性表', '45数据结构第七章图的定义和基本术语1', 'Bilibili', 'https://www.bilibili.com/video/BV1xSqaBfEAT', '小贱课堂 讲解 · 播放 1115 次 · 覆盖 线性表 相关内容', 'https://i1.hdslb.com/bfs/archive/33d5d7e5afdef3b5280adfbeb56d3e59c85e8663.jpg', '30:41', 0, 41, '小贱课堂', 'seed', '线性表的定义和基本操作'),
  (85, '数据结构', '线性表', '数据结构 强化阶段 复盘总结 线性表的顺序存储 实现方式(分配) 基本操作(创消增删改查) 大题代码示例', 'Bilibili', 'https://www.bilibili.com/video/BV1sN4y1c7Cn', '60Stone 讲解 · 播放 343 次 · 覆盖 线性表 相关内容', 'https://i1.hdslb.com/bfs/archive/4ed79704569c83b232132a62163f519ff3045332.jpg', '33:29', 0, 45, '60Stone', 'seed', '线性表的定义和基本操作'),
  (86, '数据结构', '线性表', '玩转数据结构-第2讲 线性表之顺序表3', 'Bilibili', 'https://www.bilibili.com/video/BV1g84y1W7Mq', '计算机考研刘财政 讲解 · 播放 698 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/5b7ede184531ea7f9b9a9a6ec902cd29634c89c4.jpg', '59:19', 0, 49, '计算机考研刘财政', 'seed', '顺序表示'),
  (87, '数据结构', '线性表', '计算机考研408|《数据结构》第二章 2.2线性表的顺序表示01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV16Ho1YyERW', '计算机考研408羊驼老师 讲解 · 播放 336 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '50:25', 0, 51, '计算机考研408羊驼老师', 'seed', '顺序表示'),
  (88, '数据结构', '线性表', '线性表的定义和基本操作（含习题）&amp;线性表的顺序表示', 'Bilibili', 'https://www.bilibili.com/video/BV1tM4y1U7gN', '书乔yw 讲解 · 播放 320 次 · 覆盖 线性表 相关内容', 'https://i1.hdslb.com/bfs/archive/5cc441c070b622368e44adacbe6bea86a569317d.jpg', '52:5', 0, 43, '书乔yw', 'seed', '顺序表示'),
  (89, '数据结构', '线性表', '计算机考研经典教材带读丨《数据结构》严蔚敏版： 2.1-2.2线性表定义、顺序表现和实现', 'Bilibili', 'https://www.bilibili.com/video/BV1jRE7z5Eo1', '启航计算机考研 讲解 · 播放 300 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/af72f7549eaf691a00b2b19b9b082a3d7ea9b26b.jpg', '32:59', 0, 49, '启航计算机考研', 'seed', '顺序表示'),
  (90, '数据结构', '线性表', '计算机考研408|《数据结构》第二章 2.3线性表的链式表示01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1rHo1YyETL', '计算机考研408羊驼老师 讲解 · 播放 275 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '56:23', 0, 51, '计算机考研408羊驼老师', 'seed', '顺序表示'),
  (91, '数据结构', '线性表', '数据结构-3-线性表-清晰讲解线性表的定义特点及顺序实现和链式实现-顺序表的实现和链表的实现', 'Bilibili', 'https://www.bilibili.com/video/BV1kWuBzXEZT', '熊熊计算机课堂 讲解 · 播放 2256 次 · 覆盖 线性表 相关内容', 'https://i1.hdslb.com/bfs/archive/0eb5ac3345e1b75f732777b2dfd6cab88b8cdf9c.jpg', '36:29', 0, 55, '熊熊计算机课堂', 'seed', '链式表示'),
  (92, '数据结构', '线性表', '数据结构-3.3-线性表-上机实验-链表编程实现-单链表上机实践', 'Bilibili', 'https://www.bilibili.com/video/BV1Y5udzXEfX', '熊熊计算机课堂 讲解 · 播放 1630 次 · 覆盖 线性表 相关内容', 'https://i1.hdslb.com/bfs/archive/793e649a1c943177eef3f9c6f799433fa0fa45b3.jpg', '38:41', 0, 55, '熊熊计算机课堂', 'seed', '链式表示'),
  (93, '数据结构', '线性表', '《数据结构考研辅导》2.3 线性表的链式表示和实现', 'Bilibili', 'https://www.bilibili.com/video/BV1k34y1x7wM', '人邮教育中心 讲解 · 播放 205 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/d5a8331f06403a19b216a760aab77b8adfa34f32.jpg', '44:6', 0, 47, '人邮教育中心', 'seed', '链式表示'),
  (94, '数据结构', '线性表', '计算机考研408|《数据结构》第二章 2.3线性表的链式表示03|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1QWoxYrEhf', '计算机考研408羊驼老师 讲解 · 播放 182 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '36:49', 0, 51, '计算机考研408羊驼老师', 'seed', '链式表示'),
  (95, '数据结构', '线性表', '计算机考研408|《数据结构》第二章 2.3线性表的链式表示02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1GWoxYkEKD', '计算机考研408羊驼老师 讲解 · 播放 174 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '32:47', 0, 51, '计算机考研408羊驼老师', 'seed', '链式表示'),
  (96, '数据结构', '线性表', '【考研数据结构-线性表-链表3】 完结撒花 好多题都是万变不离其宗，每次做代码题都会有不一样的感受，有时候会忘记之前自己怎么做出来的，有时候会突然脑袋开窍', 'Bilibili', 'https://www.bilibili.com/video/BV1z34y1d7JM', '优质推荐 · 狂暴的南希 制作 · 播放 10719 次 · 与 线性表 高度相关', 'https://i1.hdslb.com/bfs/archive/d89bdef2de5441327985dcd97b89ac4d2d5cf16c.jpg', '33:11', 0, 67, '狂暴的南希', 'seed', '顺序表与链表的比较'),
  (97, '数据结构', '线性表', '王道408数据结构线性表2.37小题（18-34）（注意静态链表跟顺序表的静态分配的概念区别）线性表结束，明天开栈', 'Bilibili', 'https://www.bilibili.com/video/BV1RZ42117ed', 'wz不是喂猪 讲解 · 播放 1045 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/f85b20f2a5085b1b9277f8f070d9ccb2eae26526.jpg', '43:22', 0, 57, 'wz不是喂猪', 'seed', '顺序表与链表的比较'),
  (98, '数据结构', '线性表', '玩转数据结构-第2讲线性表之单链表5', 'Bilibili', 'https://www.bilibili.com/video/BV1f24y1m7Ug', '计算机考研刘财政 讲解 · 播放 350 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/5b7ede184531ea7f9b9a9a6ec902cd29634c89c4.jpg', '51:15', 0, 49, '计算机考研刘财政', 'seed', '顺序表与链表的比较'),
  (99, '数据结构', '线性表', '玩转数据结构-第2讲 线性表之静态，双链表 8', 'Bilibili', 'https://www.bilibili.com/video/BV1dM411C7vR', '计算机考研刘财政 讲解 · 播放 281 次 · 覆盖 线性表 相关内容', 'https://i0.hdslb.com/bfs/archive/7f3c92d9d849d7e34e5de1e2a3c31a710f86ec01.jpg', '48:13', 0, 49, '计算机考研刘财政', 'seed', '顺序表与链表的比较'),
  (100, '数据结构', '线性表', '玩转数据结构-第2讲 线性表之单链表6', 'Bilibili', 'https://www.bilibili.com/video/BV1J8411n7Zk', '计算机考研刘财政 讲解 · 播放 244 次 · 覆盖 线性表 相关内容', 'https://i2.hdslb.com/bfs/archive/5b7ede184531ea7f9b9a9a6ec902cd29634c89c4.jpg', '43:1', 0, 49, '计算机考研刘财政', 'seed', '顺序表与链表的比较');
INSERT INTO `video_resource` (`id`, `subject`, `knowledge_point`, `title`, `platform`, `url`, `reason`, `cover_url`, `duration`, `is_deleted`, `quality_score`, `author`, `crawl_source`, `section`) VALUES
  (101, '数据结构', '栈、队列和数组', '数据结构 第三章 栈、队列和数组', 'Bilibili', 'https://www.bilibili.com/video/BV17At5zRECe', '卓文同学 讲解 · 播放 507 次 · 覆盖 栈、队列和数组 相关内容', 'https://i1.hdslb.com/bfs/archive/92468c514266230f942f39a484d7701e8f515497.jpg', '54:54', 0, 49, '卓文同学', 'seed', '栈'),
  (102, '数据结构', '栈、队列和数组', '数据结构冲刺-栈与队列及其应用', 'Bilibili', 'https://www.bilibili.com/video/BV1tT4nzpEyi', '就是氧气11 讲解 · 播放 3503 次 · 覆盖 栈、队列和数组 相关内容', 'https://i2.hdslb.com/bfs/archive/6045a21e25fce4984d69b37591a31f7b7083e2e0.jpg', '32:27', 0, 45, '就是氧气11', 'seed', '栈'),
  (103, '数据结构', '栈、队列和数组', '《王道408数据结构考研》第三章栈队列数组—重点知识与课后题点播', 'Bilibili', 'https://www.bilibili.com/video/BV1Tr4y1s7Ka', '生活必知必会 讲解 · 播放 1386 次 · 覆盖 栈、队列和数组 相关内容', 'https://i0.hdslb.com/bfs/archive/8bed429962c6b9a712c70cebfd7e00147a840098.jpg', '33:46', 0, 49, '生活必知必会', 'seed', '栈'),
  (104, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列 3.2队列01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1f4oeYrEW6', '计算机考研408羊驼老师 · 播放 242 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '46:20', 0, 39, '计算机考研408羊驼老师', 'seed', '栈'),
  (105, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列  3.4特殊矩阵的压缩存储01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV11oZgYoEoN', '计算机考研408羊驼老师 · 播放 208 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '48:22', 0, 39, '计算机考研408羊驼老师', 'seed', '栈'),
  (106, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列 3.1栈01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1z4oeYkEEj', '计算机考研408羊驼老师 · 播放 176 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '54:3', 0, 39, '计算机考研408羊驼老师', 'seed', '队列'),
  (107, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列 3.3栈和队列的应用01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1kNZ3YHE96', '计算机考研408羊驼老师 · 播放 161 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '44:48', 0, 39, '计算机考研408羊驼老师', 'seed', '队列'),
  (108, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列 3.2队列02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1z4oeYkEnF', '计算机考研408羊驼老师 · 播放 145 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '45:1', 0, 39, '计算机考研408羊驼老师', 'seed', '队列'),
  (109, '数据结构', '栈、队列和数组', '计算机考研408|《数据结构》第三章 栈和队列 3.3栈和队列的应用02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV12oZgYoE2u', '计算机考研408羊驼老师 · 播放 133 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '46:29', 0, 39, '计算机考研408羊驼老师', 'seed', '队列'),
  (110, '数据结构', '栈、队列和数组', '27考研408专业课基础：50min通关数据结构-栈、队列、数组', 'Bilibili', 'https://www.bilibili.com/video/BV1k26cB3EGa', '杰夫408 · 播放 252 次 · 与 栈、队列和数组 相关', 'https://i1.hdslb.com/bfs/archive/20b7d0d1c155934b79641b186744a29641631c03.jpg', '52:8', 0, 37, '杰夫408', 'seed', '队列'),
  (111, '数据结构', '栈、队列和数组', '数据结构 7.栈应用：确认过眼神，我匹配对的括号', 'Bilibili', 'https://www.bilibili.com/video/BV16HHyzaEGx', '西安数学张老师 · 播放 21 次 · 与 栈、队列和数组 相关', 'https://i0.hdslb.com/bfs/archive/19f30a58ba2e1545222e66dd45973ed802fa2d9e.jpg', '30:13', 0, 28, '西安数学张老师', 'seed', '栈和队列的应用'),
  (112, '数据结构', '栈、队列和数组', '【特殊矩阵压缩存储】在一维数组下标的计算公式推导', 'Bilibili', 'https://www.bilibili.com/video/BV1T54y1p7eH', 'CodeLinghu 讲解 · 播放 9329 次 · 覆盖 栈、队列和数组 相关内容', 'https://i0.hdslb.com/bfs/archive/2f00e49fbe8f62b4675cdf97400a3d2d0100a335.jpg', '30:13', 0, 35, 'CodeLinghu', 'seed', '数组和特殊矩阵'),
  (113, '数据结构', '栈、队列和数组', '数据结构冲刺-矩阵与数组的存储与应用', 'Bilibili', 'https://www.bilibili.com/video/BV1ys44zNE1t', '就是氧气11 讲解 · 播放 2435 次 · 覆盖 栈、队列和数组 相关内容', 'https://i1.hdslb.com/bfs/archive/09511641fe112365e65b3ce23f3cf8003a48b868.jpg', '30:36', 0, 41, '就是氧气11', 'seed', '数组和特殊矩阵'),
  (114, '数据结构', '栈、队列和数组', '数据结构强化专题-数组与矩阵', 'Bilibili', 'https://www.bilibili.com/video/BV1DWMKzzEkX', '就是氧气11 讲解 · 播放 1768 次 · 覆盖 栈、队列和数组 相关内容', 'https://i0.hdslb.com/bfs/archive/bb4faeff23d29a29ad49bf528f892225cb0c3820.jpg', '34:41', 0, 41, '就是氧气11', 'seed', '数组和特殊矩阵'),
  (115, '数据结构', '栈、队列和数组', '27数据结构基础-数组与矩阵', 'Bilibili', 'https://www.bilibili.com/video/BV1MKrsBDESZ', '就是氧气11 讲解 · 播放 848 次 · 覆盖 栈、队列和数组 相关内容', 'https://i2.hdslb.com/bfs/archive/c608d7d1d454432ead0636df9688e06686cc4260.jpg', '32:1', 0, 41, '就是氧气11', 'seed', '数组和特殊矩阵'),
  (116, '数据结构', '栈、队列和数组', '27数据结构强化-数组与矩阵选择题专题', 'Bilibili', 'https://www.bilibili.com/video/BV1SULq6FEQ6', '就是氧气11 · 播放 762 次 · 与 栈、队列和数组 相关', 'https://i1.hdslb.com/bfs/archive/a8d57cd4aae77ff186b768817485cc56d4d2d13a.jpg', '31:54', 0, 31, '就是氧气11', 'seed', '数组和特殊矩阵'),
  (117, '数据结构', '串', '《数据结构考研辅导》4.2 串的类型定义、存储结构及其运算（下）', 'Bilibili', 'https://www.bilibili.com/video/BV1VY4y1v76z', '人邮教育中心 讲解 · 播放 140 次 · 覆盖 串 相关内容', 'https://i1.hdslb.com/bfs/archive/f49aef3af652907b7497a8e6d83fc190d0c939f3.jpg', '37:42', 0, 47, '人邮教育中心', 'seed', '串的定义和实现'),
  (118, '数据结构', '串', '3模运算系统与补码的数学定义', 'Bilibili', 'https://www.bilibili.com/video/BV1BM4m1z767', 'math也是柠檬精 · 播放 2508 次 · 与 串 相关', 'https://i0.hdslb.com/bfs/archive/4152206bc47b08f3a60a36cbfaf8df6cc7b9b2db.jpg', '48:19', 0, 25, 'math也是柠檬精', 'seed', '串的定义和实现'),
  (119, '数据结构', '串', '无痛学408计算机考研数据结构|树的定义与术语', 'Bilibili', 'https://www.bilibili.com/video/BV1pBYPzUExL', '李栈讲计算机 · 播放 215 次 · 与 串 相关', 'https://i2.hdslb.com/bfs/archive/bc0eab7094708e927029c3d456a4cbc75fac921e.jpg', '42:6', 0, 35, '李栈讲计算机', 'seed', '串的定义和实现'),
  (120, '数据结构', '串', '计算机考研408|《数据结构》第二章线性表2.1定义|精讲精练零基础速成小白必备一战上岸计算机专业C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1ZQRwY7Eah', '研途计算机考研 · 播放 212 次 · 与 串 相关', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '48:7', 0, 35, '研途计算机考研', 'seed', '串的定义和实现'),
  (121, '数据结构', '串', '计算机考研经典教材带读丨《数据结构》严蔚敏版：6.1树的定义和基本术语', 'Bilibili', 'https://www.bilibili.com/video/BV1Pi7nzcEZ8', '启航计算机考研 · 播放 187 次 · 与 串 相关', 'https://i2.hdslb.com/bfs/archive/af72f7549eaf691a00b2b19b9b082a3d7ea9b26b.jpg', '31:5', 0, 33, '启航计算机考研', 'seed', '串的定义和实现'),
  (122, '数据结构', '串', '数据结构强化专题-KMP字符串匹配', 'Bilibili', 'https://www.bilibili.com/video/BV1NAMgz6EEX', '就是氧气11 讲解 · 播放 2541 次 · 覆盖 串 相关内容', 'https://i1.hdslb.com/bfs/archive/03365dabbef7f1784a5274fc9a7f78d651d8b6fe.jpg', '31:8', 0, 57, '就是氧气11', 'seed', '串的模式匹配'),
  (123, '数据结构', '串', '强化1000题数据结构-KMP字符串匹配', 'Bilibili', 'https://www.bilibili.com/video/BV1CaG4zbELZ', '就是氧气11 讲解 · 播放 1331 次 · 覆盖 串 相关内容', 'https://i0.hdslb.com/bfs/archive/0a97851adc7f77bd81c7a3462953aeb54bab94dc.jpg', '35:34', 0, 57, '就是氧气11', 'seed', '串的模式匹配'),
  (124, '数据结构', '串', '27数据结构强化-字符串匹配KMP专题', 'Bilibili', 'https://www.bilibili.com/video/BV1MF5f6EE8m', '就是氧气11 讲解 · 播放 956 次 · 覆盖 串 相关内容', 'https://i1.hdslb.com/bfs/archive/6adca29334a5d3bed33ef3aa0fb18a361cb76c41.jpg', '36:32', 0, 57, '就是氧气11', 'seed', '串的模式匹配'),
  (125, '数据结构', '串', '3.2  串的存储结构与操作-1', 'Bilibili', 'https://www.bilibili.com/video/BV1hu411r7gX', 'Taylor读研版 讲解 · 播放 1015 次 · 覆盖 串 相关内容', 'https://i2.hdslb.com/bfs/archive/19cab011f2d2e8db14331da787d7b4dd16f187af.jpg', '33:27', 0, 53, 'Taylor读研版', 'seed', '串的模式匹配'),
  (126, '数据结构', '串', '数据结构-6-串---串的基本概念--串的模式匹配--KMP算法详解', 'Bilibili', 'https://www.bilibili.com/video/BV1o8hPzTErX', '熊熊计算机课堂 讲解 · 播放 1173 次 · 覆盖 串 相关内容', 'https://i0.hdslb.com/bfs/archive/e4b34c490f75f7ab90478c2db19f21fc12e85529.jpg', '37:6', 0, 55, '熊熊计算机课堂', 'seed', '串的模式匹配'),
  (127, '数据结构', '树与二叉树', '数据结构-9.1-树与二叉树的基本概念、二叉树的性质与特点、树、森林与二叉树的相互转换', 'Bilibili', 'https://www.bilibili.com/video/BV1QoFDzjELC', '熊熊计算机课堂 讲解 · 播放 998 次 · 覆盖 树与二叉树 相关内容', 'https://i1.hdslb.com/bfs/archive/be636d80f3814b4d99b0b8284a6fb296cd7ab454.jpg', '37:50', 0, 55, '熊熊计算机课堂', 'seed', '树的基本概念'),
  (128, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.3二叉树的遍历和线索二叉树02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1uioDY6E4y', '计算机考研408羊驼老师 讲解 · 播放 177 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/f1693da5c79f877798c9a7a24f85affe7bb72526.jpg', '32:24', 0, 51, '计算机考研408羊驼老师', 'seed', '树的基本概念'),
  (129, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.1树的基本概念和术语02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1MBoDYuEsf', '计算机考研408羊驼老师 讲解 · 播放 106 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '44:8', 0, 51, '计算机考研408羊驼老师', 'seed', '树的基本概念'),
  (130, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.1树的基本概念和术语01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1MBoDYuExG', '计算机考研408羊驼老师 讲解 · 播放 102 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '47:0', 0, 51, '计算机考研408羊驼老师', 'seed', '树的基本概念'),
  (131, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.2二叉树02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1MBoDYgEDv', '计算机考研408羊驼老师 讲解 · 播放 95 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '45:46', 0, 46, '计算机考研408羊驼老师', 'seed', '树的基本概念'),
  (132, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第三章 第四章 树与二叉树 4.3二叉树的遍历和线索二叉树01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1uioDY6EhM', '计算机考研408羊驼老师 讲解 · 播放 88 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/f1693da5c79f877798c9a7a24f85affe7bb72526.jpg', '45:43', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的概念'),
  (133, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.5树与二叉树的应用03|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1YHZnYaEKd', '计算机考研408羊驼老师 讲解 · 播放 87 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '51:15', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的概念'),
  (134, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.4树与森林03|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1VHZnYaE5s', '计算机考研408羊驼老师 讲解 · 播放 85 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/f1693da5c79f877798c9a7a24f85affe7bb72526.jpg', '32:17', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的概念'),
  (135, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.2二叉树01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1MBoDYuEJn', '计算机考研408羊驼老师 讲解 · 播放 84 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '47:15', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的概念'),
  (136, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.5 树与二叉树的应用01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1VHZnYaEgk', '计算机考研408羊驼老师 讲解 · 播放 80 次 · 覆盖 树与二叉树 相关内容', 'https://i1.hdslb.com/bfs/archive/e5e229dd6339c7d2f42efb3169c56a6eceae385d.jpg', '45:15', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的概念'),
  (137, '数据结构', '树与二叉树', '数据结构强化专题-树与二叉树代码大题', 'Bilibili', 'https://www.bilibili.com/video/BV1zBg2zuE74', '就是氧气11 讲解 · 播放 3505 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/9c82cbadc371fd6295a86b9c6f8c7294469f3b51.jpg', '44:51', 0, 57, '就是氧气11', 'seed', '二叉树的遍历'),
  (138, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.3二叉树的遍历和线索二叉树03|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1uioDY6EaT', '计算机考研408羊驼老师 讲解 · 播放 64 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '51:16', 0, 46, '计算机考研408羊驼老师', 'seed', '二叉树的遍历'),
  (139, '数据结构', '树与二叉树', '【超详细】25王道数据结构课后题逐题精讲5.2二叉树的概念', 'Bilibili', 'https://www.bilibili.com/video/BV1eT421U7vv', '计算机考研Cocoa学姐 讲解 · 播放 4030 次 · 覆盖 树与二叉树 相关内容', 'https://i1.hdslb.com/bfs/archive/ad684d40b2b8593f17f6f14cd6c8b0b9a19c7261.jpg', '30:40', 0, 39, '计算机考研Cocoa学姐', 'seed', '二叉树的遍历'),
  (140, '数据结构', '树与二叉树', '数据结构强化专题-线索二叉树与Morris遍历', 'Bilibili', 'https://www.bilibili.com/video/BV1irN1zSE3s', '就是氧气11 讲解 · 播放 2551 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/85b9860fadceb7e6983fdee89d40b03bd87a0f98.jpg', '41:17', 0, 41, '就是氧气11', 'seed', '二叉树的遍历'),
  (141, '数据结构', '树与二叉树', '数据结构强化专题-二叉树的遍历', 'Bilibili', 'https://www.bilibili.com/video/BV1RdM4zMEjW', '就是氧气11 讲解 · 播放 1899 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/963e367a465252d835816477390b97328a1ad734.jpg', '42:16', 0, 41, '就是氧气11', 'seed', '二叉树的遍历'),
  (142, '数据结构', '树与二叉树', '数据结构与算法基础--第07周11--5.5 遍历二叉树和线索二叉树1--遍历二叉树', 'Bilibili', 'https://www.bilibili.com/video/BV1xb411A7NV', '王卓老师 讲解 · 播放 40669 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/72dfe8859396cbb5704d507f98255a1a158a2dcd.jpg', '30:51', 0, 59, '王卓老师', 'seed', '线索二叉树'),
  (143, '数据结构', '树与二叉树', '数据结构树与二叉树', 'Bilibili', 'https://www.bilibili.com/video/BV1jW2pYUE35', '布偶小喵11408 讲解 · 播放 106 次 · 覆盖 树与二叉树 相关内容', 'https://i2.hdslb.com/bfs/archive/6b09d3f1c9ffa6b5a2eb5f654cbf1be27df463c8.jpg', '54:21', 0, 45, '布偶小喵11408', 'seed', '线索二叉树'),
  (144, '数据结构', '树与二叉树', '7.6 线索二叉树《数据结构与算法（Java版）》陈平上课实录', 'Bilibili', 'https://www.bilibili.com/video/BV1J44y1B7Kk', '游戏只会红警和三国 · 播放 840 次 · 与 树与二叉树 相关', 'https://i0.hdslb.com/bfs/archive/62daf8284aef5e88c411cb2c1893baa5aa9695db.png', '55:37', 0, 41, '游戏只会红警和三国', 'seed', '线索二叉树'),
  (145, '数据结构', '树与二叉树', '4.22.线索二叉树：中序遍历_代码和测试（选学）', 'Bilibili', 'https://www.bilibili.com/video/BV1q84y1a7Pp', '彭彭学编程 · 播放 1092 次 · 与 树与二叉树 相关', 'https://i1.hdslb.com/bfs/archive/9cff7bdd8049e8b0f92b3c8389c8fef4d9d01d28.jpg', '34:51', 0, 25, '彭彭学编程', 'seed', '线索二叉树'),
  (146, '数据结构', '树与二叉树', '线索二叉树及408历年真题', 'Bilibili', 'https://www.bilibili.com/video/BV1bd4y1m7gr', '头秃萌Xin · 播放 294 次 · 与 树与二叉树 相关', 'https://i0.hdslb.com/bfs/archive/2fe1f213a60b308a9948a768910ae982663bf275.jpg', '42:44', 0, 17, '头秃萌Xin', 'seed', '线索二叉树'),
  (147, '数据结构', '树与二叉树', '计算机考研408|《数据结构》第四章 树与二叉树 4.4树与森林02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1VHZnYaEgt', '计算机考研408羊驼老师 讲解 · 播放 71 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '34:29', 0, 46, '计算机考研408羊驼老师', 'seed', '树、森林'),
  (148, '数据结构', '树与二叉树', '43数据结构第六章10哈夫曼树', 'Bilibili', 'https://www.bilibili.com/video/BV13jm7BpEWW', '小贱课堂 · 播放 1494 次 · 与 树与二叉树 相关', 'https://i2.hdslb.com/bfs/archive/7fce335df25709b9bf1bb86781bc7b2024ac6394.jpg', '35:20', 0, 41, '小贱课堂', 'seed', '树、森林'),
  (149, '数据结构', '树与二叉树', '25新版玩转数据结构：030-第五讲-考点六：树、森林和二叉树的关系', 'Bilibili', 'https://www.bilibili.com/video/BV1pKSjYmEkE', '计算机考研刘财政 · 播放 110 次 · 与 树与二叉树 相关', 'https://i2.hdslb.com/bfs/archive/53716ee8c69a32dfbf1fd73027d9d62317dd0343.jpg', '30:14', 0, 33, '计算机考研刘财政', 'seed', '树、森林'),
  (150, '数据结构', '树与二叉树', '第五章  考点六：树、森林和二叉树的关系', 'Bilibili', 'https://www.bilibili.com/video/BV1nj421Z711', '计算机考研刘财政 · 播放 100 次 · 与 树与二叉树 相关', 'https://i1.hdslb.com/bfs/archive/6392ca615ae6b751f15e7edad586a4ab90f96f66.jpg', '45:6', 0, 15, '计算机考研刘财政', 'seed', '树、森林'),
  (151, '数据结构', '树与二叉树', '数据结构复盘—二叉树的遍历（前序中序后序）、线索二叉树（构造）、树、森林（二叉树的转换） 20240418', 'Bilibili', 'https://www.bilibili.com/video/BV1ht421j7DA', '布偶小喵11408 · 播放 164 次 · 与 树与二叉树 相关', 'https://i1.hdslb.com/bfs/archive/1c9b98615b46deb618b8836f149c5daa502e4ba3.jpg', '48:17', 0, 29, '布偶小喵11408', 'seed', '树、森林'),
  (152, '数据结构', '树与二叉树', '数据结构（试听） 5.5树与二叉树的应用', 'Bilibili', 'https://www.bilibili.com/video/BV1v64y1W7DW', 'Now_or_Nerver 讲解 · 播放 297 次 · 覆盖 树与二叉树 相关内容', 'https://i1.hdslb.com/bfs/archive/38e88d1b8cb73eeed7337b84909ee1cf4d447d86.jpg', '48:45', 0, 49, 'Now_or_Nerver', 'seed', '树与二叉树的应用'),
  (153, '数据结构', '树与二叉树', '【24贵大计算机】初试课程 树与二叉树的应用/贵州大学计算机840程序设计与数据结构/24贵大计算机考研初试课程', 'Bilibili', 'https://www.bilibili.com/video/BV1tz4y137Dv', '文彦考研专业课 讲解 · 播放 193 次 · 覆盖 树与二叉树 相关内容', 'https://i1.hdslb.com/bfs/archive/68e84f9019997e86a77167d9de11e8c24b4789ab.jpg', '40:17', 0, 49, '文彦考研专业课', 'seed', '树与二叉树的应用'),
  (154, '数据结构', '树与二叉树', '27数据结构强化-二叉树的性质与遍历选择题专题', 'Bilibili', 'https://www.bilibili.com/video/BV1bTLx6tEaZ', '就是氧气11 讲解 · 播放 916 次 · 覆盖 树与二叉树 相关内容', 'https://i2.hdslb.com/bfs/archive/ffde609ed35f6ebefc6c6194f4c17ab948279672.jpg', '40:39', 0, 41, '就是氧气11', 'seed', '树与二叉树的应用'),
  (155, '数据结构', '树与二叉树', '27数据结构强化-二叉树的性质与遍历专题', 'Bilibili', 'https://www.bilibili.com/video/BV1d4Ly64EDC', '就是氧气11 讲解 · 播放 851 次 · 覆盖 树与二叉树 相关内容', 'https://i0.hdslb.com/bfs/archive/0e91f84dc701fe2cf3e18160b152abeb8ad290e5.jpg', '36:10', 0, 41, '就是氧气11', 'seed', '树与二叉树的应用'),
  (156, '数据结构', '树与二叉树', '无痛学408计算机考研数据结构|平衡二叉树的概念与调整', 'Bilibili', 'https://www.bilibili.com/video/BV1JW2vB2EB7', '李栈讲计算机 · 播放 124 次 · 与 树与二叉树 相关', 'https://i2.hdslb.com/bfs/archive/bc2a03fb624bff4e775d1715b05f58b6938dd40d.jpg', '48:16', 0, 35, '李栈讲计算机', 'seed', '树与二叉树的应用'),
  (157, '数据结构', '图', '数据结构冲刺-图的基本应用', 'Bilibili', 'https://www.bilibili.com/video/BV1cdWrz8EEq', '就是氧气11 讲解 · 播放 2656 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/7c71b60771861cd9215f62484eaea28caa86c5d5.jpg', '40:40', 0, 57, '就是氧气11', 'seed', '图的基本概念'),
  (158, '数据结构', '图', '数据结构强化专题-图的基本概念与存储', 'Bilibili', 'https://www.bilibili.com/video/BV1DJKWzEEqZ', '就是氧气11 讲解 · 播放 2024 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/330c1c6055c9bf6a347407bd685b7495c933d04a.jpg', '40:28', 0, 57, '就是氧气11', 'seed', '图的基本概念'),
  (159, '数据结构', '图', '27数据结构强化-图的概念与存储专题', 'Bilibili', 'https://www.bilibili.com/video/BV1rPVA65Eyc', '就是氧气11 讲解 · 播放 777 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/f05dfda65cc8273416fb8f327c4bc79ee0d0d026.jpg', '50:13', 0, 47, '就是氧气11', 'seed', '图的基本概念'),
  (160, '数据结构', '图', '27数据结构强化-图的概念与存储选择题专题', 'Bilibili', 'https://www.bilibili.com/video/BV157VA6vEaa', '就是氧气11 讲解 · 播放 693 次 · 覆盖 图 相关内容', 'https://i1.hdslb.com/bfs/archive/9870bdbf7a0527a258317fd340596320b657db11.jpg', '32:44', 0, 47, '就是氧气11', 'seed', '图的基本概念'),
  (161, '数据结构', '图', '无痛学408计算机考研数据结构|B树的基本概念', 'Bilibili', 'https://www.bilibili.com/video/BV1B2CLBEEyM', '李栈讲计算机 讲解 · 播放 312 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/4f5153cf0f0e5d1021bf253f0f2e1642b682f08b.jpg', '43:37', 0, 51, '李栈讲计算机', 'seed', '图的基本概念'),
  (162, '数据结构', '图', '【第1版用心版】24考研408王道课后题|数据结构—图的存储', 'Bilibili', 'https://www.bilibili.com/video/BV1Bz4y1L7kr', '计算机考研408小言 讲解 · 播放 1338 次 · 覆盖 图 相关内容', 'https://i1.hdslb.com/bfs/archive/35bf39524f06466e256b03fe20ca158b900a4a37.jpg', '40:50', 0, 59, '计算机考研408小言', 'seed', '图的存储及基本操作'),
  (163, '数据结构', '图', '27数据结构基础-图的存储', 'Bilibili', 'https://www.bilibili.com/video/BV1GS6eBEEFu', '就是氧气11 讲解 · 播放 594 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/58cd05a87d3629b2deb9d57581756777020bb3a2.jpg', '32:5', 0, 47, '就是氧气11', 'seed', '图的存储及基本操作'),
  (164, '数据结构', '图', '无痛学408计算机考研数据结构|队列的链式存储之进与出', 'Bilibili', 'https://www.bilibili.com/video/BV1YfanzLER4', '李栈讲计算机 讲解 · 播放 229 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/0d74e739767d7c17451a9b2ce8bfaf1d4616f496.jpg', '36:16', 0, 51, '李栈讲计算机', 'seed', '图的存储及基本操作'),
  (165, '数据结构', '图', '计算机考研408|40 24《数据结构》第五章 图 5.2图的存储和基本操作02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1aqdAY6EAg', '计算机考研408羊驼老师 讲解 · 播放 196 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/17a2e8aef5619b9e4538aa395f527583a199e88b.jpg', '37:51', 0, 51, '计算机考研408羊驼老师', 'seed', '图的存储及基本操作'),
  (166, '数据结构', '图', '快速学懂数据结构图的应用、最小生成树，最短路径，关键路径，最早、最晚开始时间、时间余量', 'Bilibili', 'https://www.bilibili.com/video/BV1Mf421q7bH', '优质推荐 · 一惭何知夏 制作 · 播放 13381 次 · 与 图 高度相关', 'https://i1.hdslb.com/bfs/archive/d17b64a1cac7bf3600be8ce95ec6c1f1d054be70.jpg', '37:34', 0, 65, '一惭何知夏', 'seed', '图的遍历'),
  (167, '数据结构', '图', '1小时速通考研数据结构图的应用代码题，秒杀法！看完直接拿下！', 'Bilibili', 'https://www.bilibili.com/video/BV16nSYBQEdg', '芒果学长奥 讲解 · 播放 4688 次 · 覆盖 图 相关内容', 'https://i2.hdslb.com/bfs/archive/3d2c16601f2f479417746de8903ce0c7b31e7936.jpg', '57:37', 0, 57, '芒果学长奥', 'seed', '图的遍历'),
  (168, '数据结构', '图', '「数据结构·算法模拟」图——图的应用', 'Bilibili', 'https://www.bilibili.com/video/BV1RGNueWEb1', '浅夏柒韵 讲解 · 播放 2561 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/d604e2af8865e619fe4c966d03fee274db08611a.png', '44:47', 0, 55, '浅夏柒韵', 'seed', '图的遍历'),
  (169, '数据结构', '图', '计算机考研408| 42 24《数据结构》第五章 图 5.3图的遍历01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1a6dNYjEsX', '计算机考研408羊驼老师 讲解 · 播放 197 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/2828f16cb897105b219b4feefd520e27e38bd668.jpg', '34:59', 0, 51, '计算机考研408羊驼老师', 'seed', '图的遍历'),
  (170, '数据结构', '图', '计算机考研408| 43 24《数据结构》第五章 图 5.3图的遍历02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1vmdoYYEsD', '计算机考研408羊驼老师 讲解 · 播放 158 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/41662447fe293521bf18fa0298c7082f62284940.jpg', '32:47', 0, 51, '计算机考研408羊驼老师', 'seed', '图的遍历'),
  (171, '数据结构', '图', '【第1版用心版】24考研408王道课后题|数据结构—图P183', 'Bilibili', 'https://www.bilibili.com/video/BV1Vp4y1E73j', '计算机考研408小言 讲解 · 播放 2381 次 · 覆盖 图 相关内容', 'https://i1.hdslb.com/bfs/archive/35bf39524f06466e256b03fe20ca158b900a4a37.jpg', '51:55', 0, 59, '计算机考研408小言', 'seed', '图的应用'),
  (172, '数据结构', '图', '27数据结构强化-有向无环图的应用专题', 'Bilibili', 'https://www.bilibili.com/video/BV1w8Vb6pE4j', '就是氧气11 讲解 · 播放 816 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/b21de1b476d9afb670235d9f1e35e22a5553513e.jpg', '42:59', 0, 57, '就是氧气11', 'seed', '图的应用'),
  (173, '数据结构', '图', '【408算法代码带练】图部分(十)图的DFS和BFS代码讲解和用法', 'Bilibili', 'https://www.bilibili.com/video/BV1k1qPYEEpn', '阿炜408 讲解 · 播放 1542 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/8517d684e8e27233e00f7ad60b87c962dfc4c9eb.jpg', '38:47', 0, 55, '阿炜408', 'seed', '图的应用'),
  (174, '数据结构', '图', '计算机考研408数据结构|图板块|详细版|搞懂不会的|', 'Bilibili', 'https://www.bilibili.com/video/BV1C14y12711', '计算机考研408小言 讲解 · 播放 667 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/ba2f9d46224d0b9ea78fead9484086dea1af7456.jpg', '50:52', 0, 51, '计算机考研408小言', 'seed', '图的应用'),
  (175, '数据结构', '图', '计算机考研408| 45 24《数据结构》第五章 图 5.4图的应用02|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1KQ5kzUENv', '计算机考研408羊驼老师 讲解 · 播放 293 次 · 覆盖 图 相关内容', 'https://i0.hdslb.com/bfs/archive/2828f16cb897105b219b4feefd520e27e38bd668.jpg', '35:23', 0, 51, '计算机考研408羊驼老师', 'seed', '图的应用'),
  (176, '数据结构', '查找', '数据结构冲刺-基本查找与树形查找', 'Bilibili', 'https://www.bilibili.com/video/BV1ETWWzuEsr', '就是氧气11 讲解 · 播放 2190 次 · 覆盖 查找 相关内容', 'https://i1.hdslb.com/bfs/archive/dca7ba073ded9ef16b09f97aa83b987d5c38cb26.jpg', '30:10', 0, 57, '就是氧气11', 'seed', '查找的基本概念'),
  (177, '数据结构', '查找', '数据结构强化专题-树的概念与性质', 'Bilibili', 'https://www.bilibili.com/video/BV1ChM1zMEic', '就是氧气11 讲解 · 播放 1924 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/90ab5b2a325c05bf8330a7c2a49bdc203589959c.jpg', '39:24', 0, 41, '就是氧气11', 'seed', '查找的基本概念'),
  (178, '数据结构', '查找', '【考研408数据结构】01数据结构的基本概念，算法和算法的评价', 'Bilibili', 'https://www.bilibili.com/video/BV1quxfzrEr2', '研胜计算机考研408 · 播放 427 次 · 与 查找 相关', 'https://i2.hdslb.com/bfs/archive/08c7efa9148bf984ac83a58dd69491f1575f984d.jpg', '54:16', 0, 33, '研胜计算机考研408', 'seed', '查找的基本概念'),
  (179, '数据结构', '查找', '无痛学408计算机考研数据结构|图的基本概念', 'Bilibili', 'https://www.bilibili.com/video/BV1ki4JzCEhA', '李栈讲计算机 · 播放 275 次 · 与 查找 相关', 'https://i1.hdslb.com/bfs/archive/e5ab59916a3487d7204b56b768cf9c78f31b0534.jpg', '30:51', 0, 35, '李栈讲计算机', 'seed', '查找的基本概念'),
  (180, '数据结构', '查找', '408数据结构部分-图的基本概念', 'Bilibili', 'https://www.bilibili.com/video/BV1Xa411P7XN', '头秃萌Xin · 播放 264 次 · 与 查找 相关', 'https://i1.hdslb.com/bfs/archive/b94a32201f9f93145eeb14884f76ed982782193f.jpg', '39:24', 0, 31, '头秃萌Xin', 'seed', '查找的基本概念'),
  (181, '数据结构', '查找', '计算机考研408| 51 24《数据结构》第六章 查找 6.2顺序查找和折半查找01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1AkG9zqE3K', '计算机考研408羊驼老师 讲解 · 播放 294 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/2828f16cb897105b219b4feefd520e27e38bd668.jpg', '31:6', 0, 51, '计算机考研408羊驼老师', 'seed', '顺序查找和折半查找'),
  (182, '数据结构', '查找', '25新版玩转数据结构：042-第七讲-考点三：折半查找', 'Bilibili', 'https://www.bilibili.com/video/BV1zYSLYgE8Q', '计算机考研刘财政 讲解 · 播放 143 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/53716ee8c69a32dfbf1fd73027d9d62317dd0343.jpg', '44:28', 0, 49, '计算机考研刘财政', 'seed', '顺序查找和折半查找'),
  (183, '数据结构', '查找', '56.第八章折半查找2', 'Bilibili', 'https://www.bilibili.com/video/BV14HXjBoEDT', '小贱课堂 讲解 · 播放 368 次 · 覆盖 查找 相关内容', 'https://i1.hdslb.com/bfs/archive/a14b40cb95da405886a7272cdd060a3a6b319449.jpg', '37:47', 0, 47, '小贱课堂', 'seed', '顺序查找和折半查找'),
  (184, '数据结构', '查找', '第七章  考点三：折半查找', 'Bilibili', 'https://www.bilibili.com/video/BV1Ex4y1Q7f4', '计算机考研刘财政 讲解 · 播放 58 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/8cebbdc26e154ebc507ec94437b6781dc83db5ab.jpg', '54:8', 0, 42, '计算机考研刘财政', 'seed', '顺序查找和折半查找'),
  (185, '数据结构', '查找', '27数据结构基础-顺序表与链表', 'Bilibili', 'https://www.bilibili.com/video/BV1NXquBbE9z', '就是氧气11 讲解 · 播放 1841 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/f34c2f71ee2ca97c1b45da767bb7a5f78a2a89ef.jpg', '39:49', 0, 41, '就是氧气11', 'seed', '顺序查找和折半查找'),
  (186, '数据结构', '查找', '22计算机考研～408考纲新增内容精讲～红黑树！快来学习！（烫嘴）', 'Bilibili', 'https://www.bilibili.com/video/BV1mU4y1w7XM', '计算机考研大师兄 讲解 · 播放 36186 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/6436aa0cf6878274ad814b501753155465e13e41.jpg', '35:7', 0, 41, '计算机考研大师兄', 'seed', '树型查找'),
  (187, '数据结构', '查找', '【408真题速通】哈夫曼树：真题考察11次，真题考法全掌握', 'Bilibili', 'https://www.bilibili.com/video/BV168sHzzEE1', '王道计算机教育 讲解 · 播放 23144 次 · 覆盖 查找 相关内容', 'https://i1.hdslb.com/bfs/archive/7c19cd9c87b5162a9d9d0ef27c8d513cf2d34cd4.jpg', '49:36', 0, 37, '王道计算机教育', 'seed', '树型查找'),
  (188, '数据结构', '查找', '数据结构纯菜比捞分指南代码篇-二叉树', 'Bilibili', 'https://www.bilibili.com/video/BV1cb4y1T7aV', '白话拆解数据结构 讲解 · 播放 33013 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/34be4930962d65b1ba24bf6506019b9103738c1a.jpg', '42:39', 0, 49, '白话拆解数据结构', 'seed', '树型查找'),
  (189, '数据结构', '查找', '408数据结构部分-树型查找_二叉排序树BST', 'Bilibili', 'https://www.bilibili.com/video/BV1yP41157gV', '头秃萌Xin 讲解 · 播放 238 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/42a471d7a74239cbf7ddd6e97e50e2192d23e9f5.jpg', '30:43', 0, 47, '头秃萌Xin', 'seed', '树型查找'),
  (190, '数据结构', '查找', '408数据结构部分-树型查找_平衡二叉树AVL', 'Bilibili', 'https://www.bilibili.com/video/BV1kd4y1d7Tu', '头秃萌Xin 讲解 · 播放 168 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/06796691d76c597beedec7a4e2cd2f21baba8502.jpg', '48:39', 0, 47, '头秃萌Xin', 'seed', '树型查找'),
  (191, '数据结构', '查找', '【数据结构期末速成课】 | 第七章 查找', 'Bilibili', 'https://www.bilibili.com/video/BV1k7LG65Eh5', '令狐冲计算机考研 讲解 · 播放 2361 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/272de39a530dd94e8fa39d7a215de5b6c01294bd.jpg', '31:53', 0, 55, '令狐冲计算机考研', 'seed', '散列查找'),
  (192, '数据结构', '查找', '强化1000题数据结构-查找第一部分', 'Bilibili', 'https://www.bilibili.com/video/BV1vA8VzXEBL', '就是氧气11 讲解 · 播放 2061 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/d9a58584df409407006ce1ef8b8195de4f92e4b4.jpg', '34:49', 0, 57, '就是氧气11', 'seed', '散列查找'),
  (193, '数据结构', '查找', '7.数据结构·必备代码——查找', 'Bilibili', 'https://www.bilibili.com/video/BV1D2Nde2EWk', '浅夏柒韵 讲解 · 播放 1775 次 · 覆盖 查找 相关内容', 'https://i1.hdslb.com/bfs/archive/0240e2dfe8953baa34b9f91d13080b4884766e08.png', '38:16', 0, 57, '浅夏柒韵', 'seed', '散列查找'),
  (194, '数据结构', '查找', '数据结构强化专题-基础查找', 'Bilibili', 'https://www.bilibili.com/video/BV1X2K7ziErK', '就是氧气11 讲解 · 播放 1755 次 · 覆盖 查找 相关内容', 'https://i0.hdslb.com/bfs/archive/2596177acbf91044e9ceef03a07c4b7c138c25df.jpg', '31:49', 0, 57, '就是氧气11', 'seed', '散列查找'),
  (195, '数据结构', '查找', '零壹计算机考研第一次直播试讲课 -- 哈希查找', 'Bilibili', 'https://www.bilibili.com/video/BV1BT4y1P795', '零壹考研数学号 讲解 · 播放 1495 次 · 覆盖 查找 相关内容', 'https://i2.hdslb.com/bfs/archive/b41657317b7a1da0952ddfb209b8d73049c77d9d.jpg', '36:43', 0, 57, '零壹考研数学号', 'seed', '散列查找'),
  (196, '数据结构', '排序', '【408真题速通】内部排序的按趟模拟：带你复习408内部排序，考前提分必看', 'Bilibili', 'https://www.bilibili.com/video/BV1fxCxBCEEF', '优质推荐 · 王道计算机教育 制作 · 播放 29412 次 · 与 排序 高度相关', 'https://i0.hdslb.com/bfs/archive/4da80c43792647198f5435ea537c5ea46f005b5b.jpg', '46:4', 0, 65, '王道计算机教育', 'seed', '排序的基本概念'),
  (197, '数据结构', '排序', '24考研408（计算机专业基础综合）真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV17c41187Us', '优质推荐 · AcKing_专业的IT教育品牌 制作 · 播放 11151 次 · 与 排序 高度相关', 'https://i2.hdslb.com/bfs/archive/8ef9255b9f86261bcf5782186211bbbbb50c9feb.png', '45:30', 0, 41, 'AcKing_专业的IT教育品牌', 'seed', '排序的基本概念'),
  (198, '数据结构', '排序', '基数排序代码(C/C++链式实现) 细到爆炸!', 'Bilibili', 'https://www.bilibili.com/video/BV1afTrzzEri', '优质推荐 · 蓝不过海呀 制作 · 播放 25555 次 · 与 排序 高度相关', 'https://i2.hdslb.com/bfs/archive/914f1ed12dfda0e3d6bbf532b7bee512ec70a9a8.jpg', '31:32', 0, 63, '蓝不过海呀', 'seed', '排序的基本概念'),
  (199, '数据结构', '排序', '快排的考法汇总（1）', 'Bilibili', 'https://www.bilibili.com/video/BV155h2zEEx3', '22408练习生 讲解 · 播放 1124 次 · 覆盖 排序 相关内容', 'https://i2.hdslb.com/bfs/archive/b48a9b1b4554647a5a2969e99d1f8d41a85fa689.jpg', '39:57', 0, 25, '22408练习生', 'seed', '排序的基本概念'),
  (200, '数据结构', '排序', '计算机考研408| 60 24《数据结构》第七章 排序 7.1排序概念和插入排序|零基础考研必备 小白速成 C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1dAj7zwEaL', '计算机考研408羊驼老师 讲解 · 播放 270 次 · 覆盖 排序 相关内容', 'https://i0.hdslb.com/bfs/archive/2828f16cb897105b219b4feefd520e27e38bd668.jpg', '38:27', 0, 51, '计算机考研408羊驼老师', 'seed', '排序的基本概念');
INSERT INTO `video_resource` (`id`, `subject`, `knowledge_point`, `title`, `platform`, `url`, `reason`, `cover_url`, `duration`, `is_deleted`, `quality_score`, `author`, `crawl_source`, `section`) VALUES
  (201, '数据结构', '排序', '1小时速通考研数据结构排序代码，看完直接轻松拿下！', 'Bilibili', 'https://www.bilibili.com/video/BV1iy2aBvE7F', '芒果学长奥 讲解 · 播放 3743 次 · 覆盖 排序 相关内容', 'https://i1.hdslb.com/bfs/archive/aa791483e4664dc98d1f0dc141a8abdf42acb1ef.jpg', '47:54', 0, 57, '芒果学长奥', 'seed', '内部排序'),
  (202, '数据结构', '排序', '数据结构强化专题-外部排序', 'Bilibili', 'https://www.bilibili.com/video/BV1XtgozdEoj', '就是氧气11 讲解 · 播放 2751 次 · 覆盖 排序 相关内容', 'https://i1.hdslb.com/bfs/archive/3671ca2102dd55ee63ae6844e225bbbca851e5eb.jpg', '32:59', 0, 57, '就是氧气11', 'seed', '内部排序'),
  (203, '数据结构', '排序', '数据结构冲刺-内部排序算法', 'Bilibili', 'https://www.bilibili.com/video/BV1gEstz3EWi', '就是氧气11 讲解 · 播放 2566 次 · 覆盖 排序 相关内容', 'https://i1.hdslb.com/bfs/archive/af0cb9d099b0f041d1ac64ffea340525287ae97b.jpg', '46:3', 0, 57, '就是氧气11', 'seed', '内部排序'),
  (204, '数据结构', '排序', '8.数据结构·必备代码——排序', 'Bilibili', 'https://www.bilibili.com/video/BV1YqKNeyEQr', '浅夏柒韵 讲解 · 播放 2529 次 · 覆盖 排序 相关内容', 'https://i1.hdslb.com/bfs/archive/b23bdcedce236963e995ef6f92acff8d17e94400.png', '40:12', 0, 57, '浅夏柒韵', 'seed', '内部排序'),
  (205, '数据结构', '排序', '数据结构强化专题-内部排序', 'Bilibili', 'https://www.bilibili.com/video/BV1qxK1z9EhD', '就是氧气11 讲解 · 播放 2205 次 · 覆盖 排序 相关内容', 'https://i2.hdslb.com/bfs/archive/63d988c822f3581500e91ef9db9cdad5b6dcee6f.jpg', '46:13', 0, 57, '就是氧气11', 'seed', '内部排序'),
  (206, '数据结构', '排序', '408数据结构排序 最后一部分 外部排序 （这里我也不是很熟练 大家海涵）', 'Bilibili', 'https://www.bilibili.com/video/BV1vG4y1G7JL', '阿涛的三件事 讲解 · 播放 1644 次 · 覆盖 排序 相关内容', 'https://i2.hdslb.com/bfs/archive/4d2862c9ec9c5eec7dedca715f5e48857c1cadaf.jpg', '34:33', 0, 57, '阿涛的三件事', 'seed', '外部排序'),
  (207, '数据结构', '排序', '「数据结构」外部排序，外排读写次数计算，补充虚段数计算', 'Bilibili', 'https://www.bilibili.com/video/BV1jf4y1i7LQ', '熊哥保佑你 讲解 · 播放 4402 次 · 覆盖 排序 相关内容', 'https://i1.hdslb.com/bfs/archive/1bcd8503e4b5c676e3f5c677d2a9cc51d33cfd8d.jpg', '47:31', 0, 55, '熊哥保佑你', 'seed', '外部排序'),
  (208, '数据结构', '排序', '27数据结构强化-外部排序专题', 'Bilibili', 'https://www.bilibili.com/video/BV18bEs6NEDJ', '就是氧气11 讲解 · 播放 708 次 · 覆盖 排序 相关内容', 'https://i0.hdslb.com/bfs/archive/381ea8d46d8b33ac59342a0ba6460899d7bad81d.jpg', '38:0', 0, 47, '就是氧气11', 'seed', '外部排序'),
  (209, '数据结构', '排序', '408 外部排序 2025年', 'Bilibili', 'https://www.bilibili.com/video/BV1MX1uYbEA4', '焦糖柠汁 讲解 · 播放 394 次 · 覆盖 排序 相关内容', 'https://i2.hdslb.com/bfs/archive/89b25fca1854529b882fb19de6fd43e11207394f.jpg', '44:47', 0, 45, '焦糖柠汁', 'seed', '外部排序'),
  (210, '数据结构', '排序', '6-3-1 数据通路 —— CPU内部单总线结构（无字幕版）', 'Bilibili', 'https://www.bilibili.com/video/BV1tYzzYwEt3', '湖科大教书匠 · 播放 27383 次 · 与 排序 相关', 'https://i0.hdslb.com/bfs/archive/f93320dbbd4c7d4e0aa5c8e0a60ecceb8a2ac89e.jpg', '31:43', 0, 39, '湖科大教书匠', 'seed', '外部排序'),
  (211, '计算机组成原理', '计算机系统概述', '“纵观408中的计算机组成原理”：第一章计算机系统概述的奇妙之旅', 'Bilibili', 'https://www.bilibili.com/video/BV1e94y1T75M', '图灵讲计组 讲解 · 播放 5681 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/33e0a70bd283b7537272ae3088b49e8359366989.jpg', '32:35', 0, 59, '图灵讲计组', 'seed', '计算机发展历程'),
  (212, '计算机组成原理', '计算机系统概述', '计组过完一轮跟没学一样？一张图帮你完成408考研组成原理章节知识点梳理以及重点解题技巧', 'Bilibili', 'https://www.bilibili.com/video/BV1EY4y1K72K', '神秘人出海了 讲解 · 播放 32694 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/b0fbfd648726c5eaf210f2164e285d1d3cb56de0.jpg', '33:35', 0, 39, '神秘人出海了', 'seed', '计算机发展历程'),
  (213, '计算机组成原理', '计算机系统概述', '打破计组和操作系统的屏障！一节课学完408考研中磁盘计算相关真题知识点', 'Bilibili', 'https://www.bilibili.com/video/BV1EK411a74G', '图灵讲计组 · 播放 17700 次 · 与 计算机系统概述 相关', 'https://i1.hdslb.com/bfs/archive/29af19b1f0cf75429c7d4b69758be1d6e53f9cc0.jpg', '46:26', 0, 41, '图灵讲计组', 'seed', '计算机发展历程'),
  (214, '计算机组成原理', '计算机系统概述', '计组强化-第三章（4）磁盘存储器真题精讲及知识大总结', 'Bilibili', 'https://www.bilibili.com/video/BV1X4yzBVEeP', '计算机考研-雨涵 · 播放 8388 次 · 与 计算机系统概述 相关', 'https://i0.hdslb.com/bfs/archive/98c7238e7fb327cc33928971a328b9d3834d9c41.jpg', '37:3', 0, 35, '计算机考研-雨涵', 'seed', '计算机发展历程'),
  (215, '计算机组成原理', '计算机系统概述', '计算机组成原理中央处理器CPU', 'Bilibili', 'https://www.bilibili.com/video/BV1Nc2rY7Ecm', '布偶小喵11408 · 播放 233 次 · 与 计算机系统概述 相关', 'https://i0.hdslb.com/bfs/archive/a76b2d4e0f973cfaad865a17e8c4a045e6b1f9ae.jpg', '58:42', 0, 31, '布偶小喵11408', 'seed', '计算机发展历程'),
  (216, '计算机组成原理', '计算机系统概述', '干掉存储器计划-第一话：主存储器概述（附王道计组3.1，3.2课后题讲解）', 'Bilibili', 'https://www.bilibili.com/video/BV1J14y147CL', '优质推荐 · Beokayy_ 制作 · 播放 55630 次 · 与 计算机系统概述 高度相关', 'https://i0.hdslb.com/bfs/archive/f336b56d3f01adec32027c7d9cf094e07f1cc9b3.jpg', '54:8', 0, 45, 'Beokayy_', 'seed', '计算机系统层次结构'),
  (217, '计算机组成原理', '计算机系统概述', '深入浅出讲解微程序控制器『计算机考研408 计组』', 'Bilibili', 'https://www.bilibili.com/video/BV14m4y1e7KE', '零壹计算机考研 讲解 · 播放 10087 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/c2d8d59400d9f9f11293f081cb4456b70d898031.jpg', '49:14', 0, 43, '零壹计算机考研', 'seed', '计算机系统层次结构'),
  (218, '计算机组成原理', '计算机系统概述', '计算机考研408|《计算机组成原理》第一章 计算机系统概述01|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV1EyX6YSEFb', '计算机考研408羊驼老师 讲解 · 播放 367 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/97851169b786a5073f27b2f09033594eef22a00e.jpg', '33:1', 0, 51, '计算机考研408羊驼老师', 'seed', '计算机系统层次结构'),
  (219, '计算机组成原理', '计算机系统概述', '计组难点详解－RAM内部结构和设计[408真题常考点详解 计算机考研大众难点]', 'Bilibili', 'https://www.bilibili.com/video/BV199pzeUE7z', '零壹计算机考研 讲解 · 播放 3840 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/8df77830a040809fc8a1e2610252b354bcd90bc8.jpg', '36:18', 0, 33, '零壹计算机考研', 'seed', '计算机系统层次结构'),
  (220, '计算机组成原理', '计算机系统概述', '【柠宝408】计算机组成原理 第一章 概述 | 小白必看 | 零基础保姆级 | 包教包会', 'Bilibili', 'https://www.bilibili.com/video/BV1gDrTY7Esi', 'math也是柠檬精 讲解 · 播放 3300 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/c74c1eb733e83e56896b978cb1ea519af1ce7af5.jpg', '33:4', 0, 43, 'math也是柠檬精', 'seed', '计算机系统层次结构'),
  (221, '计算机组成原理', '计算机系统概述', '45分钟讲清计组各种计算机性能指标如何通关！', 'Bilibili', 'https://www.bilibili.com/video/BV1CfdBBQEJa', '木子老师408 讲解 · 播放 944 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/7be510b7033928740ccea292b63be06c85757cb9.jpg', '44:26', 0, 29, '木子老师408', 'seed', '计算机的性能指标'),
  (222, '计算机组成原理', '计算机系统概述', '组原022-第六讲 总线系统 01', 'Bilibili', 'https://www.bilibili.com/video/BV1YH4y1W7cL', '计算机考研刘财政 · 播放 95 次 · 与 计算机系统概述 相关', 'https://i0.hdslb.com/bfs/archive/ba37457a1eaf222f4ca661b18fb8acba644b6fb9.png', '48:58', 0, 19, '计算机考研刘财政', 'seed', '计算机的性能指标'),
  (223, '计算机组成原理', '计算机系统概述', '计组强化！第一章真题全解析及知识回顾', 'Bilibili', 'https://www.bilibili.com/video/BV1cc4HzjEw2', '计算机考研-雨涵 · 播放 6923 次 · 与 计算机系统概述 相关', 'https://i2.hdslb.com/bfs/archive/dfb657e47a0ef9ff8ca4947782933193d18dd43f.jpg', '49:33', 0, 25, '计算机考研-雨涵', 'seed', '计算机的性能指标'),
  (224, '计算机组成原理', '计算机系统概述', '补码：有符号数加减法解析', 'Bilibili', 'https://www.bilibili.com/video/BV1gxAJeBELp', '计算机考研-雨涵 · 播放 5571 次 · 与 计算机系统概述 相关', 'https://i2.hdslb.com/bfs/archive/f5f6efce899001170558b5a4b21a634d8d1030b6.jpg', '32:11', 0, 25, '计算机考研-雨涵', 'seed', '计算机的性能指标'),
  (225, '计算机组成原理', '计算机系统概述', '408操作系统基本概念扫码（适合27考研先导或基础模糊同学！）', 'Bilibili', 'https://www.bilibili.com/video/BV1wA1CBgEdU', '计算机考研-雨涵 · 播放 4305 次 · 与 计算机系统概述 相关', 'https://i1.hdslb.com/bfs/archive/403c4bd2ef5e3d6e05d120fc6b6db932f195327b.jpg', '50:28', 0, 29, '计算机考研-雨涵', 'seed', '计算机的性能指标'),
  (226, '计算机组成原理', '数据的表示和运算', '408计算机组成原理部分-数据的表示和运算_加法器和算逻部件ALU', 'Bilibili', 'https://www.bilibili.com/video/BV1Ed4y1A7iP', '头秃萌Xin 讲解 · 播放 830 次 · 覆盖 数据的表示和运算 相关内容', 'https://i1.hdslb.com/bfs/archive/0030b426d43964665e96d2776cdd7e158ab1be9d.jpg', '34:7', 0, 49, '头秃萌Xin', 'seed', '数制与编码'),
  (227, '计算机组成原理', '数据的表示和运算', '408计算机组成原理复习—数据表示和运算', 'Bilibili', 'https://www.bilibili.com/video/BV1W6SUYyEZ9', '栾灰灰向前看 讲解 · 播放 4766 次 · 覆盖 数据的表示和运算 相关内容', 'https://i1.hdslb.com/bfs/archive/c26e2e33d267edc2c12a18afec54fb979807fa2a.jpg', '34:42', 0, 43, '栾灰灰向前看', 'seed', '数制与编码'),
  (228, '计算机组成原理', '数据的表示和运算', '计算机组成原理数据的表示与运算', 'Bilibili', 'https://www.bilibili.com/video/BV1FH2VYFEAK', '布偶小喵11408 · 播放 180 次 · 与 数据的表示和运算 相关', 'https://i0.hdslb.com/bfs/archive/065a75a1a569bfd0aede40b45b52b74855091c5b.jpg', '37:59', 0, 31, '布偶小喵11408', 'seed', '数制与编码'),
  (229, '计算机组成原理', '数据的表示和运算', '考研408计组之基本功学习—纵横第二章数据的表示与存储', 'Bilibili', 'https://www.bilibili.com/video/BV1og4y127TA', '图灵讲计组 · 播放 2731 次 · 与 数据的表示和运算 相关', 'https://i1.hdslb.com/bfs/archive/ee5ce8296e0cff2bdfb7cebdb7adb00c9f45ddaa.jpg', '54:28', 0, 29, '图灵讲计组', 'seed', '数制与编码'),
  (230, '计算机组成原理', '数据的表示和运算', '40分钟多拿4～12分｜看完再也不怕“原反补移真无”转换｜数据的表示与运算从头梳理｜计算机考研408｜26计算机考研', 'Bilibili', 'https://www.bilibili.com/video/BV1C6yZBjE3v', '五道口一只鸭 · 播放 2208 次 · 与 数据的表示和运算 相关', 'https://i2.hdslb.com/bfs/archive/f52938aeaeb2f55b2a3de87a27243c260ab0ad1e.jpg', '42:15', 0, 33, '五道口一只鸭', 'seed', '数制与编码'),
  (231, '计算机组成原理', '数据的表示和运算', '手把手练透计组基本功:数据表示与运算（计组小观03）', 'Bilibili', 'https://www.bilibili.com/video/BV1FTWqz2EXL', '花田慎鸾交 · 播放 1469 次 · 与 数据的表示和运算 相关', 'https://i0.hdslb.com/bfs/archive/c0a5224ff50901ea96263cf050905336690ed4e6.jpg', '54:48', 0, 25, '花田慎鸾交', 'seed', '运算方法和运算电路'),
  (232, '计算机组成原理', '数据的表示和运算', '【408wd逐题精讲】2.2 运算方法和运算电路', 'Bilibili', 'https://www.bilibili.com/video/BV1aCoVYgEtX', 'math也是柠檬精 · 播放 1249 次 · 与 数据的表示和运算 相关', 'https://i2.hdslb.com/bfs/archive/79faf2658355557e3da8ac571631688cb6ee7503.jpg', '42:53', 0, 27, 'math也是柠檬精', 'seed', '运算方法和运算电路'),
  (233, '计算机组成原理', '数据的表示和运算', '27组成原理强化-数据的机器级表示专题（下）', 'Bilibili', 'https://www.bilibili.com/video/BV1bwEk62ELV', '就是氧气11 · 播放 658 次 · 与 数据的表示和运算 相关', 'https://i1.hdslb.com/bfs/archive/df04ba543b28d44b1719f60f85431faa149afca3.jpg', '52:1', 0, 17, '就是氧气11', 'seed', '运算方法和运算电路'),
  (234, '计算机组成原理', '数据的表示和运算', '【计组】（选择题）第二章：数据的表示与运算。408最难的一章！', 'Bilibili', 'https://www.bilibili.com/video/BV1NueXzoEqp', '不会408 · 播放 571 次 · 与 数据的表示和运算 相关', 'https://i0.hdslb.com/bfs/archive/ad65df8757bb08cb714f0470f3d9d45aa791422b.jpg', '33:9', 0, 17, '不会408', 'seed', '运算方法和运算电路'),
  (235, '计算机组成原理', '数据的表示和运算', '27组成原理强化-数据的表示与运算综合大题专题', 'Bilibili', 'https://www.bilibili.com/video/BV1mBLQ6AEiR', '就是氧气11 · 播放 569 次 · 与 数据的表示和运算 相关', 'https://i2.hdslb.com/bfs/archive/4f2a8026ed00019b268bd930a4003d8df02a5945.jpg', '54:10', 0, 17, '就是氧气11', 'seed', '运算方法和运算电路'),
  (236, '计算机组成原理', '数据的表示和运算', '【计组】.透彻理解浮点数与IEEE754标准', 'Bilibili', 'https://www.bilibili.com/video/BV1Ks4y1E7qo', '优质推荐 · 其涼 制作 · 播放 48707 次 · 与 数据的表示和运算 高度相关', 'https://i1.hdslb.com/bfs/archive/16d3d158c7bd6273bf4d0a85bc0018c861e9cc90.jpg', '47:59', 0, 45, '其涼', 'seed', '浮点数的表示与运算'),
  (237, '计算机组成原理', '数据的表示和运算', '【柠宝408】2.4.1 浮点数的表示与IEEE754标准', 'Bilibili', 'https://www.bilibili.com/video/BV1unVWzPEXP', 'math也是柠檬精 讲解 · 播放 8900 次 · 覆盖 数据的表示和运算 相关内容', 'https://i1.hdslb.com/bfs/archive/efd9bbe73e652c0248523a87079b594cd8a3ca4e.jpg', '49:15', 0, 37, 'math也是柠檬精', 'seed', '浮点数的表示与运算'),
  (238, '计算机组成原理', '数据的表示和运算', '计算机组成原理复盘—数据的表示与运算3（浮点数、IEEE754、强制转换、大小端、边界对齐） 20240501', 'Bilibili', 'https://www.bilibili.com/video/BV14x4y1z78r', '布偶小喵11408 讲解 · 播放 2313 次 · 覆盖 数据的表示和运算 相关内容', 'https://i1.hdslb.com/bfs/archive/ee9e0eaa098e13626ba3398378f2f26a9a1f0ca8.jpg', '54:25', 0, 41, '布偶小喵11408', 'seed', '浮点数的表示与运算'),
  (239, '计算机组成原理', '数据的表示和运算', '计算机考研经典教材带读丨《计算机组成原理》袁春风版：3.4.1 浮点数加减运算', 'Bilibili', 'https://www.bilibili.com/video/BV1m6NxzUEB4', '启航计算机考研 · 播放 164 次 · 与 数据的表示和运算 相关', 'https://i0.hdslb.com/bfs/archive/d6ee8d11e4ecd94015c31d3b68d738e72d182043.jpg', '56:28', 0, 33, '启航计算机考研', 'seed', '浮点数的表示与运算'),
  (240, '计算机组成原理', '数据的表示和运算', '27组成原理基础-IEEE754浮点数的表示与运算', 'Bilibili', 'https://www.bilibili.com/video/BV1WaPnzdEkR', '就是氧气11 · 播放 1181 次 · 与 数据的表示和运算 相关', 'https://i0.hdslb.com/bfs/archive/742c71004342609b9f1c502603ac48953977ef0a.jpg', '31:24', 0, 27, '就是氧气11', 'seed', '浮点数的表示与运算'),
  (241, '计算机组成原理', '存储系统', '干掉存储器计划-第二话：主存储器与CPU的连接，寻址问题（附王道计组3.3课后题讲解，请结合知识点一起食用）', 'Bilibili', 'https://www.bilibili.com/video/BV1VG411b7e3', 'Beokayy_ 讲解 · 播放 37617 次 · 覆盖 存储系统 相关内容', 'https://i2.hdslb.com/bfs/archive/80670ed099f82c773fb937209e9601c56dd00ccd.jpg', '32:24', 0, 35, 'Beokayy_', 'seed', '存储器概述'),
  (242, '计算机组成原理', '存储系统', '408操作系统第三章3-虚拟存储器大题真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1Mr4y1Z7Zo', '就是氧气11 · 播放 18674 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/168f405c8ec9d047a21b463356dc97a1c3a0c9b4.jpg', '38:1', 0, 37, '就是氧气11', 'seed', '存储器概述'),
  (243, '计算机组成原理', '存储系统', '408操作系统第三章2-虚拟存储器以及真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1yP411W7wW', '就是氧气11 · 播放 16715 次 · 与 存储系统 相关', 'https://i0.hdslb.com/bfs/archive/217b1a215f797a682832de461c84c93673a0bbf7.jpg', '32:54', 0, 37, '就是氧气11', 'seed', '存储器概述'),
  (244, '计算机组成原理', '存储系统', '计算机组成原理之存储子系统的概述以及各类存储器的详述', 'Bilibili', 'https://www.bilibili.com/video/BV1FR4y1E7gN', '皮卡丘上大学啦 · 播放 2970 次 · 与 存储系统 相关', 'https://i1.hdslb.com/bfs/archive/4f028c9f8cdfb7c31c982d22d1fbbd008b616a64.jpg', '54:10', 0, 41, '皮卡丘上大学啦', 'seed', '存储器概述'),
  (245, '计算机组成原理', '存储系统', '计算机考研经典教材带读丨《计算机组成原理》袁春风版：4.4存储器芯片的扩展及其与CPU的链接', 'Bilibili', 'https://www.bilibili.com/video/BV1smK3zrEjP', '启航计算机考研 · 播放 171 次 · 与 存储系统 相关', 'https://i0.hdslb.com/bfs/archive/d6ee8d11e4ecd94015c31d3b68d738e72d182043.jpg', '38:11', 0, 33, '启航计算机考研', 'seed', '存储器概述'),
  (246, '计算机组成原理', '存储系统', '计算机组成原理存储器层次结构', 'Bilibili', 'https://www.bilibili.com/video/BV1gW2UYyE5F', '布偶小喵11408 · 播放 351 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/508576cd0650b6fae6f4cb2f37e2ce0b20b8d884.jpg', '48:11', 0, 31, '布偶小喵11408', 'seed', '主存储器'),
  (247, '计算机组成原理', '存储系统', '操作系统强化专题-虚拟存储器', 'Bilibili', 'https://www.bilibili.com/video/BV1U18tznEBs', '就是氧气11 · 播放 2739 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/24c9d9b28c4173e3d68733223e54ffb38f210bbf.jpg', '40:1', 0, 27, '就是氧气11', 'seed', '主存储器'),
  (248, '计算机组成原理', '存储系统', '“零基础入门408计组”之第三章存储管理，理解直接做真题', 'Bilibili', 'https://www.bilibili.com/video/BV1qw411J7MQ', '图灵讲计组 · 播放 1814 次 · 与 存储系统 相关', 'https://i0.hdslb.com/bfs/archive/12dd63e4132148b4ec392dd8f48cc07406852a6b.jpg', '30:56', 0, 27, '图灵讲计组', 'seed', '主存储器'),
  (249, '计算机组成原理', '存储系统', '6-6磁盘存储器的管理', 'Bilibili', 'https://www.bilibili.com/video/BV1JzzdYwEbP', '真题考研408 · 播放 645 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/a9fe392e1bd8370de59a027fe6c8da57a010cf51.jpg', '35:51', 0, 23, '真题考研408', 'seed', '主存储器'),
  (250, '计算机组成原理', '存储系统', '组原009-第三讲 主存储器 02', 'Bilibili', 'https://www.bilibili.com/video/BV19D42177yt', '计算机考研刘财政 · 播放 100 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/cf1d25cf8d2227eea91896ba19c8d5105f22eff2.jpg', '33:30', 0, 21, '计算机考研刘财政', 'seed', '主存储器'),
  (251, '计算机组成原理', '存储系统', '计算机组成原理，主存储器下集，尝试复述', 'Bilibili', 'https://www.bilibili.com/video/BV1dMZLBLE2V', '东泽坤 · 播放 327 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/8f098316d1f2592faf49fcc3a00529016f3c9132.jpg', '52:57', 0, 31, '东泽坤', 'seed', '主存储器与CPU的连接'),
  (252, '计算机组成原理', '存储系统', 'Cache-内存-虚存大题！最后再冲15分！！！', 'Bilibili', 'https://www.bilibili.com/video/BV1tAU1BZEBQ', '优质推荐 · 喵咪布爱学习 制作 · 播放 8557 次 · 与 存储系统 高度相关', 'https://i2.hdslb.com/bfs/archive/7fe9bbd89c1150d39c569268da1cb3a7801eb6e6.jpg', '33:31', 0, 35, '喵咪布爱学习', 'seed', '外部存储器'),
  (253, '计算机组成原理', '存储系统', '组成原理冲刺-cache与外部存储器', 'Bilibili', 'https://www.bilibili.com/video/BV1AW1gB2EKk', '就是氧气11 · 播放 2646 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/8d0b118226af8c1da12fb4297e7a981f933de97a.jpg', '34:5', 0, 27, '就是氧气11', 'seed', '外部存储器'),
  (254, '计算机组成原理', '存储系统', '【cache专项】谁说cache难了？这个cache可太棒了！', 'Bilibili', 'https://www.bilibili.com/video/BV1B6tdz6EwN', '里昂408 讲解 · 播放 48069 次 · 覆盖 存储系统 相关内容', 'https://i0.hdslb.com/bfs/archive/231c236f593b242617520414897add8d512c36c0.jpg', '49:4', 0, 45, '里昂408', 'seed', '高速缓冲存储器'),
  (255, '计算机组成原理', '存储系统', '一个视频带你全面拆解一个Cache行的完整构成', 'Bilibili', 'https://www.bilibili.com/video/BV1S8RZBJE7W', '408叁拾学长 · 播放 201 次 · 与 存储系统 相关', 'https://i2.hdslb.com/bfs/archive/abe1c2cb2b000a5983355df7078886ead2576702.jpg', '33:8', 0, 15, '408叁拾学长', 'seed', '高速缓冲存储器'),
  (256, '计算机组成原理', '存储系统', '第三章存储系统重点二虚拟存储 1 页式虚拟存储', 'Bilibili', 'https://www.bilibili.com/video/BV1yRj3zAEbc', '练习两年半的408 讲解 · 播放 151 次 · 覆盖 存储系统 相关内容', 'https://i0.hdslb.com/bfs/archive/e6ea4458619e36b9c5f23b9b62b3d8841d4eea5c.jpg', '39:31', 0, 43, '练习两年半的408', 'seed', '虚拟存储器'),
  (257, '计算机组成原理', '存储系统', '计算机学科基础综合统考408重难点突破之Cache与虚拟存储器', 'Bilibili', 'https://www.bilibili.com/video/BV1Et411E7D6', 'RAININGSPRING520 · 播放 16263 次 · 与 存储系统 相关', 'https://i0.hdslb.com/bfs/archive/6fd76a9e0a4f0c3fc7553707c9325fa8e706e5c8.jpg', '31:25', 0, 41, 'RAININGSPRING520', 'seed', '虚拟存储器'),
  (258, '计算机组成原理', '存储系统', '操作系统内存管理', 'Bilibili', 'https://www.bilibili.com/video/BV1UCmMYaELX', '布偶小喵11408 · 播放 100 次 · 与 存储系统 相关', 'https://i0.hdslb.com/bfs/archive/dbe4b8514d086f3f03077e35338c64d3bbfe1d8a.jpg', '50:17', 0, 15, '布偶小喵11408', 'seed', '虚拟存储器'),
  (259, '计算机组成原理', '指令系统', '【柠宝408】用命题人袁春风老师教材精讲408计组原码乘法以及运算逻辑图！', 'Bilibili', 'https://www.bilibili.com/video/BV1yn4y1Q7GZ', 'math也是柠檬精 · 播放 10513 次 · 与 指令系统 相关', 'https://i2.hdslb.com/bfs/archive/ce234ca26439a1c7b5de80fc6601104155a4e393.jpg', '50:11', 0, 37, 'math也是柠檬精', 'seed', '指令集体系结构'),
  (260, '计算机组成原理', '指令系统', '【27考研】408强化安排（百人经验，真实详细版，看了不后悔！！！）', 'Bilibili', 'https://www.bilibili.com/video/BV1VVEF6uEvp', '皆与忘川 · 播放 10550 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/8b1b741406eee364447e1510ce08769152cc8871.jpg', '34:43', 0, 39, '皆与忘川', 'seed', '指令集体系结构'),
  (261, '计算机组成原理', '指令系统', '计算机考研经典教材带读丨《计算机组成原理》袁春风版：6.1.4数据通路的基本结构', 'Bilibili', 'https://www.bilibili.com/video/BV16bu4zDEdm', '启航计算机考研 · 播放 155 次 · 与 指令系统 相关', 'https://i0.hdslb.com/bfs/archive/d6ee8d11e4ecd94015c31d3b68d738e72d182043.jpg', '40:13', 0, 33, '启航计算机考研', 'seed', '指令集体系结构'),
  (262, '计算机组成原理', '指令系统', '学不会我吃【柠宝408】计组 1.3 计算机系统的基本组成 | 狗都不背 | 学不会我吃', 'Bilibili', 'https://www.bilibili.com/video/BV17MA7eGEgW', 'math也是柠檬精 · 播放 2598 次 · 与 指令系统 相关', 'https://i2.hdslb.com/bfs/archive/076b908fc97dff84066611ecc7e8d473e161d43e.jpg', '43:3', 0, 31, 'math也是柠檬精', 'seed', '指令集体系结构'),
  (263, '计算机组成原理', '指令系统', '【408】王道计组习题逐题讲解| 一遍就会，包教包会', 'Bilibili', 'https://www.bilibili.com/video/BV1sFRsYpEVW', 'math也是柠檬精 · 播放 2554 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/462ce058eb6919d937cc1c3abd1ef55944999f45.jpg', '51:7', 0, 27, 'math也是柠檬精', 'seed', '指令集体系结构'),
  (264, '计算机组成原理', '指令系统', '微型计算机原理之指令系统--概述及寻址方式讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1tq4y1z78E', '优质推荐 · 皮卡丘上大学啦 制作 · 播放 33762 次 · 与 指令系统 高度相关', 'https://i2.hdslb.com/bfs/archive/190e3f289845940cd8dea72d37356387f205bcb4.jpg', '38:48', 0, 67, '皮卡丘上大学啦', 'seed', '寻址方式'),
  (265, '计算机组成原理', '指令系统', '408王道计算机组成原理第四章2-指令寻址方式知识点+选择题', 'Bilibili', 'https://www.bilibili.com/video/BV1ZN41127UB', '就是氧气11 讲解 · 播放 21675 次 · 覆盖 指令系统 相关内容', 'https://i1.hdslb.com/bfs/archive/7c9aa27c14adede211d13d9dd59700b5a18abce1.jpg', '31:5', 0, 53, '就是氧气11', 'seed', '寻址方式'),
  (266, '计算机组成原理', '指令系统', '计算机组成原理指令系统', 'Bilibili', 'https://www.bilibili.com/video/BV1zg28YrEdw', '布偶小喵11408 讲解 · 播放 220 次 · 覆盖 指令系统 相关内容', 'https://i1.hdslb.com/bfs/archive/1d94c703d3cc4d5b9feafc8fbe819f931da624b6.jpg', '33:43', 0, 47, '布偶小喵11408', 'seed', '寻址方式'),
  (267, '计算机组成原理', '指令系统', '计组 指令系统 指令寻址', 'Bilibili', 'https://www.bilibili.com/video/BV12PtmzAEvb', '固安_-_ · 播放 131 次 · 与 指令系统 相关', 'https://i2.hdslb.com/bfs/archive/2e2ba9c360cbc41f0c1b0c3d8cc5147970470d0b.jpg', '40:44', 0, 43, '固安_-_', 'seed', '寻址方式'),
  (268, '计算机组成原理', '指令系统', '计组-寻址方式套路总结（附选择题精讲）', 'Bilibili', 'https://www.bilibili.com/video/BV1dukXBLEVh', '计算机考研-雨涵 · 播放 23375 次 · 与 指令系统 相关', 'https://i2.hdslb.com/bfs/archive/165610060fff49f1d03e91306aa1429cecd9384a.jpg', '31:34', 0, 35, '计算机考研-雨涵', 'seed', '寻址方式'),
  (269, '计算机组成原理', '指令系统', '「考研复试项目」0 基础从深度学习到大模型 + CV 与自动驾驶实战', 'Bilibili', 'https://www.bilibili.com/video/BV1e5USY4E2R', 'M学长的考研top帮 讲解 · 播放 60669 次 · 覆盖 指令系统 相关内容', 'https://i0.hdslb.com/bfs/archive/874d911285a1a4dfad40306f4b8868c765d79f96.jpg', '42:13', 0, 47, 'M学长的考研top帮', 'seed', '程序的机器级代码表示'),
  (270, '计算机组成原理', '指令系统', '组成原理冲刺-程序的机器级表示与MIPS', 'Bilibili', 'https://www.bilibili.com/video/BV12q1aBjEAN', '就是氧气11 · 播放 3006 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/4e977020038d16e0dffbe7c235a5693b66279e92.jpg', '37:59', 0, 27, '就是氧气11', 'seed', '程序的机器级代码表示'),
  (271, '计算机组成原理', '指令系统', '26考研复试项目速成课，零基础一节课就能入门！', 'Bilibili', 'https://www.bilibili.com/video/BV1pSBeBhEoR', 'N诺计算机考研 · 播放 1025 次 · 与 指令系统 相关', 'https://i0.hdslb.com/bfs/archive/79755c10de0e3196bdffc71212b5aaa49969c653.jpg', '37:56', 0, 27, 'N诺计算机考研', 'seed', '程序的机器级代码表示'),
  (272, '计算机组成原理', '指令系统', '[Day108] 函数调用机器数表示', 'Bilibili', 'https://www.bilibili.com/video/BV1A9p4ewEJR', '向小园_ · 播放 1465 次 · 与 指令系统 相关', 'https://i0.hdslb.com/bfs/archive/dd5c661248eee722e8bd9ae809e97f506db53293.jpg', '32:29', 0, 25, '向小园_', 'seed', '程序的机器级代码表示'),
  (273, '计算机组成原理', '指令系统', '「哈工大计算机考研」（2）Csapp第三章程序的机器级云里雾里？哈工大电磁低音炮师兄带你秒杀', 'Bilibili', 'https://www.bilibili.com/video/BV1FX4y1E7kR', '哈工大风哥考研 · 播放 743 次 · 与 指令系统 相关', 'https://i2.hdslb.com/bfs/archive/a982404d42f4019e8128f1684151f83e545cfa31.jpg', '50:53', 0, 21, '哈工大风哥考研', 'seed', '程序的机器级代码表示'),
  (274, '计算机组成原理', '指令系统', '计算机组成原理复盘—指令系统2（汇编语言、CISC、RISC） 20240510', 'Bilibili', 'https://www.bilibili.com/video/BV1Ex4y1B7sv', '布偶小喵11408 讲解 · 播放 441 次 · 覆盖 指令系统 相关内容', 'https://i1.hdslb.com/bfs/archive/ac508f28830b9674f7048c32aab32e504f412d66.jpg', '51:40', 0, 47, '布偶小喵11408', 'seed', 'CISC和RISC的基本概念'),
  (275, '计算机组成原理', '指令系统', '22-计算机组成原理—第4章-指令系统—4.4 指令的操作类型+4.5 复杂指令集计算机CISC和 精简指令集计算机RISC-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1YFumzcEtp', '必须好好读研 讲解 · 播放 169 次 · 覆盖 指令系统 相关内容', 'https://i0.hdslb.com/bfs/archive/d2306cb28fe3cc73d608a6dac6e6453a699939e0.jpg', '48:9', 0, 47, '必须好好读研', 'seed', 'CISC和RISC的基本概念'),
  (276, '计算机组成原理', '指令系统', '第二讲 数据表示和指令系统 06 CISC和RISC结构优化', 'Bilibili', 'https://www.bilibili.com/video/BV1BHYserEn1', '全栈研究所 · 播放 35 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/db8390cea25f1e9c8b06557074ef18181a9ee8e4.jpg', '30:38', 0, 38, '全栈研究所', 'seed', 'CISC和RISC的基本概念'),
  (277, '计算机组成原理', '指令系统', '惊心动魄！RISC 和 CISC 之争', 'Bilibili', 'https://www.bilibili.com/video/BV19pPLztERJ', '葬送的模数师 · 播放 1580 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/5e1720ef488c00bbf538532f04a7ee56f1ee7b8f.jpg', '39:55', 0, 27, '葬送的模数师', 'seed', 'CISC和RISC的基本概念'),
  (278, '计算机组成原理', '指令系统', '【复盘080】408应用题自学包 PartX 指令操作类型 CISC vs RISC', 'Bilibili', 'https://www.bilibili.com/video/BV1EYpFzgE48', 'occcccc1221 · 播放 18 次 · 与 指令系统 相关', 'https://i1.hdslb.com/bfs/archive/b7e3c76bb17f738be9f7d8aa7f1b29e39f841c85.jpg', '33:1', 0, 12, 'occcccc1221', 'seed', 'CISC和RISC的基本概念'),
  (279, '计算机组成原理', '中央处理器', '拿捏中央处理器（计组第五章知识点串讲）', 'Bilibili', 'https://www.bilibili.com/video/BV1cu4y1S7HR', '优质推荐 · 里昂408 制作 · 播放 44543 次 · 与 中央处理器 高度相关', 'https://i2.hdslb.com/bfs/archive/ab1453a646b619d5518ca5ebc3dd11a8e5337f4d.png', '31:10', 0, 63, '里昂408', 'seed', 'CPU的功能和基本结构'),
  (280, '计算机组成原理', '中央处理器', '计算机组成原理—中央处理器1（运算器、控制器、指令周期、数据通路） 20240510', 'Bilibili', 'https://www.bilibili.com/video/BV1M1421z72p', '布偶小喵11408 讲解 · 播放 3637 次 · 覆盖 中央处理器 相关内容', 'https://i0.hdslb.com/bfs/archive/26a89824e5ac3e01e3bd94b498b09c0f17025e44.jpg', '44:36', 0, 57, '布偶小喵11408', 'seed', 'CPU的功能和基本结构'),
  (281, '计算机组成原理', '中央处理器', '【南航计算机考研829专业课】计算机组成原理之中央处理器-数据通路（袁春风课本）', 'Bilibili', 'https://www.bilibili.com/video/BV1mf4y1E7ad', '-小茉莉a- 讲解 · 播放 2765 次 · 覆盖 中央处理器 相关内容', 'https://i2.hdslb.com/bfs/archive/11855a3437f5a8f2bc96a51a74ceda3d1f423f4a.jpg', '43:41', 0, 59, '-小茉莉a-', 'seed', 'CPU的功能和基本结构'),
  (282, '计算机组成原理', '中央处理器', '计算机组成原理复盘—中央处理器2（微程序控制器、硬布线控制器、中断） 20240513', 'Bilibili', 'https://www.bilibili.com/video/BV1x7421f7HZ', '布偶小喵11408 讲解 · 播放 702 次 · 覆盖 中央处理器 相关内容', 'https://i1.hdslb.com/bfs/archive/0fe5418621e40930fc497b8f737d1bd84ea7c456.jpg', '56:58', 0, 47, '布偶小喵11408', 'seed', 'CPU的功能和基本结构'),
  (283, '计算机组成原理', '中央处理器', '408 | 计组碎碎念之 [ 中央处理器 ]', 'Bilibili', 'https://www.bilibili.com/video/BV18QqxY9E5T', '困困尾 讲解 · 播放 498 次 · 覆盖 中央处理器 相关内容', 'https://i1.hdslb.com/bfs/archive/76fbc675850cacdd4b1415d4a4a177b20f6e2f26.jpg', '30:45', 0, 45, '困困尾', 'seed', 'CPU的功能和基本结构'),
  (284, '计算机组成原理', '中央处理器', '408计组第五章（真题复盘）', 'Bilibili', 'https://www.bilibili.com/video/BV1pAsez1Emm', '22408练习生 讲解 · 播放 606 次 · 覆盖 中央处理器 相关内容', 'https://i2.hdslb.com/bfs/archive/61d3376d8da64297b11520f40ea8c59f248417c0.jpg', '42:11', 0, 45, '22408练习生', 'seed', '指令执行过程'),
  (285, '计算机组成原理', '中央处理器', '30-计算机组成原理—第5章 中央处理器—5.4 控制器的功能和工作原理-微程序控制器(微指令设计)+硬布线与微程序的比较-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1PD8zz2ESP', '必须好好读研 · 播放 32 次 · 与 中央处理器 相关', 'https://i0.hdslb.com/bfs/archive/e54e4ecfef4c47b1dbfaf5255cd87e0c2d5efba6.jpg', '51:52', 0, 42, '必须好好读研', 'seed', '指令执行过程'),
  (286, '计算机组成原理', '中央处理器', '数字电子技术基础 4.6 数据选择器', 'Bilibili', 'https://www.bilibili.com/video/BV16Z4y197Vr', '王文俊讲电气 讲解 · 播放 318839 次 · 覆盖 中央处理器 相关内容', 'https://i0.hdslb.com/bfs/archive/cf2a3946905faf0d811a6f6a33b288ad98e363aa.png', '58:35', 0, 55, '王文俊讲电气', 'seed', '数据通路的功能和基本结构'),
  (287, '计算机组成原理', '中央处理器', '【双语+中配】📁🌟 深入解析Linux文件系统！从root/到/usr的致命一击 😲 | Linux菜鸟逆袭指南', 'Bilibili', 'https://www.bilibili.com/video/BV1VUNszsEig', '比特光锥_BightCone 讲解 · 播放 288715 次 · 覆盖 中央处理器 相关内容', 'https://i0.hdslb.com/bfs/archive/3fff02207eee9a46bb5e85e9a5938693f93f52cb.jpg', '35:2', 0, 55, '比特光锥_BightCone', 'seed', '数据通路的功能和基本结构'),
  (288, '计算机组成原理', '中央处理器', '补码加法器，如何实现加减法的统一？', 'Bilibili', 'https://www.bilibili.com/video/BV1aajU6YEGm', 'math也是柠檬精 · 播放 716 次 · 与 中央处理器 相关', 'https://i0.hdslb.com/bfs/archive/54c171a7bc9bd9d240409d73115d4c3a9c4880fd.jpg', '36:48', 0, 15, 'math也是柠檬精', 'seed', '数据通路的功能和基本结构'),
  (289, '计算机组成原理', '中央处理器', '简单处理器的实现 [一生一芯v24.07 - P5]', 'Bilibili', 'https://www.bilibili.com/video/BV1YgxCzdEvq', '一生一芯-视频号 · 播放 8302 次 · 与 中央处理器 相关', 'https://i2.hdslb.com/bfs/archive/76dcf45732bef057ac4c83f8f3e00699f632b15d.jpg', '55:29', 0, 25, '一生一芯-视频号', 'seed', '数据通路的功能和基本结构'),
  (290, '计算机组成原理', '中央处理器', 'CMOS动态比较器原理与结构详解：从开环运放到高速锁存器设计 | ADC | 模数转换器 多伦多大学Tony Chan Carusone', 'Bilibili', 'https://www.bilibili.com/video/BV1yBiKB7E9Z', 'IC一站式服务 · 播放 3495 次 · 与 中央处理器 相关', 'https://i2.hdslb.com/bfs/archive/aa424ae4db38514e105a40a8254df6bb37829ef5.jpg', '36:58', 0, 25, 'IC一站式服务', 'seed', '数据通路的功能和基本结构'),
  (291, '计算机组成原理', '中央处理器', '一小时速通CPU指令流水线', 'Bilibili', 'https://www.bilibili.com/video/BV1Tx4y1a7zm', '优质推荐 · Beokayy_ 制作 · 播放 105002 次 · 与 中央处理器 高度相关', 'https://i2.hdslb.com/bfs/archive/5cd264d0f2fd0414a2e759898c4b2b773e58f4ec.jpg', '52:30', 0, 55, 'Beokayy_', 'seed', '指令流水线'),
  (292, '计算机组成原理', '中央处理器', '【计组】CPU流水线及冒险', 'Bilibili', 'https://www.bilibili.com/video/BV18k4y1p7dA', '其涼 讲解 · 播放 12619 次 · 覆盖 中央处理器 相关内容', 'https://i1.hdslb.com/bfs/archive/d6df2aaecaf733ff75fa4a9d37901015a5021599.jpg', '43:15', 0, 35, '其涼', 'seed', '指令流水线'),
  (293, '计算机组成原理', '中央处理器', '指令流水线（含三种冒险）解题技巧！', 'Bilibili', 'https://www.bilibili.com/video/BV1x9yVBfEXU', '计算机考研-雨涵 · 播放 23844 次 · 与 中央处理器 相关', 'https://i0.hdslb.com/bfs/archive/80a5dea9c2bdeee3d1d83111fb625977d92fa100.jpg', '56:5', 0, 35, '计算机考研-雨涵', 'seed', '指令流水线'),
  (294, '计算机组成原理', '中央处理器', '半小时彻底弄懂408指令流水线！25极大概率考！近两年考察频率上升，越来越考察细节了！', 'Bilibili', 'https://www.bilibili.com/video/BV1jFzQYVEeV', '银盐学长 · 播放 5255 次 · 与 中央处理器 相关', 'https://i1.hdslb.com/bfs/archive/014fb0d2dbebc8891b4eaf0045c5508449b58ab3.jpg', '31:8', 0, 27, '银盐学长', 'seed', '指令流水线'),
  (295, '计算机组成原理', '中央处理器', '组成原理强化专题-单周期数据通路与指令流水线', 'Bilibili', 'https://www.bilibili.com/video/BV1zHenztEmu', '就是氧气11 · 播放 3984 次 · 与 中央处理器 相关', 'https://i1.hdslb.com/bfs/archive/e89811154780d3ee12c1ff9a40039d48042d5a75.jpg', '56:56', 0, 27, '就是氧气11', 'seed', '指令流水线'),
  (296, '计算机组成原理', '总线', '[408计组]6.1总线的概述习题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1Lr421x7TK', 'Cagwin 讲解 · 播放 157 次 · 覆盖 总线 相关内容', 'https://i1.hdslb.com/bfs/archive/9d37b51932632c85a0abc2ae60c72b4c0bfe648e.jpg', '32:8', 0, 45, 'Cagwin', 'seed', '总线概述'),
  (297, '计算机组成原理', '总线', '计算机考研408|《计算机组成原理》第一章 计算机系统概述03|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV172X6YEEYP', '计算机考研408羊驼老师 · 播放 236 次 · 与 总线 相关', 'https://i2.hdslb.com/bfs/archive/97851169b786a5073f27b2f09033594eef22a00e.jpg', '46:49', 0, 35, '计算机考研408羊驼老师', 'seed', '总线概述'),
  (298, '计算机组成原理', '总线', '计算机考研408|《计算机组成原理》第一章 计算机系统概述04|零基础考研必备小白速成C语言必学', 'Bilibili', 'https://www.bilibili.com/video/BV17yX6YSE9j', '计算机考研408羊驼老师 · 播放 199 次 · 与 总线 相关', 'https://i2.hdslb.com/bfs/archive/97851169b786a5073f27b2f09033594eef22a00e.jpg', '35:22', 0, 35, '计算机考研408羊驼老师', 'seed', '总线概述'),
  (299, '计算机组成原理', '总线', '2024考研计算机408基础网课：计算机系统概述｜0基础跨专业必刷课程', 'Bilibili', 'https://www.bilibili.com/video/BV1Dk4y1T76F', '金程考研辅导 · 播放 74 次 · 与 总线 相关', 'https://i2.hdslb.com/bfs/archive/705d4d087a754c4f4721c318b3cc3c28d63a10fd.jpg', '56:4', 0, 18, '金程考研辅导', 'seed', '总线概述'),
  (300, '计算机组成原理', '总线', 'BMS、整车 CAN总线概述与数据仲裁—第一讲', 'Bilibili', 'https://www.bilibili.com/video/BV1QP4y1n7j6', '雅客YY 讲解 · 播放 3108 次 · 覆盖 总线 相关内容', 'https://i0.hdslb.com/bfs/archive/14f654a0cb0d4981de6cd90257df9bbd882d1efa.jpg', '35:45', 0, 53, '雅客YY', 'seed', '总线仲裁');
INSERT INTO `video_resource` (`id`, `subject`, `knowledge_point`, `title`, `platform`, `url`, `reason`, `cover_url`, `duration`, `is_deleted`, `quality_score`, `author`, `crawl_source`, `section`) VALUES
  (301, '计算机组成原理', '总线', '6.2_总线仲裁', 'Bilibili', 'https://www.bilibili.com/video/BV1DU4y1v7DK', '躺平睡觉觉_ · 播放 346 次 · 与 总线 相关', 'https://i1.hdslb.com/bfs/archive/7257bffcb5fc087ed2bb47213edd37e28e054066.jpg', '30:5', 0, 43, '躺平睡觉觉_', 'seed', '总线仲裁'),
  (302, '计算机组成原理', '总线', '6-3-2 数据通路 —— 习题课（2）（无字幕版）', 'Bilibili', 'https://www.bilibili.com/video/BV1Mni2YkEx4', '湖科大教书匠 讲解 · 播放 6507 次 · 覆盖 总线 相关内容', 'https://i2.hdslb.com/bfs/archive/f51e2b2b240723239558e3f729a6a33853f6289d.jpg', '30:22', 0, 41, '湖科大教书匠', 'seed', '总线操作和定时'),
  (303, '计算机组成原理', '总线', '组成原理强化-总线与数据通路专题', 'Bilibili', 'https://www.bilibili.com/video/BV1JeGVzDETs', '就是氧气11 讲解 · 播放 4691 次 · 覆盖 总线 相关内容', 'https://i1.hdslb.com/bfs/archive/2266354f2d658ab4322e17517f3ead5bd165f50d.jpg', '46:10', 0, 53, '就是氧气11', 'seed', '总线操作和定时'),
  (304, '计算机组成原理', '总线', '组成原理冲刺-总线与IO', 'Bilibili', 'https://www.bilibili.com/video/BV1qm1UByEGy', '就是氧气11 讲解 · 播放 3146 次 · 覆盖 总线 相关内容', 'https://i0.hdslb.com/bfs/archive/042adceef7174176b837bc1adf262d481f33cb92.jpg', '45:38', 0, 55, '就是氧气11', 'seed', '总线操作和定时'),
  (305, '计算机组成原理', '总线', '27组成原理强化-总线专题', 'Bilibili', 'https://www.bilibili.com/video/BV1LBje6AE8V', '就是氧气11 讲解 · 播放 678 次 · 覆盖 总线 相关内容', 'https://i0.hdslb.com/bfs/archive/080ec171827cff4089ae848e08f050001baf910c.jpg', '32:12', 0, 45, '就是氧气11', 'seed', '总线操作和定时'),
  (306, '计算机组成原理', '总线', '27组成原理强化-存储器与总线选择题专题', 'Bilibili', 'https://www.bilibili.com/video/BV13wjC6UEHS', '就是氧气11 讲解 · 播放 579 次 · 覆盖 总线 相关内容', 'https://i0.hdslb.com/bfs/archive/9b009da18f6408b70fce8ca694468755d3422005.jpg', '33:56', 0, 45, '就是氧气11', 'seed', '总线操作和定时'),
  (307, '计算机组成原理', '总线', '彻底理解IEEE 754标准|看完就会做题|计算机组成原理', 'Bilibili', 'https://www.bilibili.com/video/BV1Aw4m1D7cS', '蓬蓬学长 讲解 · 播放 13115 次 · 覆盖 总线 相关内容', 'https://i1.hdslb.com/bfs/archive/7228bc04aec5f5b454cc57004dd56810192c7d0b.png', '57:17', 0, 51, '蓬蓬学长', 'seed', '总线标准'),
  (308, '计算机组成原理', '输入输出系统', '计组强化抢分！第二章（2）浮点数真题全解析及知识回顾', 'Bilibili', 'https://www.bilibili.com/video/BV1U94izKEG9', '计算机考研-雨涵 · 播放 7296 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/9dae52cd2dfe79c1ac9224803cfd9bf62faf9605.jpg', '43:30', 0, 25, '计算机考研-雨涵', 'seed', 'I/O系统概述'),
  (309, '计算机组成原理', '输入输出系统', 'I/O 系统一系列', 'Bilibili', 'https://www.bilibili.com/video/BV1MXewzsEtf', '情敌贝多芬的心跳 · 播放 1359 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/5cfe7c52b36fc0ee6de10b6a1c94c2863644d6cc.jpg', '38:14', 0, 25, '情敌贝多芬的心跳', 'seed', 'I/O系统概述'),
  (310, '计算机组成原理', '输入输出系统', '90.I/O系统【考研408操作系统R1#会员课】', 'Bilibili', 'https://www.bilibili.com/video/BV1kzpEeBEco', 'Y4NGY · 播放 627 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/af4fff145313d82d522e04513813517fe07e71bb.jpg', '34:15', 0, 19, 'Y4NGY', 'seed', 'I/O系统概述'),
  (311, '计算机组成原理', '输入输出系统', '操作系统输入输出管理', 'Bilibili', 'https://www.bilibili.com/video/BV1QTyTY4Ezp', '布偶小喵11408 · 播放 81 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/afebc9ad167d843992d50d9bf8608d7197e90352.jpg', '34:25', 0, 15, '布偶小喵11408', 'seed', 'I/O系统概述'),
  (312, '计算机组成原理', '输入输出系统', '考研大纲梳理直播回放（5、输入输出管理）上', 'Bilibili', 'https://www.bilibili.com/video/BV1dG411v7no', '操作系统艾老师 · 播放 445 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/64220a5629ed400bd0c12283e94862c1a07829e3.jpg', '35:46', 0, 17, '操作系统艾老师', 'seed', 'I/O系统概述'),
  (313, '计算机组成原理', '输入输出系统', '2024考研计算机408基础网课：输入输出管理｜0基础跨专业必刷课程', 'Bilibili', 'https://www.bilibili.com/video/BV1Tj411U7wn', '金程考研辅导 · 播放 58 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/13b2ec6d3c35956f2f904c0b494af827236ef365.jpg', '34:24', 0, 18, '金程考研辅导', 'seed', '外部设备'),
  (314, '计算机组成原理', '输入输出系统', '【计组】轻松拿捏微程序控制器', 'Bilibili', 'https://www.bilibili.com/video/BV1qw411271W', '其涼 · 播放 37461 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/b5057af3dde236550ab29dff14c182f14c8f128a.jpg', '31:17', 0, 35, '其涼', 'seed', 'I/O控制方式'),
  (315, '计算机组成原理', '输入输出系统', '5.2.3寻址方式', 'Bilibili', 'https://www.bilibili.com/video/BV1WH3TzrER8', '启航计算机考研 · 播放 178 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/d6ee8d11e4ecd94015c31d3b68d738e72d182043.jpg', '30:25', 0, 15, '启航计算机考研', 'seed', 'I/O控制方式'),
  (316, '计算机组成原理', '输入输出系统', '组成原理强化-中断与IO控制方式', 'Bilibili', 'https://www.bilibili.com/video/BV1sduezLEqj', '就是氧气11 · 播放 4010 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/620f8bd2e18f0492800d5fc9977a3176094ef6f4.jpg', '42:56', 0, 27, '就是氧气11', 'seed', 'I/O控制方式'),
  (317, '计算机组成原理', '输入输出系统', '408计组必考考点-Cache的三种映射方式，你学会了嘛？', 'Bilibili', 'https://www.bilibili.com/video/BV1bCRrBiET9', '408叁拾学长 · 播放 899 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/4ed15201ab3b4829bfb7de14de623b061d2de4ac.jpg', '56:29', 0, 27, '408叁拾学长', 'seed', 'I/O控制方式'),
  (318, '计算机组成原理', '输入输出系统', '3道题搞定408计组IO方式！', 'Bilibili', 'https://www.bilibili.com/video/BV1Nn4izfEa2', '木子老师408 · 播放 7656 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/89680aca5b8019286acc0b0c21e23ccd778b5b1c.jpg', '44:17', 0, 27, '木子老师408', 'seed', 'I/O控制方式'),
  (319, '计算机组成原理', '输入输出系统', '【考研408操作系统R1】26.中断（Interrupts）', 'Bilibili', 'https://www.bilibili.com/video/BV19p421X7Pj', 'Y4NGY · 播放 1651 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/cb4b0350679a3aa2cd3df8b8ed1f1cb24d4a7bb1.jpg', '34:22', 0, 29, 'Y4NGY', 'seed', '中断机制'),
  (320, '计算机组成原理', '输入输出系统', '计算机组成原理复盘—I/O系统（程序中断方式、DMA方式） 20240521', 'Bilibili', 'https://www.bilibili.com/video/BV1Ks421A7Lr', '布偶小喵11408 讲解 · 播放 1479 次 · 覆盖 输入输出系统 相关内容', 'https://i0.hdslb.com/bfs/archive/6fc8e03b9cc13e69edc75d069d0deef7658f948a.jpg', '43:3', 0, 41, '布偶小喵11408', 'seed', 'DMA方式'),
  (321, '计算机组成原理', '输入输出系统', '微型计算机的输入输出方式', 'Bilibili', 'https://www.bilibili.com/video/BV1RG4y1N7dT', 'Dedicated_Huang · 播放 973 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/b196665c57e719b0d0d9dae61b7ec49e238a4276.jpg', '36:23', 0, 29, 'Dedicated_Huang', 'seed', 'DMA方式'),
  (322, '计算机组成原理', '输入输出系统', '操作系统强化专题-基本分页、分段、段页式管理方式', 'Bilibili', 'https://www.bilibili.com/video/BV13jbXzWENC', '就是氧气11 · 播放 3569 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/af02c3d5202361d554a5e9783e9aeed07fe282dd.jpg', '44:43', 0, 27, '就是氧气11', 'seed', '通道方式'),
  (323, '计算机组成原理', '输入输出系统', '4-3基本分页存储管理方式', 'Bilibili', 'https://www.bilibili.com/video/BV1S1trehE7q', '真题考研408 · 播放 941 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/4385f0f462ebac616c2b82bc8eee3ec2a5cb4012.jpg', '50:12', 0, 33, '真题考研408', 'seed', '通道方式'),
  (324, '计算机组成原理', '输入输出系统', '65.连续分配管理方式【考研408操作系统R1#会员课】', 'Bilibili', 'https://www.bilibili.com/video/BV12Z421T7b8', 'Y4NGY · 播放 537 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/580448b5edc66bf3315a44a766059666a652c202.jpg', '32:31', 0, 19, 'Y4NGY', 'seed', '通道方式'),
  (325, '计算机组成原理', '输入输出系统', '66.段式存储管理方式【考研408操作系统R1#会员课】', 'Bilibili', 'https://www.bilibili.com/video/BV1qy411e7RY', 'Y4NGY · 播放 512 次 · 与 输入输出系统 相关', 'https://i0.hdslb.com/bfs/archive/b9698d1c4005762ec9c92434274cc8c7cd1ca644.jpg', '31:38', 0, 19, 'Y4NGY', 'seed', '通道方式'),
  (326, '操作系统', '计算机系统概述', '操作系统强化专题-操作系统基础概念', 'Bilibili', 'https://www.bilibili.com/video/BV1augczaE4A', '就是氧气11 讲解 · 播放 5176 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/835cc2dcd13abec4e13e02157ff00e2802b6cb02.jpg', '50:23', 0, 41, '就是氧气11', 'seed', '操作系统的基本概念'),
  (327, '操作系统', '计算机系统概述', '27考研408《操作系统》1.1操作系统的基本概念', 'Bilibili', 'https://www.bilibili.com/video/BV1DuXvBmEKF', '牛牛学姐勇闯408 讲解 · 播放 1513 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/4a196a97d76e72aa91ebef3a9d5f4594dbe6685d.jpg', '35:55', 0, 43, '牛牛学姐勇闯408', 'seed', '操作系统的基本概念'),
  (328, '操作系统', '计算机系统概述', '40分钟理清操作系统，期末、考研必备，节约一半复习时间', 'Bilibili', 'https://www.bilibili.com/video/BV1584y1C7yr', '优质推荐 · 乐智教学 制作 · 播放 102775 次 · 与 计算机系统概述 高度相关', 'https://i1.hdslb.com/bfs/archive/ef2a506ef540db972ad62bae61334f95f9fecd48.jpg', '41:48', 0, 71, '乐智教学', 'seed', '操作系统发展历程'),
  (329, '操作系统', '计算机系统概述', '【操作系统 | PV】40min带你狠狠拿捏PV大题的所有核心知识与解题技巧', 'Bilibili', 'https://www.bilibili.com/video/BV1fWx4eaE9g', '优质推荐 · _不是小火龙 制作 · 播放 67876 次 · 与 计算机系统概述 高度相关', 'https://i1.hdslb.com/bfs/archive/993605e324cf5e816e3626431484807ab51097c7.jpg', '40:37', 0, 69, '_不是小火龙', 'seed', '操作系统发展历程'),
  (330, '操作系统', '计算机系统概述', '408《操作系统》1.2操作系统的发展历程', 'Bilibili', 'https://www.bilibili.com/video/BV1iwDwB4EbS', '牛牛学姐勇闯408 · 播放 531 次 · 与 计算机系统概述 相关', 'https://i0.hdslb.com/bfs/archive/33c42ed869da583404acd3f298ad48229a19a977.jpg', '58:19', 0, 31, '牛牛学姐勇闯408', 'seed', '操作系统发展历程'),
  (331, '操作系统', '计算机系统概述', '【408真题速通】IO层次结构：真题共考察8次，2/3的同学都不能完全做对', 'Bilibili', 'https://www.bilibili.com/video/BV17vsHzKEGG', '王道计算机教育 讲解 · 播放 38645 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/fadc54fcfab073e4221e65e56f5e42bd30c7d219.jpg', '31:23', 0, 37, '王道计算机教育', 'seed', '操作系统的运行环境'),
  (332, '操作系统', '计算机系统概述', '【全网首发】26考研408真题及解析完整版！速来估分！！', 'Bilibili', 'https://www.bilibili.com/video/BV1q9BEBkED9', '木子老师408 讲解 · 播放 34382 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/e7b363c30317a833e8bcb4df69cbe32fea8f8f47.jpg', '48:4', 0, 39, '木子老师408', 'seed', '操作系统的运行环境'),
  (333, '操作系统', '计算机系统概述', '【哈工大计算机408考研】131分上岸北大！颠覆你对408的认知！', 'Bilibili', 'https://www.bilibili.com/video/BV1JA4m1c7f3', '哈工大风哥考研 讲解 · 播放 6919 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/60440f8d7ebb453408fdc1b28fa96ad21479edf5.jpg', '33:29', 0, 31, '哈工大风哥考研', 'seed', '操作系统的运行环境'),
  (334, '操作系统', '计算机系统概述', '2020年408操作系统真题自讲，数组原来在虚拟空间是连续的啊 哈哈我才知道。 最后一题可能有点混乱不好意思。', 'Bilibili', 'https://www.bilibili.com/video/BV1P24y1m7ja', '阿涛的三件事 讲解 · 播放 5540 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/2c3c18c5b33cccdd0965497dddae5b09a1e52136.jpg', '51:21', 0, 41, '阿涛的三件事', 'seed', '操作系统的运行环境'),
  (335, '操作系统', '计算机系统概述', 'Hive-I.1.文件系统大题模块化训练【考研408操作系统R3】', 'Bilibili', 'https://www.bilibili.com/video/BV1Z7UHYDEPV', 'Y4NGY 讲解 · 播放 5446 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/2d20bdc166bb76b60f506f21f51f8268336c8f2e.jpg', '53:32', 0, 43, 'Y4NGY', 'seed', '操作系统的运行环境'),
  (336, '操作系统', '计算机系统概述', '一小时速通408操作系统', 'Bilibili', 'https://www.bilibili.com/video/BV1V5nqzcErH', '优质推荐 · 408良子-令狐冲计算机 制作 · 播放 45341 次 · 与 计算机系统概述 高度相关', 'https://i2.hdslb.com/bfs/archive/a06e7c015ffdb5b64c5aebdd1f4f156022ab165d.jpg', '59:30', 0, 61, '408良子-令狐冲计算机', 'seed', '操作系统结构'),
  (337, '操作系统', '计算机系统概述', '408操作系统第四章1-文件管理-逻辑结构与物理结构以及真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1ku411E7HK', '就是氧气11 讲解 · 播放 23476 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/dae56ac0c432c3266f3c5cc53734dc21eaa821c6.jpg', '38:7', 0, 51, '就是氧气11', 'seed', '操作系统结构'),
  (338, '操作系统', '计算机系统概述', '【第1版用心版】24考研408王道课后题|操作系统—P142死锁', 'Bilibili', 'https://www.bilibili.com/video/BV1N14y127Mi', '计算机考研408小言 讲解 · 播放 9787 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/4e38fac100d421ee99df998a5bd35daba87043da.jpg', '55:33', 0, 53, '计算机考研408小言', 'seed', '操作系统结构'),
  (339, '操作系统', '计算机系统概述', '理清文件系统整体结构一个视频就够了『计算机考研408操作系统』', 'Bilibili', 'https://www.bilibili.com/video/BV1bF411X7fm', '零壹计算机考研 讲解 · 播放 8401 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/de9a06486d5151fa0396a8972bea0ec77c91bc2f.jpg', '57:55', 0, 55, '零壹计算机考研', 'seed', '操作系统结构'),
  (340, '操作系统', '计算机系统概述', '408考前终极防爆指南-冷门刺客列举', 'Bilibili', 'https://www.bilibili.com/video/BV1ZuqGBsETv', '俗伯阳-Soapayev 讲解 · 播放 7797 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/c5602d249abcaee612174a9796219bf72d4c6a38.jpg', '31:16', 0, 37, '俗伯阳-Soapayev', 'seed', '操作系统结构'),
  (341, '操作系统', '计算机系统概述', '408操作系统第三章1-内存管理（分页，分段，连续存储）及真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1R14y1q7eE', '就是氧气11 讲解 · 播放 38905 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/a4166737ce62142449d14f643ff62e41830a99d8.jpg', '37:26', 0, 51, '就是氧气11', 'seed', '操作系统引导'),
  (342, '操作系统', '计算机系统概述', '【408真题速通】存储系统综合问题：真题共考察20次，一个视频完整串起来', 'Bilibili', 'https://www.bilibili.com/video/BV1ovsHzNEkK', '王道计算机教育 讲解 · 播放 33659 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/d9be4bd8ce60aa4d6b4d074892f9a78946a71681.jpg', '36:38', 0, 37, '王道计算机教育', 'seed', '操作系统引导'),
  (343, '操作系统', '计算机系统概述', '我试图消灭所有不懂操作系统装入与链接之人！', 'Bilibili', 'https://www.bilibili.com/video/BV17fTLzCEbQ', 'Beokayy_ 讲解 · 播放 27992 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/53a17206091ddcb05f157aeff8d04e083bba78a4.jpg', '32:7', 0, 49, 'Beokayy_', 'seed', '操作系统引导'),
  (344, '操作系统', '计算机系统概述', '计算机408统考操作系统文件管理强化1', 'Bilibili', 'https://www.bilibili.com/video/BV1Uh4y1F7CP', '枕套1 讲解 · 播放 18933 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/d1c92c06cde0c81d7e86f86b2ce6b55645a91b1a.jpg', '30:12', 0, 53, '枕套1', 'seed', '操作系统引导'),
  (345, '操作系统', '计算机系统概述', '408操作系统第四章3-文件管理综合大题真题讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1hX4y1x73W', '就是氧气11 讲解 · 播放 18903 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/d078201e538d8729d5574355ceef633568e77729.jpg', '32:22', 0, 51, '就是氧气11', 'seed', '操作系统引导'),
  (346, '操作系统', '计算机系统概述', '操作系统强化专题-空闲空间管理与虚拟文件系统VFS', 'Bilibili', 'https://www.bilibili.com/video/BV1FT8kzCEBb', '就是氧气11 讲解 · 播放 2680 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/dbfa10cedb5259a0613c02e890f91bf5139401d1.jpg', '49:31', 0, 41, '就是氧气11', 'seed', '虚拟机'),
  (347, '操作系统', '计算机系统概述', '操作系统冲刺-程序，内核与虚拟机', 'Bilibili', 'https://www.bilibili.com/video/BV1PUkBBpEjW', '就是氧气11 讲解 · 播放 2648 次 · 覆盖 计算机系统概述 相关内容', 'https://i1.hdslb.com/bfs/archive/580a4975a1661a220dee7d57ab211ed5f8533844.jpg', '32:37', 0, 41, '就是氧气11', 'seed', '虚拟机'),
  (348, '操作系统', '计算机系统概述', '【考研408操作系统R1】29.操作系统结构和虚拟机', 'Bilibili', 'https://www.bilibili.com/video/BV1Bw4m1C7XW', 'Y4NGY 讲解 · 播放 1030 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/cb4b0350679a3aa2cd3df8b8ed1f1cb24d4a7bb1.jpg', '41:39', 0, 43, 'Y4NGY', 'seed', '虚拟机'),
  (349, '操作系统', '计算机系统概述', '一节课搞定操作系统进程与线程的所有知识点，25考研408备考新思路', 'Bilibili', 'https://www.bilibili.com/video/BV1Ry421q7EA', '图灵讲计组 讲解 · 播放 4545 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/83893c26f3b4a94add246317bd51d1d1c6524ec7.jpg', '53:45', 0, 43, '图灵讲计组', 'seed', '本章疑难点'),
  (350, '操作系统', '计算机系统概述', '2022操作系统408真题解析（含知识点梳理）', 'Bilibili', 'https://www.bilibili.com/video/BV1YG4y137vs', '李哥考研 讲解 · 播放 3266 次 · 覆盖 计算机系统概述 相关内容', 'https://i2.hdslb.com/bfs/archive/0d60a2f1713aff1cfd9f9b3be91ed88f79fd00ec.png', '39:14', 0, 41, '李哥考研', 'seed', '本章疑难点'),
  (351, '操作系统', '计算机系统概述', '408操作系统偏难冷知识点汇总', 'Bilibili', 'https://www.bilibili.com/video/BV1zWSgBnEEn', '晓旭QuQ 讲解 · 播放 3209 次 · 覆盖 计算机系统概述 相关内容', 'https://i0.hdslb.com/bfs/archive/2ccaee373fd029a89e4c6e0aae977134d697fd03.jpg', '47:11', 0, 41, '晓旭QuQ', 'seed', '本章疑难点'),
  (352, '操作系统', '计算机系统概述', '操作系统001-第一讲-考点1', 'Bilibili', 'https://www.bilibili.com/video/BV1H2421P7PP', '计算机考研刘财政 · 播放 916 次 · 与 计算机系统概述 相关', 'https://i2.hdslb.com/bfs/archive/a619024257ce89ee584337a831125d8eb4378c21.png', '48:0', 0, 29, '计算机考研刘财政', 'seed', '本章疑难点'),
  (353, '操作系统', '计算机系统概述', '操作系统006-第二讲-考点1', 'Bilibili', 'https://www.bilibili.com/video/BV17A4m1P7oN', '计算机考研刘财政 · 播放 170 次 · 与 计算机系统概述 相关', 'https://i1.hdslb.com/bfs/archive/006e70f2ee44bbc75c608bba1b3153c0dc5cdd89.png', '39:25', 0, 29, '计算机考研刘财政', 'seed', '本章疑难点'),
  (354, '操作系统', '进程与线程', '操作系统强化专题-进程切换及进程与线程', 'Bilibili', 'https://www.bilibili.com/video/BV1ATuUzLEgF', '就是氧气11 讲解 · 播放 4539 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/a14b139ea13f1dc645fd6374cc743d3627a16a9c.jpg', '39:24', 0, 57, '就是氧气11', 'seed', '进程与线程简介'),
  (355, '操作系统', '进程与线程', '操作系统-第二章 进程与线程-408复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1WN1wBoE7a', '必须好好读研 讲解 · 播放 319 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/b9dec05b3f4216c03ddeff2066cb188b8f933b2d.jpg', '53:12', 0, 47, '必须好好读研', 'seed', '进程与线程简介'),
  (356, '操作系统', '进程与线程', '408操作系统第二章2.1.2进程与线程', 'Bilibili', 'https://www.bilibili.com/video/BV1RW4y1x7fT', 'Rita2018- 讲解 · 播放 110 次 · 覆盖 进程与线程 相关内容', 'https://i2.hdslb.com/bfs/archive/c342c21ed84abc53c12e6760d6acd79594c27e89.jpg', '53:4', 0, 47, 'Rita2018-', 'seed', '进程与线程简介'),
  (357, '操作系统', '进程与线程', '操作系统强化专题-进程的同步与互斥', 'Bilibili', 'https://www.bilibili.com/video/BV1hdg5zqEdg', '就是氧气11 讲解 · 播放 2855 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/5132e2f1310044fa01be17e090998ec354ce1442.jpg', '31:4', 0, 41, '就是氧气11', 'seed', '进程与线程简介'),
  (358, '操作系统', '进程与线程', '操作系统冲刺-进程切换与进线程实现', 'Bilibili', 'https://www.bilibili.com/video/BV1FVkmBMELf', '就是氧气11 讲解 · 播放 2526 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/461ea5e3ba5bbb3907f0ad01f6d49c0149a5de7a.jpg', '40:31', 0, 41, '就是氧气11', 'seed', '进程与线程简介'),
  (359, '操作系统', '进程与线程', '操作系统强化专题-进程调度', 'Bilibili', 'https://www.bilibili.com/video/BV1LNgvzAEpp', '就是氧气11 讲解 · 播放 2463 次 · 覆盖 进程与线程 相关内容', 'https://i0.hdslb.com/bfs/archive/76016efd45f50295382acc4888f14d84a86fe785.jpg', '36:10', 0, 41, '就是氧气11', 'seed', 'CPU调度'),
  (360, '操作系统', '进程与线程', '《操作系统》实验5（代码）实时调试算法模拟EDF/RMS甘特图', 'Bilibili', 'https://www.bilibili.com/video/BV1J72oYDECZ', '为学习服务 讲解 · 播放 1569 次 · 覆盖 进程与线程 相关内容', 'https://i2.hdslb.com/bfs/archive/20c9b200210b2942b0cede2b1187515e9b4b810a.jpg', '30:4', 0, 39, '为学习服务', 'seed', 'CPU调度'),
  (361, '操作系统', '进程与线程', '408新考纲，多CPU调度详细讲解', 'Bilibili', 'https://www.bilibili.com/video/BV1NstVeGEex', '李哥考研 · 播放 8654 次 · 与 进程与线程 相关', 'https://i2.hdslb.com/bfs/archive/fdc9d0d57db4a33881cfea18f30b100dba382d4a.jpg', '34:27', 0, 37, '李哥考研', 'seed', 'CPU调度'),
  (362, '操作系统', '进程与线程', '27操作系统基础-磁盘的结构与调度算法', 'Bilibili', 'https://www.bilibili.com/video/BV18pdqBtEBx', '就是氧气11 · 播放 559 次 · 与 进程与线程 相关', 'https://i2.hdslb.com/bfs/archive/de0d8737b00900771792e189c39262e6bac10b5c.jpg', '30:14', 0, 31, '就是氧气11', 'seed', 'CPU调度'),
  (363, '操作系统', '进程与线程', 'K16.处理器调度【考研408操作系统R2】', 'Bilibili', 'https://www.bilibili.com/video/BV1S81dYfEMR', 'Y4NGY · 播放 412 次 · 与 进程与线程 相关', 'https://i0.hdslb.com/bfs/archive/ce51f8f636239d331e1f8588d0f5972e9f84e3a9.jpg', '39:29', 0, 33, 'Y4NGY', 'seed', 'CPU调度'),
  (364, '操作系统', '进程与线程', 'Hive-III.1.进程同步大题模块化训练【考研408操作系统R3】', 'Bilibili', 'https://www.bilibili.com/video/BV1kwqmYqEjw', 'Y4NGY 讲解 · 播放 1455 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/f6eefead7346e699371e84d4fd4748262a2639d7.jpg', '36:42', 0, 43, 'Y4NGY', 'seed', '同步与互斥'),
  (365, '操作系统', '进程与线程', 'Hive-III.2.进程同步大题分步解题【考研408操作系统R3】', 'Bilibili', 'https://www.bilibili.com/video/BV1XkBuYSEwm', 'Y4NGY 讲解 · 播放 1428 次 · 覆盖 进程与线程 相关内容', 'https://i0.hdslb.com/bfs/archive/2469eeedc0a8150d5a60ce6cec25e3c9b643e74a.jpg', '44:29', 0, 43, 'Y4NGY', 'seed', '同步与互斥'),
  (366, '操作系统', '进程与线程', '27操作系统基础-进程的同步与互斥', 'Bilibili', 'https://www.bilibili.com/video/BV1UCDAB7EcB', '就是氧气11 讲解 · 播放 792 次 · 覆盖 进程与线程 相关内容', 'https://i2.hdslb.com/bfs/archive/0e2185dc4329e2ca043a349e5a03bfdc6cdf81d8.jpg', '36:24', 0, 41, '就是氧气11', 'seed', '同步与互斥'),
  (367, '操作系统', '进程与线程', 'os从未考过的新增考点！条件变量与同步互斥（操作系统小观03）', 'Bilibili', 'https://www.bilibili.com/video/BV1Vc1gBaEZX', '花田慎鸾交 · 播放 2679 次 · 与 进程与线程 相关', 'https://i1.hdslb.com/bfs/archive/d9916da36af0827bb99e2325c0da747915f0cc4a.jpg', '31:6', 0, 41, '花田慎鸾交', 'seed', '同步与互斥'),
  (368, '操作系统', '进程与线程', '408操作系统解题步骤总结丨同步与互斥-生产消费者问题', 'Bilibili', 'https://www.bilibili.com/video/BV19RGJz8EyG', '启航计算机考研 · 播放 918 次 · 与 进程与线程 相关', 'https://i1.hdslb.com/bfs/archive/2eba16d71e33e47734acbda17f7ec62832c2f8b7.jpg', '51:18', 0, 35, '启航计算机考研', 'seed', '同步与互斥'),
  (369, '操作系统', '进程与线程', '操作系统复盘 进程与线程4（死锁、银行家算法） 20240718', 'Bilibili', 'https://www.bilibili.com/video/BV18x4y147AG', '布偶小喵11408 讲解 · 播放 167 次 · 覆盖 进程与线程 相关内容', 'https://i1.hdslb.com/bfs/archive/fcf1bc8c2d5ba5c0250f38f732595d001549cef7.jpg', '30:16', 0, 45, '布偶小喵11408', 'seed', '死锁'),
  (370, '操作系统', '进程与线程', '操作系统强化专题-管程与死锁', 'Bilibili', 'https://www.bilibili.com/video/BV1Hg8cz8Esn', '就是氧气11 讲解 · 播放 2654 次 · 覆盖 进程与线程 相关内容', 'https://i2.hdslb.com/bfs/archive/2544ebddb8726cc68b63f8c05f127f0231de0f06.jpg', '34:35', 0, 41, '就是氧气11', 'seed', '死锁'),
  (371, '操作系统', '进程与线程', '操作系统原理13a（伪）：死锁小结&amp;进程通信机制&amp;计算机启动过程与BIOS', 'Bilibili', 'https://www.bilibili.com/video/BV1Cs4y117AT', 'zhengwei_xmucs · 播放 1094 次 · 与 进程与线程 相关', 'https://i0.hdslb.com/bfs/archive/24107e9e7035bbe8645368c474026c9eef8873e6.jpg', '55:45', 0, 41, 'zhengwei_xmucs', 'seed', '死锁'),
  (372, '操作系统', '进程与线程', '第2章 进程与线程-2.4 死锁-操作系统OS-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1J1YSzrEHw', '必须好好读研 · 播放 33 次 · 与 进程与线程 相关', 'https://i0.hdslb.com/bfs/archive/bb0dbe170dcd32edbd619beded7c0b0d7903e9fb.jpg', '32:27', 0, 40, '必须好好读研', 'seed', '死锁'),
  (373, '操作系统', '进程与线程', 'p10【番外篇】刷真题和课后题 进程（下）+ cpu的调度和死锁', 'Bilibili', 'https://www.bilibili.com/video/BV11w411z75G', 'JustinAndCindy · 播放 314 次 · 与 进程与线程 相关', 'https://i2.hdslb.com/bfs/archive/0c1f6c6b8479cf9ce815f7aff13fd2bec8db6018.jpg', '38:28', 0, 33, 'JustinAndCindy', 'seed', '死锁'),
  (374, '操作系统', '内存管理', '【考研408操统】用图讲清楚基本分页存储管理！| 内存管理(三)', 'Bilibili', 'https://www.bilibili.com/video/BV1zh4y1i7iD', '优质推荐 · 小狗走两步 制作 · 播放 14816 次 · 与 内存管理 高度相关', 'https://i1.hdslb.com/bfs/archive/72d04fc53eb4e789f4f7d005d8b223c5a947970b.jpg', '54:21', 0, 69, '小狗走两步', 'seed', '内存管理概念'),
  (375, '操作系统', '内存管理', 'Hive-II.1.内存管理大题模块化训练【考研408操作系统R3】', 'Bilibili', 'https://www.bilibili.com/video/BV17r6NYQE4h', 'Y4NGY 讲解 · 播放 1555 次 · 覆盖 内存管理 相关内容', 'https://i2.hdslb.com/bfs/archive/aa81c6d83c28b8232757c61fccfcb6b52c0795d7.jpg', '45:15', 0, 59, 'Y4NGY', 'seed', '内存管理概念'),
  (376, '操作系统', '内存管理', '《开源巨全408导图》操作系统：内存管理', 'Bilibili', 'https://www.bilibili.com/video/BV1j9XyYFEem', '408小牛 讲解 · 播放 384 次 · 覆盖 内存管理 相关内容', 'https://i2.hdslb.com/bfs/archive/3d79a774285e7a8eb4db1ccc16b67a6f435f430a.jpg', '48:22', 0, 47, '408小牛', 'seed', '内存管理概念'),
  (377, '操作系统', '内存管理', '408操作系统第三章3.1.1内存管理 连续分配', 'Bilibili', 'https://www.bilibili.com/video/BV1i84y1y7Kc', 'Rita2018- 讲解 · 播放 101 次 · 覆盖 内存管理 相关内容', 'https://i2.hdslb.com/bfs/archive/c342c21ed84abc53c12e6760d6acd79594c27e89.jpg', '32:32', 0, 47, 'Rita2018-', 'seed', '内存管理概念'),
  (378, '操作系统', '内存管理', '【操作系统】考研大纲梳理直播回放（3.2、虚拟内存管理）中', 'Bilibili', 'https://www.bilibili.com/video/BV1aw411b7LX', '操作系统艾老师 讲解 · 播放 350 次 · 覆盖 内存管理 相关内容', 'https://i2.hdslb.com/bfs/archive/06148af6bce274ab37957675ecc309850d73c75f.jpg', '35:40', 0, 47, '操作系统艾老师', 'seed', '内存管理概念'),
  (379, '操作系统', '内存管理', '操作系统-第三章 内存管理-408复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1pZ17BiEnA', '必须好好读研 · 播放 62 次 · 与 内存管理 相关', 'https://i1.hdslb.com/bfs/archive/d78d115ec1d1ac51ce5ce1d057ab059ed40012a1.jpg', '36:6', 0, 42, '必须好好读研', 'seed', '虚拟内存管理'),
  (380, '操作系统', '内存管理', '408虚拟地址转物理地址', 'Bilibili', 'https://www.bilibili.com/video/BV1S14y1H7qq', '小杜777 · 播放 401 次 · 与 内存管理 相关', 'https://i1.hdslb.com/bfs/archive/8033267e5ef28e1b6f6c10893767b7110f9e5134.jpg', '32:6', 0, 31, '小杜777', 'seed', '虚拟内存管理'),
  (381, '操作系统', '文件管理', '【26考前押题】OS救急，务必看完这道题，文件大题统统秒杀！', 'Bilibili', 'https://www.bilibili.com/video/BV1FN2iBUEEM', '优质推荐 · 令狐冲计算机考研 制作 · 播放 8471 次 · 与 文件管理 高度相关', 'https://i2.hdslb.com/bfs/archive/fd01e5abc9768891bc1cfeffffc1e34958b7856c.jpg', '40:58', 0, 63, '令狐冲计算机考研', 'seed', '文件系统基础'),
  (382, '操作系统', '文件管理', '计算机408统考操作系统文件管理强化2', 'Bilibili', 'https://www.bilibili.com/video/BV1j84y1f7st', '优质推荐 · 枕套1 制作 · 播放 8415 次 · 与 文件管理 高度相关', 'https://i1.hdslb.com/bfs/archive/430f3457590a1899e15023294b6b6471841c5300.jpg', '53:54', 0, 69, '枕套1', 'seed', '文件系统基础'),
  (383, '操作系统', '文件管理', '操作系统第四章文件管理大题真题复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1fT4Hz3E1P', '慢宋宋宋宋 讲解 · 播放 1849 次 · 覆盖 文件管理 相关内容', 'https://i1.hdslb.com/bfs/archive/1c3444d41ccabb60654e50e9207143fe9187680d.jpg', '50:7', 0, 55, '慢宋宋宋宋', 'seed', '文件系统基础'),
  (384, '操作系统', '文件管理', '《开源巨全408导图》操作系统：文件管理', 'Bilibili', 'https://www.bilibili.com/video/BV1q9XyYFEyb', '408小牛 讲解 · 播放 367 次 · 覆盖 文件管理 相关内容', 'https://i0.hdslb.com/bfs/archive/f8a0e9676e1507f44da40f453fd8e0b668aa7b1a.jpg', '48:24', 0, 47, '408小牛', 'seed', '文件系统基础'),
  (385, '操作系统', '文件管理', '操作系统文件管理', 'Bilibili', 'https://www.bilibili.com/video/BV1bcmMYwEih', '布偶小喵11408 讲解 · 播放 255 次 · 覆盖 文件管理 相关内容', 'https://i0.hdslb.com/bfs/archive/6bf242527e2724666b7b650f03f12aaa05e4dbfb.jpg', '34:41', 0, 45, '布偶小喵11408', 'seed', '文件系统基础'),
  (386, '操作系统', '文件管理', '操作系统034-第7讲-文件管理专题', 'Bilibili', 'https://www.bilibili.com/video/BV1Jm421V7e7', '计算机考研刘财政 讲解 · 播放 189 次 · 覆盖 文件管理 相关内容', 'https://i0.hdslb.com/bfs/archive/2d673e1aa9a712415f9d98e5c63342d09b9b6680.jpg', '47:39', 0, 45, '计算机考研刘财政', 'seed', '目录与文件'),
  (387, '操作系统', '文件管理', '【操作系统】考研大纲梳理直播回放（4、文件管理）上', 'Bilibili', 'https://www.bilibili.com/video/BV1De411d7NG', '操作系统艾老师 讲解 · 播放 588 次 · 覆盖 文件管理 相关内容', 'https://i1.hdslb.com/bfs/archive/65bba8fadb38d0b2a8465245175a0e43fd89452e.jpg', '30:53', 0, 47, '操作系统艾老师', 'seed', '目录与文件'),
  (388, '操作系统', '文件管理', '【操作系统】考研大纲梳理直播回放（4、文件管理）下', 'Bilibili', 'https://www.bilibili.com/video/BV1cC4y1X7Ev', '操作系统艾老师 讲解 · 播放 437 次 · 覆盖 文件管理 相关内容', 'https://i1.hdslb.com/bfs/archive/3277f296ce4a0070066e31df319c0aab1db8ba43.jpg', '30:37', 0, 47, '操作系统艾老师', 'seed', '目录与文件'),
  (389, '操作系统', '文件管理', '文件系统-物理组织与磁盘管理', 'Bilibili', 'https://www.bilibili.com/video/BV17KH1zaEXb', '俗伯阳-Soapayev · 播放 463 次 · 与 文件管理 相关', 'https://i1.hdslb.com/bfs/archive/3ddc947d4b64cdecb8055822eaafeea1d051ff72.jpg', '54:36', 0, 15, '俗伯阳-Soapayev', 'seed', '目录与文件'),
  (390, '操作系统', '文件管理', '操作系统-第四章 文件管理-408复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1Zk1xBUEKC', '必须好好读研 讲解 · 播放 203 次 · 覆盖 文件管理 相关内容', 'https://i0.hdslb.com/bfs/archive/17a6634e93fa7adfc2762e2f51eb0dbc1474e12c.jpg', '40:16', 0, 47, '必须好好读研', 'seed', '文件系统'),
  (391, '操作系统', '输入输出管理', '操作系统半小时知识点记忆，设备分配与回收，磁盘，磁盘调度算法，固态硬盘SSD（操作系统复习完毕啦）', 'Bilibili', 'https://www.bilibili.com/video/BV1tb411f7Sm', '费棍 · 播放 1407 次 · 与 输入输出管理 相关', 'https://i0.hdslb.com/bfs/archive/d7601543af32a49478ca513511b7255c629c66c5.jpg', '41:45', 0, 39, '费棍', 'seed', '磁盘和固态硬盘'),
  (392, '操作系统', '输入输出管理', '91.磁盘管理【考研408操作系统R1#会员课】', 'Bilibili', 'https://www.bilibili.com/video/BV1N146eUENZ', 'Y4NGY · 播放 707 次 · 与 输入输出管理 相关', 'https://i0.hdslb.com/bfs/archive/5a1c2d6dbc2f008ff49924df90f9fc5dcf9a883c.jpg', '50:19', 0, 33, 'Y4NGY', 'seed', '磁盘和固态硬盘'),
  (393, '操作系统', '输入输出管理', '计算机组成原理复盘—存储系统2（字扩展、位扩展、字位扩展、磁盘存储器、固态硬盘） 20240504', 'Bilibili', 'https://www.bilibili.com/video/BV1Wf421D7cx', '布偶小喵11408 · 播放 631 次 · 与 输入输出管理 相关', 'https://i1.hdslb.com/bfs/archive/298fe043b1564151d1c208aebfb9519e8718a5d3.jpg', '41:48', 0, 17, '布偶小喵11408', 'seed', '磁盘和固态硬盘'),
  (394, '操作系统', '输入输出管理', '老哥们咱们今天使用ssd固态硬盘SATA3转物理虚拟磁盘的VMware虚拟机安装Applemacos12', 'Bilibili', 'https://www.bilibili.com/video/BV1nw9tY9EY1', '一个七搞数码 · 播放 209 次 · 与 输入输出管理 相关', 'https://i2.hdslb.com/bfs/archive/81d3574c1a3352ff730ec816e3d2839bc0ef8eab.jpg', '35:11', 0, 15, '一个七搞数码', 'seed', '磁盘和固态硬盘'),
  (395, '计算机网络', '计算机网络体系结构', '【408计网】 网工学长带你分章节吃透历年真题 | 开课引言与计算机网络体系结构', 'Bilibili', 'https://www.bilibili.com/video/BV1bdh9zYEob', '半幺郎 讲解 · 播放 7235 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i0.hdslb.com/bfs/archive/76b7c532a75cb9f5b2cf1d461a439c7af490568b.jpg', '47:28', 0, 61, '半幺郎', 'seed', '计算机网络概述'),
  (396, '计算机网络', '计算机网络体系结构', '[408大观·寄网] 第一章 计算机网络体系结构', 'Bilibili', 'https://www.bilibili.com/video/BV1iNxozqEd2', '我还是想当408高手 讲解 · 播放 1230 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i0.hdslb.com/bfs/archive/866d732e7180d2de1bcf96d690e751c7f74c3fac.jpg', '46:58', 0, 61, '我还是想当408高手', 'seed', '计算机网络概述'),
  (397, '计算机网络', '计算机网络体系结构', '408考前押题！计算机网络最后4道必刷大题精讲！', 'Bilibili', 'https://www.bilibili.com/video/BV19ZmkB8EHR', '哈喜老师 讲解 · 播放 29429 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i0.hdslb.com/bfs/archive/42b76cce13ed32636cff6d325587b25985b17156.jpg', '35:37', 0, 53, '哈喜老师', 'seed', '计算机网络概述'),
  (398, '计算机网络', '计算机网络体系结构', '【残云】湖科大教书匠2025模拟卷一：全套详细解析版 | 408计网', 'Bilibili', 'https://www.bilibili.com/video/BV1LS23BrESn', '残云1448 讲解 · 播放 7941 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i2.hdslb.com/bfs/archive/cebcad3fc37105aec3b06e9a954b31b581faa3db.jpg', '35:5', 0, 27, '残云1448', 'seed', '计算机网络概述'),
  (399, '计算机网络', '计算机网络体系结构', '【残云】湖科大教书匠2025模拟卷二：全套详细解析版 | 408计网', 'Bilibili', 'https://www.bilibili.com/video/BV19d2oBPE9D', '残云1448 讲解 · 播放 4602 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i2.hdslb.com/bfs/archive/b5331c8e63acd3568fddf4a7fef6b5d28a25ca81.jpg', '30:50', 0, 27, '残云1448', 'seed', '计算机网络概述'),
  (400, '计算机网络', '计算机网络体系结构', '计网体系汇总版（考点和考法）', 'Bilibili', 'https://www.bilibili.com/video/BV1cdYyz8EXX', '22408练习生 讲解 · 播放 4120 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i2.hdslb.com/bfs/archive/2b3546867cd5a879c2a5a227de0eac37142b06a1.jpg', '40:45', 0, 27, '22408练习生', 'seed', '计算机网络体系结构与参考模型');
INSERT INTO `video_resource` (`id`, `subject`, `knowledge_point`, `title`, `platform`, `url`, `reason`, `cover_url`, `duration`, `is_deleted`, `quality_score`, `author`, `crawl_source`, `section`) VALUES
  (401, '计算机网络', '计算机网络体系结构', '408计网体系结构：一张图宏观理解计算机网络', 'Bilibili', 'https://www.bilibili.com/video/BV1XZ421T7fR', '图灵讲计组 讲解 · 播放 3724 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i1.hdslb.com/bfs/archive/f93b11d6250e716ae7e6756a461eb92ca5ba9e0c.jpg', '30:22', 0, 43, '图灵讲计组', 'seed', '计算机网络体系结构与参考模型'),
  (402, '计算机网络', '计算机网络体系结构', '计网冲刺-以太网与无线局域网', 'Bilibili', 'https://www.bilibili.com/video/BV1ASUnBnEBW', '就是氧气11 讲解 · 播放 2245 次 · 覆盖 计算机网络体系结构 相关内容', 'https://i1.hdslb.com/bfs/archive/6b0c2ceae3e8cb6132ba75a5c00a7460ab27979f.jpg', '31:47', 0, 27, '就是氧气11', 'seed', '计算机网络体系结构与参考模型'),
  (403, '计算机网络', '计算机网络体系结构', '《开源巨全408导图》计网：网络层', 'Bilibili', 'https://www.bilibili.com/video/BV1ZHXzY1EGa', '408小牛 · 播放 287 次 · 与 计算机网络体系结构 相关', 'https://i0.hdslb.com/bfs/archive/94eaec74e94dfcd69cbdbb4da809bf5199b1ec3b.jpg', '59:6', 0, 17, '408小牛', 'seed', '计算机网络体系结构与参考模型'),
  (404, '计算机网络', '物理层', '第2章 物理层-2.1 通信基础-编码与调制+习题-计算机网络-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1TwpUzdEBi', '必须好好读研 · 播放 83 次 · 与 物理层 相关', 'https://i1.hdslb.com/bfs/archive/7cc85e524f1ed0a5b46b3a3657d488978d93915c.jpg', '38:50', 0, 42, '必须好好读研', 'seed', '通信基础'),
  (405, '计算机网络', '物理层', '2025年合肥工业大学868半导体物理真题逐题精讲｜难度不大题量少，平时多注重基础 ｜通信考研｜合肥工业大学868电子通信考研', 'Bilibili', 'https://www.bilibili.com/video/BV1hPJCzuESR', '电子通信考研 · 播放 1172 次 · 与 物理层 相关', 'https://i0.hdslb.com/bfs/archive/0a50ba1bf1486723234b54aeefe8c10a511b6ea8.jpg', '44:28', 0, 27, '电子通信考研', 'seed', '通信基础'),
  (406, '计算机网络', '物理层', '25届哈尔滨工业大学826电子技术基础、877大学物理报考细则|哈工大仪器院、卓工院|25电子通信考研', 'Bilibili', 'https://www.bilibili.com/video/BV1yr421s7rS', '水木观畴电子通信考研 · 播放 903 次 · 与 物理层 相关', 'https://i1.hdslb.com/bfs/archive/a4d18a4d2e4030e9a032d62740ce1a64d4f8dade.jpg', '33:16', 0, 17, '水木观畴电子通信考研', 'seed', '通信基础'),
  (407, '计算机网络', '物理层', '2025年合肥工业大学868半导体物理真题逐题精讲｜难度不大题量少 平时多注重基础｜电子考研｜南邮电子通信考研', 'Bilibili', 'https://www.bilibili.com/video/BV1mWnWz2EDD', '水木观畴电子通信考研 · 播放 630 次 · 与 物理层 相关', 'https://i2.hdslb.com/bfs/archive/b6eb9f4ae19756c1dc3ec1b2b83dae8a30a9ff9a.jpg', '44:29', 0, 17, '水木观畴电子通信考研', 'seed', '通信基础'),
  (408, '计算机网络', '物理层', '【全网最详细】26天大813/814/815复试扫盲科普，不会准备复试、获取信息？不知道什么时候联系导师？天大直系学长带你进阶为复试大神！|电子信息考研', 'Bilibili', 'https://www.bilibili.com/video/BV1kpvHBSEWd', '水木观畴电子通信考研 · 播放 606 次 · 与 物理层 相关', 'https://i1.hdslb.com/bfs/archive/2e4c558365deefa0862fcf7168d6a26d3c8bc846.jpg', '37:26', 0, 17, '水木观畴电子通信考研', 'seed', '通信基础'),
  (409, '计算机网络', '物理层', '4.物理层传输介质及网络设备', 'Bilibili', 'https://www.bilibili.com/video/BV19LC4BuEZi', '新星云网络 · 播放 55 次 · 与 物理层 相关', 'https://i2.hdslb.com/bfs/archive/3adff944c24ae5a30417e3a9b7cfd38fc3524471.jpg', '56:16', 0, 38, '新星云网络', 'seed', '传输介质'),
  (410, '计算机网络', '物理层', '第三章 物理层 第7节课 3.2传输介质', 'Bilibili', 'https://www.bilibili.com/video/BV116poeHENo', '全栈研究所 · 播放 18 次 · 与 物理层 相关', 'https://i1.hdslb.com/bfs/archive/f4b20bfd3543ab2a65afbfaf40d0d564d76c9d61.jpg', '32:1', 0, 42, '全栈研究所', 'seed', '传输介质'),
  (411, '计算机网络', '物理层', '计网5.3 TCP（TCP首部、TCP连接、TCP传输、TCP流量控制、TCP拥塞控制）', 'Bilibili', 'https://www.bilibili.com/video/BV1Gu411V7pN', '吃葡萄不吐葡萄皮ooc · 播放 713 次 · 与 物理层 相关', 'https://i1.hdslb.com/bfs/archive/f6271886239b0bf84ce5f0f074c4a08f81057b51.jpg', '35:46', 0, 15, '吃葡萄不吐葡萄皮ooc', 'seed', '传输介质'),
  (412, '计算机网络', '物理层', '408复盘-计网-绪论+传输层', 'Bilibili', 'https://www.bilibili.com/video/BV1yP11BjEiv', '22408小手子 · 播放 602 次 · 与 物理层 相关', 'https://i0.hdslb.com/bfs/archive/3e2448e2a59935c282f95e90a50b97d502f48ea1.jpg', '58:43', 0, 17, '22408小手子', 'seed', '传输介质'),
  (413, '计算机网络', '物理层', '计算机网络串讲-物理层', 'Bilibili', 'https://www.bilibili.com/video/BV1id4y117E9', '优质推荐 · Beokayy_ 制作 · 播放 62312 次 · 与 物理层 高度相关', 'https://i0.hdslb.com/bfs/archive/ad3d945709742e2ec9aaa596bd4387a35ae9af94.jpg', '48:23', 0, 77, 'Beokayy_', 'seed', '物理层设备'),
  (414, '计算机网络', '物理层', '计算机网络 408 考研 历年 真题解析【物理层】（字幕版）', 'Bilibili', 'https://www.bilibili.com/video/BV1fa4y147Q8', '优质推荐 · 湖科大教书匠 制作 · 播放 20844 次 · 与 物理层 高度相关', 'https://i2.hdslb.com/bfs/archive/d61559448aa03f82c5bc7d9e836af5aee5415542.jpg', '40:39', 0, 71, '湖科大教书匠', 'seed', '物理层设备'),
  (415, '计算机网络', '物理层', '计算机网络 408 考研 历年 真题解析【物理层】（无字幕版）', 'Bilibili', 'https://www.bilibili.com/video/BV1Gz411b79P', '湖科大教书匠 讲解 · 播放 3812 次 · 覆盖 物理层 相关内容', 'https://i1.hdslb.com/bfs/archive/c73b50d28c02ccae10fdbcd124c366c990eca75b.jpg', '34:3', 0, 61, '湖科大教书匠', 'seed', '物理层设备'),
  (416, '计算机网络', '物理层', '计算机网络强化专题-物理层', 'Bilibili', 'https://www.bilibili.com/video/BV1KwtFzFEt6', '就是氧气11 讲解 · 播放 2923 次 · 覆盖 物理层 相关内容', 'https://i2.hdslb.com/bfs/archive/130f1927620d0e2d3a3be80a4935fd7cb9832636.jpg', '47:19', 0, 59, '就是氧气11', 'seed', '物理层设备'),
  (417, '计算机网络', '物理层', '计网各层设备汇总版（考点专题）', 'Bilibili', 'https://www.bilibili.com/video/BV1Vmn9zCE3e', '22408练习生 讲解 · 播放 2563 次 · 覆盖 物理层 相关内容', 'https://i1.hdslb.com/bfs/archive/40e56803cf4c758993bec01cafe3c8b53ec69c7e.jpg', '52:30', 0, 53, '22408练习生', 'seed', '物理层设备'),
  (418, '计算机网络', '数据链路层', '第3章 数据链路层（背诵手册 音视频版）', 'Bilibili', 'https://www.bilibili.com/video/BV1JzNteUEj9', '优质推荐 · 湖科大教书匠 制作 · 播放 12732 次 · 与 数据链路层 高度相关', 'https://i0.hdslb.com/bfs/archive/2b3959fb1d0b296938049d2f765af0838b50cf81.jpg', '31:48', 0, 63, '湖科大教书匠', 'seed', '数据链路层的功能'),
  (419, '计算机网络', '数据链路层', '计算机网络强化专题-数据链路层及检错纠错编码', 'Bilibili', 'https://www.bilibili.com/video/BV1hLtvzTEmd', '就是氧气11 讲解 · 播放 2659 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/f631bd35cf66eb1e3b4217c5028e8f4d050d279b.jpg', '33:11', 0, 59, '就是氧气11', 'seed', '数据链路层的功能'),
  (420, '计算机网络', '数据链路层', '【计算机考研-408】计算机网络之数据链路层', 'Bilibili', 'https://www.bilibili.com/video/BV14q4y1m7Nu', '我不叫二进制 讲解 · 播放 454 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/7b6ebc034b70073ed8d99d9035045cc05f3c80c1.jpg', '34:1', 0, 51, '我不叫二进制', 'seed', '数据链路层的功能'),
  (421, '计算机网络', '数据链路层', '《开源巨全408导图》计网：数据链路层', 'Bilibili', 'https://www.bilibili.com/video/BV1oHXzY1EBZ', '408小牛 讲解 · 播放 266 次 · 覆盖 数据链路层 相关内容', 'https://i0.hdslb.com/bfs/archive/073cb3a56c5d1b3eeb9a935003e64fe61a5ccaad.jpg', '50:47', 0, 45, '408小牛', 'seed', '数据链路层的功能'),
  (422, '计算机网络', '数据链路层', '【计算机网络速成课04数据链路层（下）】，第三章数据链路链路层，期末看这个就足够了哦！', 'Bilibili', 'https://www.bilibili.com/video/BV1G5Vh63EMq', '计算机考研大师兄 讲解 · 播放 158 次 · 覆盖 数据链路层 相关内容', 'https://i1.hdslb.com/bfs/archive/e787686bee9d8608afb6e134011e16dfa8aa8bae.jpg', '38:3', 0, 47, '计算机考研大师兄', 'seed', '数据链路层的功能'),
  (423, '计算机网络', '数据链路层', '2024考研计算机408基础网课：数据链路层2 ｜0基础跨专业必刷课程', 'Bilibili', 'https://www.bilibili.com/video/BV1hs4y1C7M7', '金程考研辅导 讲解 · 播放 50 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/d0ff35e13974f4c12a56a3c49274285a714d357a.jpg', '38:7', 0, 46, '金程考研辅导', 'seed', '组帧'),
  (424, '计算机网络', '数据链路层', '2024考研计算机408基础网课：数据链路层1 ｜0基础跨专业必刷课程', 'Bilibili', 'https://www.bilibili.com/video/BV1zF411d7Gn', '金程考研辅导 讲解 · 播放 47 次 · 覆盖 数据链路层 相关内容', 'https://i0.hdslb.com/bfs/archive/c9c46b319a693e478355a804b4bd7423b44e9a9f.jpg', '57:52', 0, 46, '金程考研辅导', 'seed', '组帧'),
  (425, '计算机网络', '数据链路层', '《开源巨全408导图》计网：物理层', 'Bilibili', 'https://www.bilibili.com/video/BV1oHXzY1E6a', '408小牛 · 播放 214 次 · 与 数据链路层 相关', 'https://i2.hdslb.com/bfs/archive/889c349f6a97c72f452dd80534638a951fc34f84.jpg', '42:41', 0, 17, '408小牛', 'seed', '组帧'),
  (426, '计算机网络', '数据链路层', '【数据链路层】介质访问控制', 'Bilibili', 'https://www.bilibili.com/video/BV18bxbzjEoG', '情敌贝多芬的心跳 讲解 · 播放 686 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/1764d5e12ac0f71049dd40b04047f1c11dcd1f88.jpg', '30:57', 0, 43, '情敌贝多芬的心跳', 'seed', '差错控制'),
  (427, '计算机网络', '数据链路层', '2024考研计算机408基础网课：数据链路层3 ｜0基础跨专业必刷课程', 'Bilibili', 'https://www.bilibili.com/video/BV1Qm4y1e75R', '金程考研辅导 讲解 · 播放 44 次 · 覆盖 数据链路层 相关内容', 'https://i1.hdslb.com/bfs/archive/06285ada9bcc9d63b04c7c59c8230fab9d037d6f.jpg', '54:42', 0, 46, '金程考研辅导', 'seed', '差错控制'),
  (428, '计算机网络', '数据链路层', '计算机网络复盘 数据链路层1（差错检测、可靠传输） 20240810', 'Bilibili', 'https://www.bilibili.com/video/BV1kJY7efEPX', '布偶小喵11408 讲解 · 播放 244 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/1a335ee814e82e4aa974f4f9fcd11aafa3fceb73.jpg', '52:37', 0, 49, '布偶小喵11408', 'seed', '流量控制与可靠传输机制'),
  (429, '计算机网络', '数据链路层', '11数据链路层-封装成帧、透明传输（字符填充）、差错控制（循环冗余检错码CRC）', 'Bilibili', 'https://www.bilibili.com/video/BV171421f7aw', '常cc_ 讲解 · 播放 705 次 · 覆盖 数据链路层 相关内容', 'https://i1.hdslb.com/bfs/archive/874027fc9199a72564cf5b9d1e7a70d176e98f78.jpg', '42:35', 0, 43, '常cc_', 'seed', '流量控制与可靠传输机制'),
  (430, '计算机网络', '数据链路层', '第3章 数据链路层-3.4 流量控制与可靠传输机制-计算机网络-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV159WGzMEKE', '必须好好读研 讲解 · 播放 85 次 · 覆盖 数据链路层 相关内容', 'https://i2.hdslb.com/bfs/archive/fe530e0eb45b0d459a77b5c35627b4f2f0581049.jpg', '49:24', 0, 47, '必须好好读研', 'seed', '流量控制与可靠传输机制'),
  (431, '计算机网络', '数据链路层', '6.15.超文本传输协议：HTTP', 'Bilibili', 'https://www.bilibili.com/video/BV1YK411X7UQ', '彭彭学编程 讲解 · 播放 3704 次 · 覆盖 数据链路层 相关内容', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '33:50', 0, 25, '彭彭学编程', 'seed', '流量控制与可靠传输机制'),
  (432, '计算机网络', '数据链路层', '计算机网络强化专题-TCP可靠传输，流量控制与拥塞控制', 'Bilibili', 'https://www.bilibili.com/video/BV1tFeTzKE12', '就是氧气11 讲解 · 播放 2102 次 · 覆盖 数据链路层 相关内容', 'https://i1.hdslb.com/bfs/archive/197b26223e6d029c7060a6077bcefb1fde51c037.jpg', '46:1', 0, 43, '就是氧气11', 'seed', '流量控制与可靠传输机制'),
  (433, '计算机网络', '数据链路层', '30分钟搞定408计网MAC介质访问控制历年真题｜真题复盘｜小桐', 'Bilibili', 'https://www.bilibili.com/video/BV1Q9eEeEEc2', '图灵讲计组 讲解 · 播放 1985 次 · 覆盖 数据链路层 相关内容', 'https://i0.hdslb.com/bfs/archive/fa5bf0eb8e61a1c66e0d9d021a8d9ebcb63e6e89.jpg', '32:0', 0, 27, '图灵讲计组', 'seed', '介质访问控制'),
  (434, '计算机网络', '数据链路层', '4.08.IP数据报的概念和格式', 'Bilibili', 'https://www.bilibili.com/video/BV1UM41167sP', '彭彭学编程 讲解 · 播放 3198 次 · 覆盖 数据链路层 相关内容', 'https://i1.hdslb.com/bfs/archive/a37197aaa16de75204e65ec477447274ec4ac467.jpg', '33:38', 0, 25, '彭彭学编程', 'seed', '局域网'),
  (435, '计算机网络', '网络层', '第4章 网络层（背诵手册 音视频版）', 'Bilibili', 'https://www.bilibili.com/video/BV1xwNSeWEoH', '优质推荐 · 湖科大教书匠 制作 · 播放 11483 次 · 与 网络层 高度相关', 'https://i0.hdslb.com/bfs/archive/1e2c639522a523fc132383c5ec553b9ed1d544d5.jpg', '35:0', 0, 63, '湖科大教书匠', 'seed', '网络层的功能'),
  (436, '计算机网络', '网络层', '【计网计算题讲解集锦】单身狗！你过什么七夕！计算机网络计算题你都会了吗？', 'Bilibili', 'https://www.bilibili.com/video/BV18S42197eG', '里昂408 讲解 · 播放 21057 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/115b6bb5804a76cd3af3c2ecfc4959cc0868be47.png', '55:7', 0, 51, '里昂408', 'seed', '网络层的功能'),
  (437, '计算机网络', '网络层', '408 | 计网碎碎念之 [ 网络层 ]', 'Bilibili', 'https://www.bilibili.com/video/BV1QJqeYmEru', '困困尾 讲解 · 播放 514 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/a79335dd6c0ac2112bef28dcc1a990ce1cdfe62d.jpg', '43:44', 0, 45, '困困尾', 'seed', '网络层的功能'),
  (438, '计算机网络', '网络层', '计网冲刺-应用层专题(完结撒花)', 'Bilibili', 'https://www.bilibili.com/video/BV1LASNB8EVG', '就是氧气11 讲解 · 播放 5316 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/72cbae96823fdb701da176d768425e002fcb1a22.jpg', '42:0', 0, 27, '就是氧气11', 'seed', '网络层的功能'),
  (439, '计算机网络', '网络层', '【408计网】 网工学长带你分章节吃透历年真题 | 应用层', 'Bilibili', 'https://www.bilibili.com/video/BV11BWzzAEkd', '半幺郎 讲解 · 播放 5157 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/1afd219b826301728a7e50fe49309901d2eba271.jpg', '57:3', 0, 45, '半幺郎', 'seed', '网络层的功能'),
  (440, '计算机网络', '网络层', '【网络层】IPV4', 'Bilibili', 'https://www.bilibili.com/video/BV1vD4QzWEYi', '情敌贝多芬的心跳 讲解 · 播放 1839 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/5487d9593d5ff01a3be5a2e54dde966a7f2250b4.jpg', '42:18', 0, 53, '情敌贝多芬的心跳', 'seed', 'IPv4'),
  (441, '计算机网络', '网络层', '计算机网络复盘 网络层1（IPv4） 20241001', 'Bilibili', 'https://www.bilibili.com/video/BV1Rw4NecEez', '布偶小喵11408 讲解 · 播放 211 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/57cd152f71de1e7971c3cb8b070013223a1801c0.jpg', '40:4', 0, 47, '布偶小喵11408', 'seed', 'IPv4'),
  (442, '计算机网络', '网络层', '网络层2(取余法原理，ipv4地址分类)', 'Bilibili', 'https://www.bilibili.com/video/BV1bz4y1a7D8', 'YiJin_edu 讲解 · 播放 179 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/70ebfcec158b5473202ccaf046f1153d2c2876ce.jpg', '45:55', 0, 43, 'YiJin_edu', 'seed', 'IPv4'),
  (443, '计算机网络', '网络层', '第4章 网络层-4.2 IPv4地址-子网划分与子网掩码-子网掩码-计算机网络-复盘', 'Bilibili', 'https://www.bilibili.com/video/BV1ren2zMEf2', '必须好好读研 讲解 · 播放 150 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/7aed7bdb20866395cadcfb1d929d68e22280e7ac.jpg', '41:33', 0, 47, '必须好好读研', 'seed', 'IPv4'),
  (444, '计算机网络', '网络层', 'CCNA-EI-06-网络层-IPv4协议-子网划分', 'Bilibili', 'https://www.bilibili.com/video/BV19C4115788', '老久菜 讲解 · 播放 125 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/a43f20dccd15f337a86f849fc155a5e471ee1a33.jpg', '49:59', 0, 43, '老久菜', 'seed', 'IPv4'),
  (445, '计算机网络', '网络层', '计算机网络微课堂第047讲 IPv4地址概述（有字幕无背景音乐版）', 'Bilibili', 'https://www.bilibili.com/video/BV1dJ411R7dc', '优质推荐 · 湖科大教书匠 制作 · 播放 10578 次 · 与 网络层 高度相关', 'https://i2.hdslb.com/bfs/archive/357dcc6a05e2b325e699c196e37ae6abd435388f.jpg', '8:12', 0, 69, '湖科大教书匠', 'seed', 'IPv6'),
  (446, '计算机网络', '网络层', '4.22.IPv6的表示形式', 'Bilibili', 'https://www.bilibili.com/video/BV1n841157Zc', '彭彭学编程 讲解 · 播放 1040 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/19767e4dcbebb6cfaf22ca1382611ef7dae095c1.jpg', '5:26', 0, 25, '彭彭学编程', 'seed', 'IPv6'),
  (447, '计算机网络', '网络层', '4.23.IPv6地址类型和过渡策略', 'Bilibili', 'https://www.bilibili.com/video/BV1Nv4y1o7fV', '彭彭学编程 讲解 · 播放 969 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/19767e4dcbebb6cfaf22ca1382611ef7dae095c1.jpg', '7:4', 0, 25, '彭彭学编程', 'seed', 'IPv6'),
  (448, '计算机网络', '网络层', '计算机网络微课堂第047讲 IPv4地址概述（有字幕有背景音乐版）', 'Bilibili', 'https://www.bilibili.com/video/BV1oJ411R7AW', '湖科大教书匠 讲解 · 播放 5038 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/6d341ec591cf288c56d1c3b129d14b12b55e0530.jpg', '8:12', 0, 59, '湖科大教书匠', 'seed', 'IPv6'),
  (449, '计算机网络', '网络层', '计算机网络微课堂第047讲 IPv4地址概述（无字幕无背景音乐版）', 'Bilibili', 'https://www.bilibili.com/video/BV1dJ411R7Xf', '湖科大教书匠 讲解 · 播放 2188 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/21fbefd2d77a36081e84aa21279afd95a881ea97.jpg', '8:12', 0, 59, '湖科大教书匠', 'seed', 'IPv6'),
  (450, '计算机网络', '网络层', '计网冲刺-路由算法专题', 'Bilibili', 'https://www.bilibili.com/video/BV1ydUmBcETy', '就是氧气11 讲解 · 播放 3144 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/4f1e515048d6613a73023f09f0495b2fb90ade90.jpg', '35:39', 0, 27, '就是氧气11', 'seed', '路由算法与路由协议'),
  (451, '计算机网络', '网络层', '路由算法和路由选择协议（24年大题冷箭）', 'Bilibili', 'https://www.bilibili.com/video/BV1vzH5zBEYo', '22408练习生 讲解 · 播放 1401 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/8d693c1a5fa02e57654c38187e1e962470e1cb27.jpg', '35:24', 0, 25, '22408练习生', 'seed', '路由算法与路由协议'),
  (452, '计算机网络', '网络层', '计网冲刺-SDN、IP组播与移动IP', 'Bilibili', 'https://www.bilibili.com/video/BV18SSGB3Ewz', '就是氧气11 讲解 · 播放 3179 次 · 覆盖 网络层 相关内容', 'https://i1.hdslb.com/bfs/archive/ccad69cc2435ee7afbd384bfc2f59569254c2ab4.jpg', '30:41', 0, 27, '就是氧气11', 'seed', 'IP多播'),
  (453, '计算机网络', '网络层', '计网冲刺-物理层', 'Bilibili', 'https://www.bilibili.com/video/BV1d8yuBfE52', '就是氧气11 讲解 · 播放 2120 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/0aa69c1f670c318a2e62b047379df82855411d53.jpg', '31:48', 0, 27, '就是氧气11', 'seed', 'IP多播'),
  (454, '计算机网络', '网络层', 'IPV6；IP多播；移动IP（速通）', 'Bilibili', 'https://www.bilibili.com/video/BV1bbx4zzEBv', '22408练习生 讲解 · 播放 1285 次 · 覆盖 网络层 相关内容', 'https://i2.hdslb.com/bfs/archive/3d3c4b5ef60ba0624d98cf89139a61d944ac2551.jpg', '30:21', 0, 25, '22408练习生', 'seed', '移动IP'),
  (455, '计算机网络', '网络层', '23贵州大学电子信息考研（贵大电子信息）834电子技术基础/控制工程/新一代电子信息技术（含量子技术）通信工程（含宽带网络、移动通信）集成电路工程/23考研指导', 'Bilibili', 'https://www.bilibili.com/video/BV1QZ4y127DU', '研谌考研专业课 · 播放 2861 次 · 与 网络层 相关', 'https://i0.hdslb.com/bfs/archive/8608332dd6e9c41f92a2c44c76e1a605248f866e.jpg', '55:28', 0, 27, '研谌考研专业课', 'seed', '移动IP'),
  (456, '计算机网络', '网络层', '5.08.TCP连接：三次握手建立连接', 'Bilibili', 'https://www.bilibili.com/video/BV1XR4y1y72o', '彭彭学编程 讲解 · 播放 1738 次 · 覆盖 网络层 相关内容', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '33:35', 0, 25, '彭彭学编程', 'seed', '网络层设备'),
  (457, '计算机网络', '传输层', '计算机网络串讲-传输层', 'Bilibili', 'https://www.bilibili.com/video/BV1A24y117CM', '优质推荐 · Beokayy_ 制作 · 播放 51812 次 · 与 传输层 高度相关', 'https://i1.hdslb.com/bfs/archive/25256a0252283fbf65589fedaaec9df6d1ed0511.jpg', '49:1', 0, 77, 'Beokayy_', 'seed', '传输层提供的服务'),
  (458, '计算机网络', '传输层', '408计算机网络传输层复习', 'Bilibili', 'https://www.bilibili.com/video/BV1Tp1KYHEz2', '栾灰灰向前看 讲解 · 播放 5881 次 · 覆盖 传输层 相关内容', 'https://i2.hdslb.com/bfs/archive/4dce424b9a60498beae3e9de3c2a0c58f6081123.jpg', '33:40', 0, 59, '栾灰灰向前看', 'seed', '传输层提供的服务'),
  (459, '计算机网络', '传输层', '5.10.TCP可靠传输', 'Bilibili', 'https://www.bilibili.com/video/BV1G841157gd', '彭彭学编程 讲解 · 播放 1662 次 · 覆盖 传输层 相关内容', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '35:44', 0, 25, '彭彭学编程', 'seed', '传输层提供的服务'),
  (460, '计算机网络', '传输层', '5.07.TCP报文段首部格式', 'Bilibili', 'https://www.bilibili.com/video/BV1ve411N7k5', '彭彭学编程 讲解 · 播放 1541 次 · 覆盖 传输层 相关内容', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '40:49', 0, 25, '彭彭学编程', 'seed', '传输层提供的服务'),
  (461, '计算机网络', '传输层', '21网络层提供的两种服务、尽最大努力交付、网络层不需要实现可靠性传输', 'Bilibili', 'https://www.bilibili.com/video/BV1ki421o7Gc', '常cc_ · 播放 308 次 · 与 传输层 相关', 'https://i0.hdslb.com/bfs/archive/26d66c9d4803cd21bf78c178333a4956bee45474.jpg', '30:26', 0, 15, '常cc_', 'seed', '传输层提供的服务'),
  (462, '计算机网络', '传输层', '计算机网络强化专题-传输层与UDP协议', 'Bilibili', 'https://www.bilibili.com/video/BV1V5YszdEqS', '就是氧气11 讲解 · 播放 1580 次 · 覆盖 传输层 相关内容', 'https://i0.hdslb.com/bfs/archive/90e49b637c3b35d8a1ce74f4fcf82e655f3d1e4b.jpg', '34:39', 0, 59, '就是氧气11', 'seed', 'UDP'),
  (463, '计算机网络', '传输层', '计算机网络传输层', 'Bilibili', 'https://www.bilibili.com/video/BV1y8ypYoE2D', '布偶小喵11408 讲解 · 播放 80 次 · 覆盖 传输层 相关内容', 'https://i2.hdslb.com/bfs/archive/500149447e627dc5456d9685bca390be2cabe09a.jpg', '41:59', 0, 47, '布偶小喵11408', 'seed', 'UDP'),
  (464, '计算机网络', '传输层', '网络中传输层的TCP可靠和UDP不可靠?', 'Bilibili', 'https://www.bilibili.com/video/BV1tA411C7cq', '超有趣网络 讲解 · 播放 641 次 · 覆盖 传输层 相关内容', 'https://i0.hdslb.com/bfs/archive/d4f057a1048adb422df82d0760fcc18741f7861c.jpg', '51:41', 0, 43, '超有趣网络', 'seed', 'UDP'),
  (465, '计算机网络', '传输层', '[32]--08-7 传输层协议TCP和UDP', 'Bilibili', 'https://www.bilibili.com/video/BV12Vs3ecEpq', '像风一张 · 播放 99 次 · 与 传输层 相关', 'https://i0.hdslb.com/bfs/archive/095049a0dcf9a4c28075a61390f60356d4a5dd0e.jpg', '56:19', 0, 43, '像风一张', 'seed', 'UDP'),
  (466, '计算机网络', '传输层', '03-UDP以太网传输回环测试实验实操', 'Bilibili', 'https://www.bilibili.com/video/BV12pGDeVE4b', '迷途女孩playingsz · 播放 444 次 · 与 传输层 相关', 'https://i1.hdslb.com/bfs/archive/c02e3841cb779f7211a13b13a02db8bd290ee7ed.jpg', '32:22', 0, 15, '迷途女孩playingsz', 'seed', 'UDP'),
  (467, '计算机网络', '应用层', '6.11.发邮件协议：SMTP', 'Bilibili', 'https://www.bilibili.com/video/BV1fG4y1G7Uc', '彭彭学编程 讲解 · 播放 5310 次 · 覆盖 应用层 相关内容', 'https://i0.hdslb.com/bfs/archive/9765e8159a009e80c3b52da5a32f54a6840eebcf.jpg', '38:37', 0, 25, '彭彭学编程', 'seed', '网络应用模型'),
  (468, '计算机网络', '应用层', '计网强化课第六章，应用层', 'Bilibili', 'https://www.bilibili.com/video/BV1westzcE3h', '李哥考研 讲解 · 播放 1476 次 · 覆盖 应用层 相关内容', 'https://i2.hdslb.com/bfs/archive/8152cdb80bc39f670c2445c64c1a64cb3db43e81.jpg', '33:38', 0, 53, '李哥考研', 'seed', '网络应用模型'),
  (469, '计算机网络', '应用层', '计网强化课第二节，物理层全解析', 'Bilibili', 'https://www.bilibili.com/video/BV1s24DzME2W', '李哥考研 讲解 · 播放 1541 次 · 覆盖 应用层 相关内容', 'https://i2.hdslb.com/bfs/archive/a2f67849c0c024241eda37c69a3b0c9b470973ec.jpg', '54:8', 0, 25, '李哥考研', 'seed', '网络应用模型'),
  (470, '计算机网络', '应用层', '跟我学计网之挑战10天学完-第6天-1-应用层的东西简单多了', 'Bilibili', 'https://www.bilibili.com/video/BV1WW4y1G73S', '白告月当空照 · 播放 72 次 · 与 应用层 相关', 'https://i0.hdslb.com/bfs/archive/d47903728947435461733b83b4aec9724a457de4.jpg', '53:25', 0, 38, '白告月当空照', 'seed', '网络应用模型'),
  (471, '计算机网络', '应用层', '配置特殊域名dns服务、ansible获取FQDN、ssh免密、防火墙开放端口、NTP时间服务', 'Bilibili', 'https://www.bilibili.com/video/BV1DE4m1R7BG', '根某人L · 播放 2164 次 · 与 应用层 相关', 'https://i2.hdslb.com/bfs/archive/4c7a9325c08d608f567176cb5253a2cee1b729a9.jpg', '37:44', 0, 25, '根某人L', 'seed', 'DNS域名系统'),
  (472, '计算机网络', '应用层', '项目08 配置与管理DNS服务器', 'Bilibili', 'https://www.bilibili.com/video/BV12Hatz9Esa', 'yuanjinsong · 播放 479 次 · 与 应用层 相关', 'https://i2.hdslb.com/bfs/archive/ba1c263db54d611aceec0702de51c916f5ce1874.jpg', '34:38', 0, 19, 'yuanjinsong', 'seed', 'DNS域名系统'),
  (473, '计算机网络', '应用层', '2.Web应用&amp;备案产权&amp;Whois反查&amp;域名枚举&amp;DNS记录&amp;证书特征&amp;相似查询', 'Bilibili', 'https://www.bilibili.com/video/BV1sw5LzMETb', '烧烤老师傅 · 播放 331 次 · 与 应用层 相关', 'https://i2.hdslb.com/bfs/archive/37ab2faf0b652241b4b706c2d9a0a635bf086d06.jpg', '32:34', 0, 15, '烧烤老师傅', 'seed', 'DNS域名系统'),
  (474, '计算机网络', '应用层', '6.1 域名系统DNS-2', 'Bilibili', 'https://www.bilibili.com/video/BV1DHjZz3Efd', '又活了一周同学 · 播放 59 次 · 与 应用层 相关', 'https://i2.hdslb.com/bfs/archive/587c8d0a3aaa336e8db36c95cbad74f5cab7cc8a.jpg', '30:22', 0, 15, '又活了一周同学', 'seed', 'DNS域名系统'),
  (475, '计算机网络', '应用层', '17章.dns域名解析服务', 'Bilibili', 'https://www.bilibili.com/video/BV1tm4y1z7RB', '熊猫小AA · 播放 80 次 · 与 应用层 相关', 'https://i0.hdslb.com/bfs/archive/ade773cf7d082f5d3edbf66f162ecfb0552abac4.jpg', '40:12', 0, 10, '熊猫小AA', 'seed', 'DNS域名系统'),
  (476, '计算机网络', '应用层', '计算机网络强化专题-传输层与应用层综合大题', 'Bilibili', 'https://www.bilibili.com/video/BV1H9etzSEJy', '就是氧气11 讲解 · 播放 2202 次 · 覆盖 应用层 相关内容', 'https://i0.hdslb.com/bfs/archive/bf3473306281e02120b75a591a2d2b5437ca3d0b.jpg', '39:18', 0, 59, '就是氧气11', 'seed', '文件传输协议'),
  (477, '计算机网络', '应用层', '河北工业大学电气工程生物医学工程能源动力电子信息840/841考研如何联系心仪的导师', 'Bilibili', 'https://www.bilibili.com/video/BV1Q5411N7Vs', '河工电气小青年 · 播放 1949 次 · 与 应用层 相关', 'https://i1.hdslb.com/bfs/archive/9751a68240a149b9e7ce18bddfaa6a5e6d778fa4.jpg', '40:52', 0, 27, '河工电气小青年', 'seed', '电子邮件'),
  (478, '计算机组成原理', '输入输出系统', '计算机考研408统考机组IO章节大题强化', 'Bilibili', 'https://www.bilibili.com/video/BV12z4y1J78H', '枕套1 讲解 · 播放 8959 次 · 覆盖 输入输出系统 相关内容', 'https://i1.hdslb.com/bfs/archive/4a87ccef913aba6dba4ee610989d8a3c686118c7.jpg', '56:0', 0, 55, '枕套1', 'seed', 'IO系统概述'),
  (479, '计算机组成原理', '输入输出系统', '操作系统强化专题-IO管理', 'Bilibili', 'https://www.bilibili.com/video/BV13mtMzhEb7', '就是氧气11 · 播放 3184 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/eaa2fc08f050be3e1689d25d4483550bf12a5274.jpg', '30:52', 0, 27, '就是氧气11', 'seed', 'IO系统概述'),
  (480, '计算机组成原理', '输入输出系统', '计组：输入输出IO真题大题', 'Bilibili', 'https://www.bilibili.com/video/BV1h715BTET6', '22408练习生 · 播放 974 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/19a44b4bd8dafbc53fb99179f8d1f50adf04418c.jpg', '37:15', 0, 25, '22408练习生', 'seed', 'IO系统概述'),
  (481, '计算机组成原理', '输入输出系统', '408复盘-计组-IO、总线、多处理器', 'Bilibili', 'https://www.bilibili.com/video/BV1UjUkBHE2y', '22408小手子 · 播放 782 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/f284035c52c8365670f4dc3287742e793ac17276.jpg', '31:58', 0, 27, '22408小手子', 'seed', 'IO系统概述'),
  (482, '计算机组成原理', '输入输出系统', '计组第七章IO大题真题复盘', 'Bilibili', 'https://www.bilibili.com/video/BV12dpXzNERT', '慢宋宋宋宋 · 播放 665 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/acb09e73d654fcd266d365362e1e1648808c08ee.jpg', '48:6', 0, 15, '慢宋宋宋宋', 'seed', 'IO系统概述'),
  (483, '计算机组成原理', '输入输出系统', '27操作系统基础-IO系统层次结构', 'Bilibili', 'https://www.bilibili.com/video/BV1LwdHBoES6', '就是氧气11 · 播放 552 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/6db28ae4270e65a6dc93d44897b3a5cc16666b8a.jpg', '34:38', 0, 17, '就是氧气11', 'seed', 'IO控制方式'),
  (484, '计算机组成原理', '输入输出系统', '27组成原理基础-中断IO方式', 'Bilibili', 'https://www.bilibili.com/video/BV1NfAMzdEJe', '就是氧气11 · 播放 504 次 · 与 输入输出系统 相关', 'https://i2.hdslb.com/bfs/archive/977444df866d0cfac1b23516bf523725d4e878bd.jpg', '34:3', 0, 17, '就是氧气11', 'seed', 'IO控制方式'),
  (485, '计算机组成原理', '输入输出系统', '《开源巨全408导图》操作系统：IO', 'Bilibili', 'https://www.bilibili.com/video/BV1j9XyYFEvc', '408小牛 · 播放 271 次 · 与 输入输出系统 相关', 'https://i1.hdslb.com/bfs/archive/ccec28b0a39963f7ddf03cfd911c77d35e60d432.jpg', '50:25', 0, 17, '408小牛', 'seed', 'IO控制方式'),
  (486, '操作系统', '输入输出管理', '【复习备忘】操作系统—I/O管理', 'Bilibili', 'https://www.bilibili.com/video/BV1xo4y1k78k', '啊我有兔子牙 · 播放 4677 次 · 与 输入输出管理 相关', 'https://i0.hdslb.com/bfs/archive/03bd0f3039a1d9af6305a0540c321c5a25972673.jpg', '33:47', 0, 41, '啊我有兔子牙', 'seed', 'IO管理概述'),
  (487, '操作系统', '输入输出管理', '408IO管理复习（co和os串讲）', 'Bilibili', 'https://www.bilibili.com/video/BV1MtSvYLEtM', '栾灰灰向前看 · 播放 13116 次 · 与 输入输出管理 相关', 'https://i0.hdslb.com/bfs/archive/930a4b9747c50426ff96e26a00b41cb0ac60f343.jpg', '38:55', 0, 37, '栾灰灰向前看', 'seed', 'IO管理概述');

-- ------------------------------------------------------------
-- AUTO_INCREMENT values
-- ------------------------------------------------------------
ALTER TABLE `answer_record` AUTO_INCREMENT = 23;
ALTER TABLE `conversation` AUTO_INCREMENT = 14;
ALTER TABLE `conversation_message` AUTO_INCREMENT = 29;
ALTER TABLE `forum_category` AUTO_INCREMENT = 7;
ALTER TABLE `forum_checkin` AUTO_INCREMENT = 2;
ALTER TABLE `forum_comment` AUTO_INCREMENT = 2;
ALTER TABLE `forum_like` AUTO_INCREMENT = 3;
ALTER TABLE `forum_post` AUTO_INCREMENT = 3;
ALTER TABLE `knowledge_mastery` AUTO_INCREMENT = 39;
ALTER TABLE `knowledge_point` AUTO_INCREMENT = 350;
ALTER TABLE `mistake` AUTO_INCREMENT = 15;
ALTER TABLE `question` AUTO_INCREMENT = 319;
ALTER TABLE `question_generation_session` AUTO_INCREMENT = 75;
ALTER TABLE `report` AUTO_INCREMENT = 8;
ALTER TABLE `subject` AUTO_INCREMENT = 5;
ALTER TABLE `user` AUTO_INCREMENT = 2;
ALTER TABLE `user_memory` AUTO_INCREMENT = 11;
ALTER TABLE `user_profile` AUTO_INCREMENT = 2;
ALTER TABLE `video_crawl_log` AUTO_INCREMENT = 439;
ALTER TABLE `video_resource` AUTO_INCREMENT = 488;

SET FOREIGN_KEY_CHECKS = 1;

-- Row count summary
-- answer_record: 22
-- conversation: 13
-- conversation_message: 28
-- favorite_question: 0
-- forum_category: 6
-- forum_checkin: 1
-- forum_collect: 0
-- forum_comment: 1
-- forum_like: 2
-- forum_post: 2
-- knowledge_document: 0
-- knowledge_mastery: 38
-- knowledge_point: 349
-- mistake: 13
-- question: 312
-- question_generation_session: 74
-- report: 7
-- schema_migrations: 6
-- subject: 4
-- user: 1
-- user_daily_activity: 0
-- user_memory: 10
-- user_pending_recommendation: 0
-- user_profile: 1
-- video_crawl_log: 438
-- video_resource: 487
