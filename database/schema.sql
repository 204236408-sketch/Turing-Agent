-- Turing 408 Agent MySQL schema 优化完整版
-- 兼容 MySQL8.0+，支持ENUM、CHECK、生成列
CREATE DATABASE IF NOT EXISTS yantu408 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yantu408;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ====================== 1. 用户表 ======================
CREATE TABLE IF NOT EXISTS `user` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
  `email` VARCHAR(128) NOT NULL COMMENT '登录邮箱',
  `username` VARCHAR(64) NOT NULL COMMENT '登录用户名',
  `nickname` VARCHAR(64) NOT NULL DEFAULT '408 同学' COMMENT '用户昵称',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `avatar_url` VARCHAR(255) DEFAULT '' COMMENT '头像链接',
  `status` ENUM('active','frozen','banned') DEFAULT 'active' COMMENT '账号状态：正常/冻结/封禁',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '软删除 1删除 0正常',
  `delete_time` DATETIME NULL DEFAULT NULL COMMENT '删除时间',
  `create_ip` VARCHAR(64) DEFAULT '' COMMENT '注册IP',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_user_email` (`email`),
  UNIQUE KEY `uk_user_username` (`username`),
  INDEX `idx_user_status` (`status`),
  INDEX `idx_user_isdel` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户主表';

-- ====================== 2. 用户学习资料表 ======================
CREATE TABLE IF NOT EXISTS `user_profile` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '资料主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '外键关联user.id',
  `target_exam` VARCHAR(64) DEFAULT '考研 408' COMMENT '目标考试',
  `target_date` VARCHAR(32) DEFAULT '2026-12-19' COMMENT '考试日期',
  `target_date_val` DATE GENERATED ALWAYS AS (STR_TO_DATE(`target`, '%Y-%m-%d')) STORED COMMENT '日期计算生成列',
  `daily_minutes` INT DEFAULT 90 COMMENT '每日计划学习分钟',
  `learning_stage` ENUM('基础','强化','冲刺','复试') DEFAULT '强化' COMMENT '学习阶段',
  `long_profile` TEXT DEFAULT '' COMMENT '个人学习简介',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_user_profile_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户学习资料表';

-- ====================== 3. 科目基础表 ======================
CREATE TABLE IF NOT EXISTS `subject` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '科目主键',
  `name` VARCHAR(64) NOT NULL COMMENT '科目全称（固定4科）',
  `description` TEXT DEFAULT '' COMMENT '科目描述',
  `sort_order` INT DEFAULT 0 COMMENT '展示排序值',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '软删除',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_subject_name` (`name`),
  INDEX `idx_subject_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='408四科基础表';

-- ====================== 4. 知识点表（核心优化） ======================
CREATE TABLE IF NOT EXISTS `knowledge_point` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '知识点主键',
  `subject_id` INT UNSIGNED NOT NULL COMMENT '关联科目ID',
  `subject` VARCHAR(64) NOT NULL COMMENT '科目名称（兼容旧数据）',
  `parent_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '父知识点ID，支持层级递归',
  `parent_name` VARCHAR(128) DEFAULT '' COMMENT '父级知识点名称',
  `name` VARCHAR(128) NOT NULL COMMENT '知识点一级大节',
  `section` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '小节名称',
  `level` INT DEFAULT 1 COMMENT '层级深度',
  `content` TEXT COMMENT '核心考点内容',
  `common_mistakes` TEXT COMMENT '常见易错点',
  `keywords` TEXT COMMENT '英文逗号分隔关键词',
  `is_high_frequency` TINYINT(1) DEFAULT 0 COMMENT '是否高频 1是0否',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '软删除',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY (`parent_id`) REFERENCES `knowledge_point`(`id`) ON DELETE SET NULL,
  UNIQUE KEY `uk_kp_sub_name_sec` (`subject`, `name`, `section`),
  INDEX `idx_kp_subject_id` (`subject_id`),
  INDEX `idx_kp_parent_id` (`parent_id`),
  INDEX `idx_kp_highfreq` (`is_high_frequency`),
  INDEX `idx_kp_del` (`is_deleted`),
  FULLTEXT INDEX `ft_kp_content` (`content`,`common_mistakes`,`keywords`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='408知识点表';

-- ====================== 5. AI出题会话表 ======================
CREATE TABLE IF NOT EXISTS `question_generation_session` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '会话主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '操作用户ID',
  `generation_mode` VARCHAR(32) DEFAULT 'manual' COMMENT '出题模式',
  `recommend_mode` VARCHAR(64) DEFAULT '' COMMENT '推荐模式',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '知识点',
  `difficulty` VARCHAR(32) DEFAULT '中等' COMMENT '难度',
  `question_type` VARCHAR(32) DEFAULT '选择题' COMMENT '题型',
  `question_count` INT DEFAULT 3 COMMENT '生成题目数量',
  `reason` TEXT COMMENT '出题理由',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_session_uid` (`user_id`),
  INDEX `idx_session_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_session_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI出题会话记录表';

-- ====================== 6. 题目题库表 ======================
CREATE TABLE IF NOT EXISTS `question` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '题目主键',
  `session_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '所属出题会话ID',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '对应知识点',
  `difficulty` VARCHAR(32) DEFAULT '中等' COMMENT '难度',
  `question_type` VARCHAR(32) DEFAULT '选择题' COMMENT '大题型',
  `variant_type` ENUM('choice','essay') DEFAULT 'choice' COMMENT '细分类型',
  `question_text` TEXT NOT NULL COMMENT '题干',
  `options_json` TEXT DEFAULT '[]' COMMENT '选项JSON数组',
  `sub_questions_json` TEXT DEFAULT '[]' COMMENT '综合题子问题数组',
  `standard_answer` VARCHAR(64) DEFAULT '' COMMENT '标准答案',
  `explanation` TEXT DEFAULT '' COMMENT '题目解析',
  `hints_json` TEXT DEFAULT '[]' COMMENT '三层提示数组',
  `recommend_reason` TEXT DEFAULT '' COMMENT '推荐理由',
  `source` ENUM('seed','agent_mock') DEFAULT 'agent_mock' COMMENT '数据来源',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`session_id`) REFERENCES `question_generation_session`(`id`) ON DELETE SET NULL,
  INDEX `idx_q_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_q_session` (`session_id`),
  INDEX `idx_q_ctime` (`create_time`),
  INDEX `idx_q_del` (`is_deleted`),
  FULLTEXT INDEX `ft_q_text` (`question_text`,`explanation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='408题库表';

-- ====================== 7. 用户收藏题目 ======================
CREATE TABLE IF NOT EXISTS `favorite_question` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '收藏主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `question_id` INT UNSIGNED NOT NULL COMMENT '题目ID',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '取消收藏等价软删除',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`question_id`) REFERENCES `question`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_fav_uid_qid` (`user_id`, `question_id`),
  INDEX `idx_fav_uid` (`user_id`),
  INDEX `idx_fav_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏题目';

-- ====================== 8. 答题记录表 ======================
CREATE TABLE IF NOT EXISTS `answer_record` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '答题记录主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `question_id` INT UNSIGNED NOT NULL COMMENT '题目ID',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '知识点',
  `user_answer` VARCHAR(128) DEFAULT '' COMMENT '用户作答',
  `standard_answer` VARCHAR(128) DEFAULT '' COMMENT '标准答案',
  `is_correct` TINYINT(1) DEFAULT 0 COMMENT '是否答对 1是0否',
  `feedback` TEXT DEFAULT '' COMMENT '作答反馈',
  `mastery_feedback` VARCHAR(32) DEFAULT '' COMMENT '掌握程度标签',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '答题时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`question_id`) REFERENCES `question`(`id`) ON DELETE CASCADE,
  INDEX `idx_ans_uid` (`user_id`),
  INDEX `idx_ans_uid_ctime` (`user_id`,`create_time`),
  INDEX `idx_ans_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_ans_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户答题记录';

-- ====================== 9. 知识点掌握度 ======================
CREATE TABLE IF NOT EXISTS `knowledge_mastery` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '掌握度主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '知识点',
  `final_status` VARCHAR(32) DEFAULT '未学' COMMENT '最终掌握标签（未学/薄弱点/不会/不熟/掌握）',
  `total_answer_count` INT DEFAULT 0 COMMENT '总答题次数',
  `correct_count` INT DEFAULT 0 COMMENT '答对次数',
  `wrong_count` INT DEFAULT 0 COMMENT '答错次数',
  `unfamiliar_count` INT DEFAULT 0 COMMENT '生疏标记次数',
  `unknown_count` INT DEFAULT 0 COMMENT '完全不会次数',
  `mastered_count` INT DEFAULT 0 COMMENT '熟练掌握次数',
  `ocr_mistake_count` INT DEFAULT 0 COMMENT '手写识别错误次数',
  `qa_count` INT DEFAULT 0 COMMENT '问答咨询次数',
  `forum_count` INT DEFAULT 0 COMMENT '论坛提问次数',
  `user_mark_status` VARCHAR(32) DEFAULT '' COMMENT '用户手动标记状态',
  `weak_score` FLOAT DEFAULT 0 COMMENT '薄弱分值，越大越薄弱',
  `continuous_wrong_count` INT DEFAULT 0 COMMENT '连续答错次数',
  `last_answer_time` DATETIME NULL COMMENT '最近一次答题时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_mastery_uid_sub_kp` (`user_id`, `subject`, `knowledge_point`),
  INDEX `idx_mastery_uid` (`user_id`),
  INDEX `idx_mastery_weak` (`weak_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户知识点掌握统计表';

-- ====================== 10. 错题本 ======================
CREATE TABLE IF NOT EXISTS `mistake` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '错题主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `answer_record_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '关联答题记录ID',
  `question_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '关联题目ID',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '知识点',
  `error_type` VARCHAR(128) DEFAULT '' COMMENT '错误类型',
  `error_reason` TEXT DEFAULT '' COMMENT '错误原因',
  `suggestion` TEXT DEFAULT '' COMMENT '改进建议',
  `input_type` ENUM('系统出题','手动录入') DEFAULT '系统出题' COMMENT '题目来源',
  `status` ENUM('active','reviewed','archived') DEFAULT 'active' COMMENT '错题状态',
  `is_reviewed` TINYINT(1) DEFAULT 0 COMMENT '是否复习完成',
  `review_time` DATETIME NULL DEFAULT NULL COMMENT '复习时间',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`answer_record_id`) REFERENCES `answer_record`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`question_id`) REFERENCES `question`(`id`) ON DELETE SET NULL,
  INDEX `idx_mistake_uid` (`user_id`),
  INDEX `idx_mistake_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_mistake_review` (`is_reviewed`),
  INDEX `idx_mistake_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4_unicode_ci COMMENT='用户错题本';

-- ====================== 11. 用户记忆薄弱点 ======================
CREATE TABLE IF NOT EXISTS `user_memory` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记忆主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `memory_type` ENUM('weak_point','recite') DEFAULT 'weak_point' COMMENT '记忆类型',
  `subject` VARCHAR(64) COMMENT '科目',
  `knowledge_point` VARCHAR(128) COMMENT '知识点',
  `content` TEXT NOT NULL COMMENT '记忆内容',
  `evidence` TEXT DEFAULT '' COMMENT '生成依据',
  `status` ENUM('active','expire') DEFAULT 'active' COMMENT '状态',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_memory_uid` (`user_id`),
  INDEX `idx_memory_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户薄弱点记忆库';

-- ====================== 12. 问答会话 ======================
CREATE TABLE IF NOT EXISTS `conversation` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '对话主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `title` VARCHAR(128) DEFAULT '408 问答' COMMENT '会话标题',
  `summary` TEXT DEFAULT '' COMMENT '会话总结',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_conv_uid` (`user_id`),
  INDEX `idx_conv_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI问答会话';

-- ====================== 13. 会话消息 ======================
CREATE TABLE IF NOT EXISTS `conversation_message` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '消息主键',
  `conversation_id` INT UNSIGNED NOT NULL COMMENT '所属会话ID',
  `role` ENUM('user','assistant') NOT NULL COMMENT '角色',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
  FOREIGN KEY (`conversation_id`) REFERENCES `conversation`(`id`) ON DELETE CASCADE,
  INDEX `idx_msg_conv` (`conversation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答对话消息';

-- ====================== 14. 论坛分类 ======================
CREATE TABLE IF NOT EXISTS `forum_category` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '分类主键',
  `name` VARCHAR(64) NOT NULL COMMENT '分类名称',
  `description` TEXT DEFAULT '' COMMENT '分类说明',
  `sort_order` INT DEFAULT 0 COMMENT '排序值',
  `is_deleted` TINYINT(1) DEFAULT 0,
  UNIQUE KEY `uk_forum_cat_name` (`name`),
  INDEX `idx_cat_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论坛板块分类';

-- ====================== 15. 论坛主帖 ======================
CREATE TABLE IF NOT EXISTS `forum_post` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '帖子主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '发帖用户ID',
  `category` VARCHAR(64) COMMENT '板块分类名',
  `subject` VARCHAR(64) COMMENT '关联408科目',
  `knowledge_point` VARCHAR(128) DEFAULT '' COMMENT '关联知识点',
  `title` VARCHAR(180) NOT NULL COMMENT '帖子标题',
  `content` TEXT NOT NULL COMMENT '帖子正文',
  `like_count` INT DEFAULT 0 COMMENT '点赞数',
  `collect_count` INT DEFAULT 0 COMMENT '收藏数',
  `comment_count` INT DEFAULT 0 COMMENT '评论数',
  `is_top` TINYINT(1) DEFAULT 0 COMMENT '是否置顶 1是0否',
  `status` ENUM('normal','locked','hidden') DEFAULT 'normal' COMMENT '帖子状态',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_ip` VARCHAR(64) DEFAULT '' COMMENT '发帖IP',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发帖时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_post_uid` (`user_id`),
  INDEX `idx_post_cat` (`category`),
  INDEX `idx_post_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_post_top` (`is_top`),
  INDEX `idx_post_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论坛主帖';

-- ====================== 16. 论坛评论 ======================
CREATE TABLE IF NOT EXISTS `forum_comment` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '评论主键',
  `post_id` INT UNSIGNED NOT NULL COMMENT '所属帖子ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '评论用户ID',
  `parent_id` INT UNSIGNED NULL DEFAULT NULL COMMENT '楼中楼父评论ID',
  `content` TEXT NOT NULL COMMENT '评论内容',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
  FOREIGN KEY (`post_id`) REFERENCES `forum_post`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`parent_id`) REFERENCES `forum_comment`(`id`) ON DELETE SET NULL,
  INDEX `idx_comment_post` (`post_id`),
  INDEX `idx_comment_parent` (`parent_id`),
  INDEX `idx_comment_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论坛帖子评论';

-- ====================== 17. 论坛点赞 ======================
CREATE TABLE IF NOT EXISTS `forum_like` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '点赞主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '点赞用户',
  `target_type` ENUM('post','comment') NOT NULL COMMENT '点赞对象',
  `target_id` INT UNSIGNED NOT NULL COMMENT '帖子/评论ID',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_like_uid_target` (`user_id`, `target_type`, `target_id`),
  INDEX `idx_like_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论坛点赞记录';

-- ====================== 18. 论坛收藏 ======================
CREATE TABLE IF NOT EXISTS `forum_collect` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '收藏主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '收藏用户',
  `post_id` INT UNSIGNED NOT NULL COMMENT '收藏帖子ID',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`post_id`) REFERENCES `forum_post`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_collect_uid_pid` (`user_id`, `post_id`),
  INDEX `idx_collect_uid` (`user_id`),
  INDEX `idx_collect_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论坛帖子收藏';

-- ====================== 19. 论坛签到 ======================
CREATE TABLE IF NOT EXISTS `forum_checkin` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '签到主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '签到用户ID',
  `checkin_date` VARCHAR(10) NOT NULL COMMENT '签到日期 YYYY-MM-DD',
  `date_val` DATE GENERATED ALWAYS AS (STR_TO_DATE(checkin, '%Y-%m-%d')) STORED,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '签到时刻',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_checkin_uid_date` (`user_id`, `checkin_date`),
  INDEX `idx_checkin_uid` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日论坛签到';

-- ====================== 20. 视频资源表 ======================
CREATE TABLE IF NOT EXISTS `video_resource` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '视频主键',
  `subject` VARCHAR(64) NOT NULL COMMENT '所属科目',
  `knowledge_point` VARCHAR(128) NOT NULL COMMENT '对应知识点',
  `title` VARCHAR(180) NOT NULL COMMENT '视频标题',
  `platform` VARCHAR(64) DEFAULT 'Bilibili' COMMENT '平台',
  `url` VARCHAR(255) DEFAULT '' COMMENT '视频链接',
  `cover_url` VARCHAR(255) DEFAULT '' COMMENT '封面图片链接',
  `duration` VARCHAR(32) DEFAULT '' COMMENT '视频时长',
  `reason` TEXT DEFAULT '' COMMENT '推荐理由',
  `is_deleted` TINYINT(1) DEFAULT 0,
  INDEX `idx_video_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_video_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='408配套视频资源';

-- ====================== 21. 视频爬虫日志 ======================
CREATE TABLE IF NOT EXISTS `video_crawl_log` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '爬取日志主键',
  `subject` VARCHAR(64) NOT NULL COMMENT '科目',
  `knowledge_point` VARCHAR(128) NOT NULL COMMENT '知识点',
  `url` VARCHAR(255) NOT NULL COMMENT '视频链接',
  `platform` VARCHAR(64) NOT NULL COMMENT '爬取平台',
  `status` ENUM('success','fail') NOT NULL COMMENT '爬取状态',
  `crawl_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
  `error_msg` TEXT DEFAULT '' COMMENT '失败报错信息',
  UNIQUE KEY `uk_crawl_url` (`url`),
  INDEX `idx_crawl_sub_kp` (`subject`, `knowledge_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频爬虫日志';

-- ====================== 22. RAG知识库文档 ======================
CREATE TABLE IF NOT EXISTS `knowledge_document` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '文档主键',
  `subject` VARCHAR(64) NOT NULL COMMENT '科目',
  `parent_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '与科目同名',
  `name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '一级大章名称',
  `section` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '二级小节名称',
  `knowledge_point` VARCHAR(128) NOT NULL COMMENT '对应知识点名称',
  `file_path` VARCHAR(255) NOT NULL COMMENT 'md文件路径',
  `content` TEXT NOT NULL COMMENT '文档全文内容',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  INDEX `idx_doc_sub_name_sec` (`subject`, `name`, `section`),
  INDEX `idx_doc_sub_kp` (`subject`, `knowledge_point`),
  INDEX `idx_doc_del` (`is_deleted`),
  FULLTEXT INDEX `ft_doc_content` (`content`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='RAG知识库Markdown文档';

-- ====================== 23. 用户每日行为统计 ======================
CREATE TABLE IF NOT EXISTS `user_daily_activity` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '日活主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `date` VARCHAR(10) NOT NULL COMMENT '统计日期 YYYY-MM-DD',
  `date_val` DATE GENERATED ALWAYS AS (STR_TO_DATE(date, '%Y-%m-%d')) STORED,
  `answer_count` INT DEFAULT 0 COMMENT '当日答题数',
  `forum_count` INT DEFAULT 0 COMMENT '当日观看视频数',
  `video_count` INT DEFAULT 0 COMMENT '当日观看视频数',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_daily_uid_date` (`user_id`, `date`),
  INDEX `idx_daily_uid` (`user_id`),
  INDEX `idx_daily_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户每日学习行为统计';

-- ====================== 24. 个性化推荐待处理队列 ======================
CREATE TABLE IF NOT EXISTS `user_pending_recommendation` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '推荐任务主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `knowledge_point_id` INT UNSIGNED NOT NULL COMMENT '待推荐知识点ID',
  `reason` TEXT DEFAULT '' COMMENT '推荐依据',
  `is_finish` TINYINT(1) DEFAULT 0 COMMENT '是否已生成推荐',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`knowledge_point_id`) REFERENCES `knowledge_point`(`id`) ON DELETE CASCADE,
  INDEX `idx_rec_user` (`user_id`),
  INDEX `idx_rec_finish` (`is_finish`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4_unicode_ci COMMENT='个性化推荐待处理队列';

-- ====================== 25. 学习报告 ======================
CREATE TABLE IF NOT EXISTS `report` (
  `id` INT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '报告主键',
  `user_id` INT UNSIGNED NOT NULL COMMENT '所属用户ID',
  `title` VARCHAR(128) DEFAULT '学习报告' COMMENT '报告标题',
  `report_type` ENUM('daily','weekly','monthly','stage') DEFAULT 'stage' COMMENT '报告类型',
  `start_date` VARCHAR(10) DEFAULT '' COMMENT '周期起始',
  `end_date` VARCHAR(10) DEFAULT '' COMMENT '周期结束',
  `summary` TEXT DEFAULT '' COMMENT '整体总结',
  `weak_points` TEXT DEFAULT '' COMMENT '薄弱知识点汇总',
  `main_error_type` TEXT DEFAULT '' COMMENT '高频错误类型',
  `qa_focus` TEXT DEFAULT '' COMMENT '问答重点',
  `forum_focus` TEXT DEFAULT '' COMMENT '论坛学习重点',
  `video_suggestion` TEXT DEFAULT '' COMMENT '视频学习建议',
  `plan_json` TEXT DEFAULT '[]' COMMENT '学习计划JSON',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '报告生成时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  INDEX `idx_report_uid` (`user_id`),
  INDEX `idx_report_type` (`report_type`),
  INDEX `idx_report_del` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户阶段性学习报告';

SET FOREIGN_KEY_CHECKS = 1;
