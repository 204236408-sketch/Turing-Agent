# 重生之我是图灵：面向考研 408 的 Web 智能辅导 Agent 系统

本仓库严格按照《Rebirth of Turing - Web AI Agent System for 408 Exam》技术方案组织。

## 技术栈

- 前端：原生 HTML、CSS、JavaScript、Fetch/Axios
- 后端：FastAPI、SQLAlchemy、Pydantic、JWT
- 数据：MySQL + ChromaDB
- AI：LangChain + LangGraph + 外部大模型 API
- OCR：PaddleOCR + OpenCV/Pillow
- 部署：Nginx + Uvicorn/Gunicorn

> 技术方案明确要求沿用 `version-b`，当前阶段不使用 Vue/React 重写。

## 目录

```text
frontend/       version-b 原生前端
backend/        FastAPI、业务服务、Agent、Prompt、向量库
database/       MySQL 建表、初始化数据与 SQL 迁移
deploy/         Nginx、进程服务与容器部署
docs/           技术、数据库、接口、部署和答辩文档
tests/          核心模块测试
```

## 快速开始

1. 复制 `backend/.env.example` 为 `backend/.env`。
2. 创建 MySQL 数据库并执行 `database/schema.sql`。
3. 在 `backend/` 安装 `requirements.txt`。
4. 运行 `uvicorn main:app --reload`。
5. 使用静态服务器打开 `frontend/version-b.html`。

完整结构与责任边界见 [仓库结构说明](docs/仓库结构说明.md) 和 [团队分工](docs/team-division.md)。
