-- Turing 408 Agent MySQL schema.
-- 开发版后端默认使用 SQLAlchemy 自动建表；部署到 MySQL 时可用本文件作为审核版建表参考。

CREATE DATABASE IF NOT EXISTS yantu408 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yantu408;

CREATE TABLE IF NOT EXISTS user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(128) NOT NULL UNIQUE,
  username VARCHAR(64) NOT NULL UNIQUE,
  nickname VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  avatar_url VARCHAR(255) DEFAULT '',
  status VARCHAR(32) DEFAULT 'active',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_point (
  id INT PRIMARY KEY AUTO_INCREMENT,
  subject VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  parent_name VARCHAR(128) DEFAULT '',
  level INT DEFAULT 1,
  content TEXT,
  common_mistakes TEXT,
  keywords TEXT,
  is_high_frequency TINYINT DEFAULT 0,
  INDEX idx_kp_subject(subject),
  INDEX idx_kp_name(name)
);

CREATE TABLE IF NOT EXISTS question_generation_session (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  generation_mode VARCHAR(64),
  recommend_mode VARCHAR(64) DEFAULT '',
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  difficulty VARCHAR(32),
  question_type VARCHAR(32),
  question_count INT DEFAULT 3,
  reason TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question (
  id INT PRIMARY KEY AUTO_INCREMENT,
  session_id INT NULL,
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  difficulty VARCHAR(32),
  question_type VARCHAR(32),
  question_text TEXT NOT NULL,
  options_json TEXT,
  standard_answer VARCHAR(64),
  explanation TEXT,
  hints_json TEXT,
  recommend_reason TEXT,
  source VARCHAR(64) DEFAULT 'agent'
);

CREATE TABLE IF NOT EXISTS answer_record (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  question_id INT NOT NULL,
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  user_answer VARCHAR(128),
  standard_answer VARCHAR(128),
  is_correct TINYINT DEFAULT 0,
  feedback TEXT,
  mastery_feedback VARCHAR(32),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_mastery (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  final_status VARCHAR(32) DEFAULT '未学',
  total_answer_count INT DEFAULT 0,
  correct_count INT DEFAULT 0,
  wrong_count INT DEFAULT 0,
  unfamiliar_count INT DEFAULT 0,
  unknown_count INT DEFAULT 0,
  mastered_count INT DEFAULT 0,
  ocr_mistake_count INT DEFAULT 0,
  qa_count INT DEFAULT 0,
  forum_count INT DEFAULT 0,
  user_mark_status VARCHAR(32) DEFAULT '',
  weak_score FLOAT DEFAULT 0,
  continuous_wrong_count INT DEFAULT 0,
  last_answer_time DATETIME NULL,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mistake (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  answer_record_id INT NULL,
  question_id INT NULL,
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  error_type VARCHAR(128),
  error_reason TEXT,
  suggestion TEXT,
  input_type VARCHAR(64),
  status VARCHAR(32) DEFAULT 'active',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_memory (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  memory_type VARCHAR(64),
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  content TEXT,
  evidence TEXT,
  status VARCHAR(32) DEFAULT 'active',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forum_post (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  category VARCHAR(64),
  subject VARCHAR(64),
  knowledge_point VARCHAR(128),
  title VARCHAR(180),
  content TEXT,
  like_count INT DEFAULT 0,
  collect_count INT DEFAULT 0,
  comment_count INT DEFAULT 0,
  is_top TINYINT DEFAULT 0,
  status VARCHAR(32) DEFAULT 'normal',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(128),
  summary TEXT,
  weak_points TEXT,
  main_error_type TEXT,
  qa_focus TEXT,
  forum_focus TEXT,
  video_suggestion TEXT,
  plan_json TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
