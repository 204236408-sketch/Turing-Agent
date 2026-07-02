# 重生之我是图灵：Turing 408 Agent

面向考研 408 的 Web 智能辅导 Agent 系统。前端保留当前 `version-b.html + styles.css + app.js` 轻量工作台方案；后端使用 FastAPI，默认 SQLite 开箱即用，后续可按 `.env` 切换 MySQL、ChromaDB、PaddleOCR 和硅基流动大模型。


打开：

```text
http://127.0.0.1:8000
```


## 已落地能力

- 统一报错机制：所有失败响应返回 `ok:false / error.code / error.message / request_id`。
- 登录注册、Token、个人画像、首页概览、知识图谱、掌握度统计。
- 知识问答 Agent：目标识别、读取长期记忆、检索 408 知识、生成结构化回答。
- 智能出题 Agent：自由选择出题、智能推荐出题、出题批次、题目保存。
- 答题批改 Agent：答案判断、答题记录、掌握状态刷新、错因候选。
- 错题分析 Agent：错因确认、错题入库、长期记忆写入、复练建议。
- OCR 演示接口：上传返回 Mock OCR 文本，分析接口写入错题。
- 学习论坛和 AI 小助手：帖子、评论、点赞、收藏、AI 回答。
- 学习报告：汇总答题、错题、记忆、薄弱点和下一轮计划。

## 项目结构

```text
turing/
├── version-b.html / styles.css / app.js      # 当前直接可用前端
├── frontend/                                 # 按 PDF 结构保留的前端副本
├── backend/                                  # FastAPI 后端
├── database/                                 # SQL 与迁移文件
├── docs/                                     # 技术文档与分工方案
├── deploy/                                   # Nginx、Docker、启动脚本
└── tests/                                    # 接口测试
```

## 大模型配置

复制 `backend\.env.example` 为 `backend\.env`，填入：

```text
SILICONFLOW_API_KEY=你的硅基流动密钥
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3
```

检查：

```text
http://127.0.0.1:8000/api/health
```
