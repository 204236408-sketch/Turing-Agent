# P3 AI、RAG 与爬虫工作手册

> 角色定位：Agent、Prompt、RAG、ChromaDB、视频爬虫、相似错题、AI 降级。  
> 你承接 P2 的数据，把数据加工成智能结果，再交给 P1 包装成接口。

## 1. 你负责的大模块

| 模块 | 负责内容 | 关键文件 |
|---|---|---|
| 问答 Agent | 结构化回答、追问识别、Agent 步骤 | `backend/agents/qa_agent.py`、`backend/prompts/qa_prompt.py` |
| 出题 Agent | LLM 出题、fallback、题目格式 | `backend/agents/question_agent.py` |
| 批改 Agent | 判对错、反馈、推荐错因 | `backend/agents/answer_check_agent.py` |
| 错题 Agent | 错因确认、长期记忆、OCR 分析 | `backend/agents/mistake_agent.py` |
| 掌握触发链 | 不会/不熟/掌握后的连锁动作 | `backend/services/mastery_service.py` 或 `backend/agents/mastery_agent.py` |
| RAG/Chroma | 知识库导入、相似错题检索、降级检索 | `backend/services/chroma_service.py`、`backend/scripts/import_knowledge_to_chroma.py` |
| 视频爬虫 | 搜索、解析、评分、入库、限流 | `backend/services/video_crawler_service.py`、`backend/scripts/crawl_videos.py` |
| 论坛 AI | 结合发帖人画像回答 | `backend/agents/forum_agent.py` |
| 报告 Agent | 结构化报告、训练计划 | `backend/agents/report_agent.py` |

## 2. 先后顺序和交接关系

```text
P2 先给你：知识点、题库、视频、知识库文档、表结构
P3 产出：Agent 函数、统一 JSON、RAG 检索、爬虫结果
P1 接收：函数返回值并包装成 API
P4 接收：结构化字段并展示页面
P5 接收：可 mock 的 Agent 和无 LLM fallback
```

你的原则：

- 所有 Agent 都必须有 fallback。
- 所有 Agent 返回字段必须固定。
- 不要把异常直接抛到用户接口。
- LLM 是增强，不是系统能否运行的前提。

## 3. 统一 Agent 返回规则

每个 Agent 返回都必须包含：

- 业务结果。
- `llm_used`。
- `llm_error`。
- 可解释的步骤或依据。
- fallback 时也要字段完整。

禁止返回：

```json
{"answer": "一大段纯文本"}
```

应该返回：

```json
{
  "answer": {
    "direct_answer": "...",
    "step_by_step": [],
    "common_mistakes": [],
    "practice_suggestion": {}
  },
  "agent_steps": [],
  "llm_used": false,
  "llm_error": "SILICONFLOW_API_KEY 未配置"
}
```

## 4. 五天工作安排

### 第 1 天：统一 Prompt 和 Agent 契约

#### 要做什么

1. 检查所有 Agent：
   - `qa_agent.py`
   - `question_agent.py`
   - `answer_check_agent.py`
   - `mistake_agent.py`
   - `forum_agent.py`
   - `report_agent.py`
2. 给每个 Agent 规定返回 JSON。
3. 修改 `backend/prompts/*.py`，要求 LLM 返回结构化 JSON。
4. 新建或规划 `backend/services/video_crawler_service.py`。
5. 设计 ChromaDB chunk 元数据。

#### QA 返回结构

```json
{
  "subject": "操作系统",
  "knowledge_point": "页面置换算法",
  "answer": {
    "direct_answer": "LRU 的核心是淘汰最长时间未被访问的页面。",
    "step_by_step": ["先列页框", "判断命中", "未命中则替换"],
    "exam_focus": ["缺页次数计算", "算法对比"],
    "common_mistakes": ["初始缺页漏算", "命中后不更新顺序"],
    "practice_suggestion": {
      "action": "generate_questions",
      "subject": "操作系统",
      "knowledge_point": "页面置换算法",
      "count": 3
    }
  },
  "agent_steps": [],
  "memories_used": [],
  "suggested_followups": [],
  "llm_used": true
}
```

#### 交付给谁

- 交给 P1：每个 Agent 的输入输出字段。
- 交给 P4：前端展示需要的结构字段。
- 交给 P5：无 LLM 时的 mock/fallback 样例。

#### 完成标准

- 每个 Agent 返回字段固定。
- 没有 LLM Key 时仍能返回完整结构。
- P1 可以开始写接口契约。

### 第 2 天：视频爬虫和 QA 上下文

#### 要做什么

1. 实现 `backend/services/video_crawler_service.py` 第一版。
2. 至少包含：
   - `crawl_for_point(subject, knowledge_point)`
   - `crawl_all_points()`
   - `score_video(video, subject, knowledge_point)`
   - `deduplicate_videos(videos)`
3. 实现视频评分。
4. 优化 `qa_agent.py`。
5. QA 加入：
   - 最近 5 轮对话。
   - 用户长期记忆。
   - 知识点检索结果。
   - 追问识别。

#### 视频评分公式

```text
quality_score =
  platform_weight * 0.30 +
  relevance_weight * 0.40 +
  popularity_weight * 0.20 +
  freshness_weight * 0.10
```

#### 爬虫限流规则

```text
同一 knowledge_point 1 小时最多爬 1 次。
数据库已有 >= 3 条视频时不爬。
任一平台失败，不影响其他平台。
失败时返回空数组，不抛异常。
```

#### QA 追问规则

```text
如果用户输入少于 10 个字，或包含“为什么、举例、然后、那呢、具体”，
则继承上一轮 subject 和 knowledge_point。
```

#### 交付给谁

- 交给 P1：爬虫服务函数和 QA 返回结构。
- 交给 P4：QA 的 `agent_steps` 和 `suggested_followups`。
- 交给 P5：爬虫失败和无 LLM 的测试条件。

#### 完成标准

- 视频爬虫失败不会影响接口。
- QA 能识别追问。
- QA 返回 agent_steps。

### 第 3 天：Chroma、批改、掌握触发链

#### 要做什么

1. 实现 `backend/services/chroma_service.py`。
2. 支持：
   - 写入知识库 chunk。
   - 写入错题摘要。
   - 查询相似错题。
   - Chroma 不可用时降级。
3. 修改 `answer_check_agent.py`。
4. 返回推荐错因 `recommended_causes`。
5. 实现掌握状态触发链。

#### 推荐错因规则

```text
recommended_causes =
  固定保留 ["审题错误", "计算错误"]
  + knowledge_point.common_mistakes 提取 1-2 个
  + 用户最近 20 条 mistake 中最高频 1 个
```

#### 掌握状态触发链

标记“不会”：

```text
写 user_memory，weak_score +2。
写 user_pending_recommendation，安排同类题。
写 user_daily_activity。
```

标记“不熟”：

```text
写 user_memory，weak_score +1。
安排 3 天后复习。
写 user_daily_activity。
```

标记“掌握”：

```text
降低推荐权重。
相关 mistake 标记 resolved。
安排 7 天后复测。
写 user_daily_activity。
```

#### 交付给谁

- 交给 P1：`search_similar_mistakes`、`recommended_causes`、触发链返回字段。
- 交给 P4：错因展示和触发结果 toast 文案。
- 交给 P5：相似错题、推荐错因、掌握触发测试。

#### 完成标准

- Chroma 不安装也能运行。
- 答错后不是固定 8 个错因。
- 标记状态后有 `triggered_actions`。

### 第 4 天：论坛 AI、OCR 权重、报告计划

#### 要做什么

1. 修改 `forum_agent.py`。
2. 论坛 AI 输入增加：
   - 帖子标题和内容。
   - 作者该知识点掌握状态。
   - 最近 2 条相关记忆。
   - 最近 3 个错因。
3. 修改 `mistake_agent.py` 的 OCR 分析。
4. OCR 错题增加重复检测和权重规则。
5. 修改 `report_agent.py`。
6. 报告计划返回结构化数组，不要纯文本。

#### OCR 权重规则

```text
ocr_weight_increase =
  base 3 +
  duplicate_bonus * 2 +
  severity_bonus * 1.5 +
  recency_bonus * 1
```

重复检测：

```text
相似度 > 0.8：重复错误，weak_score 额外 +2。
相似度 > 0.95：完全重复，不新增错题，只更新时间和权重。
```

#### 论坛 AI 输出规则

回答分三段：

1. 先解释帖子问题。
2. 再写“结合你的学习情况”。
3. 最后给一个动作建议：做题、复习、追问或收藏。

#### 报告计划结构

```json
{
  "step": 1,
  "subject": "操作系统",
  "knowledge_point": "页面置换算法",
  "action": "专项练习",
  "count": 3,
  "difficulty": "中等",
  "estimated_minutes": 25,
  "reason": "针对 LRU 缺页统计遗漏"
}
```

#### 交付给谁

- 交给 P1：论坛 AI、OCR、报告 Agent 返回字段。
- 交给 P4：论坛 AI 展示、报告训练计划点击字段。
- 交给 P5：OCR 重复、报告计划测试。

#### 完成标准

- 论坛 AI 能体现用户画像。
- OCR 错题能写入记忆和权重。
- 报告计划可点击生成题目。

### 第 5 天：AI 降级和爬虫定时任务

#### 要做什么

1. 逐个关闭 LLM Key 测试所有 Agent。
2. 确保所有 Agent 有 fallback。
3. 新增或完善：
   - `backend/scripts/crawl_videos.py`
   - `backend/scheduler.py`
4. 配合 P1 在云端配置每日凌晨 3 点爬虫。
5. 配合 P5 全链路验收。

#### 降级规则

```text
LLM 不可用：
  QA 用知识点 content + common_mistakes 模板回答。
  出题用 seed_questions 或规则题。
  批改用标准答案比对 + 模板反馈。
  论坛 AI 用通用回答。
  报告用真实统计 + 模板计划。
```

#### 完成标准

- 无 LLM Key 时系统全链路可跑。
- 爬虫可手动执行。
- 爬虫失败不影响用户使用。

## 5. 每日自查清单

- 返回字段是否固定？
- 无 LLM 时是否能返回同样结构？
- 是否写了 `llm_used` 和 `llm_error`？
- 是否把新字段告诉 P1/P4/P5？
- 是否避免把外部服务异常直接抛给用户？

## 6. 你的最终交付物

- 结构化 QA Agent。
- 结构化批改 Agent。
- 推荐错因算法。
- 错题和 OCR 记忆逻辑。
- ChromaDB/降级检索。
- 视频爬虫和评分。
- 论坛个性化 AI。
- 结构化报告计划。
- 所有 Agent 的 fallback。
