---
name: fastapi-backend
description: 用于本项目 FastAPI 后端开发，生成 router、service、schema、model、JWT、数据库查询和接口联调代码。
---

# FastAPI Backend Skill

## 项目背景

本项目是“面向考研408的 Web AI Agent 学习系统”。

后端技术栈：

- FastAPI
- SQLAlchemy
- Pydantic
- MySQL / SQLite
- ChromaDB
- LangChain
- LangGraph
- JWT

## 项目目录规范

后端代码必须放在 backend/ 目录下。

常用目录：

- backend/routers/：接口路由
- backend/services/：业务逻辑
- backend/agents/：AI Agent 调度
- backend/graphs/：LangGraph 工作流
- backend/prompts/：Prompt 模板
- backend/models.py：SQLAlchemy 模型
- backend/schemas.py：Pydantic 模型
- backend/database.py：数据库连接
- backend/dependencies.py：通用依赖
- backend/auth.py：JWT 认证

## 代码生成规则

当用户要求新增后端功能时，必须优先按以下结构生成：

1. router：只负责接收请求和返回响应
2. service：负责业务逻辑
3. schemas：负责请求体和响应体
4. models：负责数据库结构
5. dependencies：负责当前用户、数据库 session 等依赖

不要把复杂业务逻辑直接写在 router 里。

## 接口规范

所有接口统一使用 `/api` 前缀。

示例：

- GET /api/home/overview
- POST /api/questions/generate
- POST /api/answers/check
- POST /api/ocr/upload
- GET /api/knowledge/graph

## 返回格式

接口返回尽量统一：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}