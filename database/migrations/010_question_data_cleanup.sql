-- 010_question_data_cleanup.sql
-- 清理 question 表历史脏数据
-- 脏数据来源：
--   1) subject='????' 的 2 道垃圾数据
--   2) variant_type=comprehensive 但无 standard_answer 的 5 道 fallback 模板
--   3) 同一 (subject, knowledge_point) 内题干前 50 字重复的题（21 组，~30 道）
--   4) 1 道 source='seed' 的题 quality_score=0（应当 100）

-- 1. 软删：subject 异常
UPDATE question SET is_deleted = 1
WHERE is_deleted = 0
  AND subject NOT IN ('数据结构', '操作系统', '计算机网络', '计算机组成原理');

-- 2. 软删：综合题无标准答案（fallback 模板残留，结构不完整）
UPDATE question SET is_deleted = 1
WHERE is_deleted = 0
  AND variant_type = 'comprehensive'
  AND (standard_answer = '' OR standard_answer IS NULL);

-- 3. 去重：按 (subject, knowledge_point, 题干前 50 字) 分组，每组保留 id 最大（最新）的一道
--    注意：使用 INNER JOIN + 子查询，SQLite 兼容
UPDATE question
SET is_deleted = 1
WHERE id IN (
    SELECT q1.id
    FROM question q1
    INNER JOIN (
        SELECT subject, knowledge_point, SUBSTR(question_text, 1, 50) AS sig, MAX(id) AS keep_id
        FROM question
        WHERE is_deleted = 0 AND question_text != ''
        GROUP BY subject, knowledge_point, sig
        HAVING COUNT(*) > 1
    ) dup
    ON  q1.subject = dup.subject
        AND q1.knowledge_point = dup.knowledge_point
        AND SUBSTR(q1.question_text, 1, 50) = dup.sig
        AND q1.id != dup.keep_id
);

-- 4. 修正：种子题 quality_score 应为 100
UPDATE question SET quality_score = 100
WHERE source = 'seed' AND quality_score = 0 AND is_deleted = 0;
