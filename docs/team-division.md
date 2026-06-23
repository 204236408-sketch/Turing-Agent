# 五人协作分工

## 第 1 人：后端

- 搭建 FastAPI、JWT、注册、登录和 Token 刷新。
- 汇总数据库、AI、Agent 能力并输出 REST API。
- 维护 Swagger、错误码、权限、日志和接口测试。

## 第 2 人：数据库

- 设计 MySQL 表、索引、外键和 Alembic 迁移。
- 重点完成 `conversation`、`conversation_message`、`user_memory`。
- 补充用户、知识点、题目、答题、错题、OCR、报告和论坛表。

## 第 3 人：RAG 与向量库

- 初始化 ChromaDB 和 408 知识库。
- 建立 `knowledge_base_408`、`conversation_summary`、`user_memory_vector`、`mastery_summary`、`mistake_summary` 等 Collection。
- 实现检索、向量写入、PaddleOCR 与视频资源匹配。

## 第 4 人：大模型、Prompt 与 Agent

- 配置外部大模型 API 和 `llm_service`。
- 设计问答、出题、批改、错题分析、记忆更新 Prompt。
- 增加学习报告与论坛 AI 助手 Agent。
- 输出稳定 JSON Schema，并建立测试样例和版本记录。

## 第 5 人：原生前端

- 维护 `frontend/version-b.html`、`styles.css`、`app.js`。
- 完成登录注册、首页、知识图谱、问答、出题、错题/OCR、报告、论坛和账号页面。
- 使用 Fetch/Axios 接入接口，保留 Mock 降级，不引入 Vue/React。

完整细则参见项目外部已形成的《重生之我是图灵-五人开发详细分工方案》。
