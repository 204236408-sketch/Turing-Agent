# P3 AI、RAG 与爬虫工作手册（综合新版）

> 角色定位：LangChain/LangGraph Agent、ChromaDB/RAG、Prompt、视频爬虫、相似错题、AI fallback。  
> 上游：P2 数据库与知识库。  
> 下游：P1 API、P4 页面、P5 测试。
>
> 注意：P3 是本次变化最大的角色。Day 1 不沿用旧版“只做 prompt 和爬虫骨架”，而是优先补 PDF 差距审计指出的 ChromaDB 和 LangGraph 地基。

---

## 0. P3 无痛执行区

这一节是 P3 每天开始前先看的执行卡。P3 的任务不是单独写一个“看起来聪明”的函数，而是把 P2 的数据加工成 P1 能封装、P4 能展示、P5 能验收的稳定 AI 能力。

### 0.1 今天开始前先确认

| 要确认的事 | 找谁拿 | 为什么 |
|---|---|---|
| 知识点、题库、文档、视频样例 | P2 | Agent/RAG 必须基于真实数据，不要硬编码演示答案 |
| 接口需要的返回字段 | P1 | 返回 JSON 要能直接被 router 包装 |
| 页面要展示的结构 | P4 | 例如 `agent_steps`、来源、推荐理由、视频理由是否展示 |
| 今天要测的降级场景 | P5 | 无 LLM、无 Chroma、爬虫失败时必须有可测结果 |

### 0.2 P3 每天固定执行顺序

1. 上午先定义函数签名和返回 JSON，不先写复杂逻辑。
2. 用 P2 给的最小样例跑通一条正常路径。
3. 给 P1 一份输入输出样例，让 P1 能先接接口。
4. 下午补 Agent/RAG/爬虫内部逻辑和 `agent_steps`。
5. 手动模拟外部依赖失败，确认 fallback 不会让接口 500。
6. 晚上交付正常样例、失败样例、fallback 样例。

### 0.3 P3 交付模板

```text
P3 今日交付

函数/服务：
- 文件：
- 函数名：
- 入参：
- 返回 JSON：

正常输入样例：
- {}

正常返回样例：
- {"agent_steps": [], "llm_used": false, "llm_error": ""}

降级行为：
- 无 LLM：
- 无 ChromaDB：
- 爬虫失败：
- 数据为空：

交付给：
- P1：如何接 router
- P4：哪些字段可展示
- P5：测试正常/失败/降级的方式

未完成/风险：
- 依赖：
- 可能变化字段：
- 明天补充：
```

### 0.4 P3 完成标准

| 层级 | 完成标准 |
|---|---|
| 函数 | P1 能直接 import 或调用，入参和返回稳定 |
| 数据 | 使用 P2 数据，不靠固定演示字符串冒充 |
| Agent | 返回 `agent_steps`，能解释每一步做了什么 |
| 降级 | 无 LLM、无 Chroma、爬虫失败时返回结构完整 |
| 文档 | 写清输入输出、依赖配置和失败行为 |
| 验收 | P5 能用样例复现正常和失败场景 |

不算完成：

- 只在 notebook 或临时脚本里跑通。
- 只返回一段文本，P4 无法结构化展示。
- 外部服务失败时抛异常。
- 今天返回 `answer`，明天改成 `result`，没有同步 P1/P4/P5。

### 0.5 新 P3 接手时怎么做

1. 先看 P2 的数据交付说明，跑导入或读取样例。
2. 打开 P1 接口文档，确认接口需要哪些字段。
3. 打开 P5 验收清单，确认失败的是正常路径还是降级路径。
4. 先写一个稳定返回结构，再补内部智能逻辑。
5. 每接一个外部依赖，都同时写 fallback。

### 0.6 P3 遇到阻塞怎么处理

P3 最常见阻塞是没有真实数据、LLM/Chroma 不可用、返回结构和 P1/P4 预期不一致。

```text
阻塞点：
影响哪个 Agent/RAG/爬虫函数：
影响哪个接口/页面/测试：
需要 P2/P1/P4/P5 提供什么：
当前可用 fallback：
最晚需要时间：
```

如果外部依赖 30 分钟内不可恢复，必须先交 fallback 版本，保证 P1 接口和 P5 测试不被卡死。

### 0.7 P3 完成后上传到 Gitee

按 `docs/Gitee提交流程.md` 上传。P3 通常只提交：

```text
backend/agents/
backend/services/chroma_service.py
backend/services/rag_service.py
backend/services/video_crawler_service.py
backend/services/vector_embedding_service.py
backend/scripts/import_knowledge_to_chroma.py
backend/scripts/crawl_videos.py
docs/Agent流程说明.md
docs/RAG知识库说明.md
```

上传前检查：

```powershell
git status --short
```

只添加明确交付文件，例如：

```powershell
git add backend/agents/qa_graph.py backend/services/rag_service.py docs/Agent流程说明.md docs/RAG知识库说明.md
git commit -m "P3 Day2: 接入 QA RAG 和降级说明"
git push -u origin p3-day2-rag
```

不要上传本地 Chroma 向量库、LLM Key、日志和临时实验脚本。返回 JSON 变化时，必须同步更新 `docs/Agent流程说明.md`。

---

## 1. P3 整体负责范围

| 负责部分 | 具体内容 | 文件 |
|---|---|---|
| LangGraph 状态 | QA、出题、批改、错题分析的 State | `backend/agents/graph_state.py` |
| QA Graph | 意图识别、历史、RAG、记忆、掌握度、回答、fallback | `backend/agents/qa_graph.py`、`backend/agents/qa_agent.py` |
| 出题 Graph | 用户状态、目标知识点、检索、生成、校验、保存 | `backend/agents/question_graph.py`、`backend/agents/question_agent.py` |
| 批改 Graph | 加载题目、客观判分、LLM 反馈、推荐错因、更新掌握度 | `backend/agents/answer_graph.py`、`backend/agents/answer_check_agent.py` |
| 错题 Graph | 错因分析、写错题、写记忆、写向量、推荐复练 | `backend/agents/mistake_graph.py`、`backend/agents/mistake_agent.py` |
| ChromaDB | collection、写入、查询、重建、降级 | `backend/services/chroma_service.py` |
| RAG | 知识库、记忆、错题摘要检索 | `backend/services/rag_service.py` |
| 视频爬虫 | 搜索、解析、评分、去重、入库、限流 | `backend/services/video_crawler_service.py`、`backend/scripts/crawl_videos.py` |
| 论坛 AI | 结合发帖人画像回答 | `backend/agents/forum_agent.py` |
| 报告 Agent | 结构化计划、趋势、画像、视频建议 | `backend/agents/report_agent.py` |

---

## 2. 上下游先后顺序

```text
P2 给：知识点、题库、视频、知识库 Markdown、schema
P3 做：ChromaDB、RAG、LangGraph、Agent、爬虫
P1 接：函数返回值，包装 API
P4 展示：answer、agent_steps、推荐、视频、报告计划
P5 测：无 LLM、无 Chroma、爬虫失败、Agent 输出结构
```

P3 每天交给 P1/P4/P5：

- 函数名。
- 输入参数。
- 返回 JSON。
- `agent_steps` 格式。
- 无 LLM fallback。
- 无 ChromaDB fallback。
- 失败是否抛异常。

---

## 3. 所有 Agent 的统一输出规则

所有 Agent 都必须返回：

```json
{
  "agent_steps": [],
  "llm_used": false,
  "llm_error": ""
}
```

`agent_steps` 每一项：

```json
{
  "name": "检索知识库",
  "input_summary": "操作系统/页面置换算法",
  "output_summary": "命中 3 个 chunk",
  "duration_ms": 42,
  "status": "success"
}
```

禁止：

- 只返回一段字符串。
- LLM 失败直接抛异常。
- Chroma 不可用导致接口 500。
- 返回字段今天一个格式、明天另一个格式。

---

## 4. 每天工作安排

## Day 1：ChromaDB 和 LangGraph 地基

### 上午要做：Graph State

新增：

```text
backend/agents/graph_state.py
```

建议内容：

```python
from typing import Any, TypedDict

class AgentStep(TypedDict, total=False):
    name: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str

class QAState(TypedDict, total=False):
    user_id: int
    conversation_id: int | None
    question: str
    subject: str
    knowledge_point: str
    history: list[dict]
    retrieved_knowledge: list[dict]
    memories_used: list[dict]
    mastery: dict
    answer: dict
    suggested_followups: list[str]
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str

class QuestionState(TypedDict, total=False):
    user_id: int
    mode: str
    subject: str
    knowledge_point: str
    difficulty: str
    question_type: str
    count: int
    context: list[dict]
    questions: list[dict]
    session_id: int
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str

class AnswerCheckState(TypedDict, total=False):
    user_id: int
    question_id: int
    user_answer: str
    question: dict
    is_correct: bool
    score: float
    feedback: dict
    recommended_causes: list[str]
    answer_record_id: int
    mastery: dict
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str

class MistakeState(TypedDict, total=False):
    user_id: int
    answer_record_id: int
    error_types: list[str]
    user_note: str
    mistake_id: int
    memory_id: int
    similar_mistakes: list[dict]
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str
```

新增：

```text
backend/services/vector_embedding_service.py
```

要求：

- 提供 `embed_texts(texts: list[str])`。
- 如果没有 embedding API，允许先使用 Chroma 默认 embedding。
- 不可用时返回清晰 fallback 状态。

### 下午要做：ChromaDB 服务

重写：

```text
backend/services/chroma_service.py
```

必须实现：

```python
def chroma_status() -> dict: ...
def get_client(): ...
def get_or_create_collection(name: str): ...
def upsert_document(collection: str, document_id: str, text: str, metadata: dict | None = None) -> dict: ...
def query_documents(collection: str, query: str, limit: int = 5, where: dict | None = None) -> dict: ...
def delete_collection(name: str) -> dict: ...
```

Collection：

```text
knowledge_base_408
user_memory_vector
mistake_summary
```

失败规则：

```text
chromadb import 失败 -> enabled=false
写入失败 -> stored=false + error
查询失败 -> items=[] + fallback=true
```

修改：

```text
backend/scripts/import_knowledge_to_chroma.py
```

支持读取：

```text
backend/data/knowledge_docs/*.md
```

### 交付给谁

- 给 P1：`chroma_status` 和 query/upsert 函数。
- 给 P5：可测 Chroma 成功/失败。
- 给 P2：知识库 Markdown 元数据要求。

### 完成标准

- Chroma 可用时能创建 collection。
- Chroma 不可用时不 500。
- 导入脚本能遍历 Markdown。

---

## Day 2：QA Graph、RAG、会话摘要

### 上午要做：QA Graph

新增：

```text
backend/agents/qa_graph.py
```

节点顺序：

```text
detect_intent
→ load_history
→ retrieve_knowledge
→ retrieve_memory
→ load_mastery
→ generate_answer
→ validate_answer
→ fallback_answer
```

每个节点必须追加 `agent_steps`。

`detect_intent` 输出：

```json
{
  "subject": "操作系统",
  "knowledge_point": "页面置换算法",
  "is_followup": true
}
```

追问判断：

```text
长度 < 10
或包含：为什么、然后、所以、举个例子、再说一遍、那呢、还有、具体
或以“那”“这”开头
```

修改：

```text
backend/agents/qa_agent.py
```

要求：外部函数 `answer_question(db, user_id, question, conversation_id=None)` 保持可用，内部调用 `qa_graph`。

### 下午要做：RAG 和摘要

修改：

```text
backend/services/rag_service.py
```

检索顺序：

```text
ChromaDB knowledge_base_408
→ MySQL knowledge_point/content/keywords fallback
→ 返回空数组但不报错
```

新增：

```text
backend/agents/summary_agent.py
backend/agents/plan_agent.py
```

`summary_agent.py`：

- 生成会话标题。
- 生成会话摘要。
- 生成 3 个追问建议。

`plan_agent.py`：

- 输入用户最近答题、错题、记忆。
- 输出今日计划个性化原因。
- 无 LLM 用模板。

### 交付给谁

- 给 P1：QA 返回结构。
- 给 P4：answer、agent_steps、suggested_followups 展示字段。
- 给 P5：无 LLM、无 Chroma、追问测试。

### 完成标准

- QA 返回结构化 JSON。
- 至少 4 个 agent_steps。
- 支持连续追问。

---

## Day 3：出题、批改、错题分析 Graph

### 上午要做：出题 Graph

新增：

```text
backend/agents/question_graph.py
```

节点：

```text
analyze_user_state
select_target
retrieve_question_context
generate_questions
validate_questions
save_questions
fallback_questions
```

修改：

```text
backend/agents/question_agent.py
```

保持原函数名 `generate_questions()` 不变，内部调用 graph。

题目校验规则：

- 题干不能为空。
- `subject/knowledge_point` 必须匹配目标。
- 选择题必须有 4 个选项。
- 必须有标准答案。
- 必须有解析和提示。

### 下午要做：批改和错题 Graph

新增：

```text
backend/agents/answer_graph.py
backend/agents/mistake_graph.py
backend/agents/hint_agent.py
```

`answer_graph.py` 节点：

```text
load_question
check_objective_answer
llm_feedback
recommend_causes
update_answer_record
update_mastery
fallback_check
```

错因推荐：

```text
固定 ["审题错误", "计算错误"]
+ common_mistakes 提取 1-2 个
+ 最近 20 条 mistake 高频错因 1 个
+ LLM 提取 0-1 个
```

`mistake_graph.py` 节点：

```text
load_answer_record
analyze_error
write_mistake
write_memory
write_chroma_summary
recommend_retrain
```

`hint_agent.py`：

```text
薄弱点 -> 详细模式
不熟 -> 适中模式
不会/未学 -> 教学模式
掌握 -> 验证模式
```

### 交付给谁

- 给 P1：出题、批改、错题 Agent 函数返回字段。
- 给 P4：批改展示字段和动态错因。
- 给 P5：闭环测试方法。

### 完成标准

- 出题、批改、错题都有 agent_steps。
- 答错后返回 `recommended_causes`。
- 错题摘要写入 `mistake_summary` 或 fallback。

---

## Day 4：视频爬虫、论坛 AI、报告 Agent、OCR 权重

### 上午要做：视频爬虫

新增：

```text
backend/services/video_crawler_service.py
backend/scripts/crawl_videos.py
```

服务函数：

```python
def crawl_for_point(db, subject: str, knowledge_point: str) -> list[dict]: ...
def crawl_all_points(db) -> dict: ...
def score_video(video: dict, subject: str, knowledge_point: str) -> float: ...
def deduplicate_videos(videos: list[dict]) -> list[dict]: ...
```

评分：

```text
quality_score =
  platform_weight * 0.30
  + relevance_weight * 0.40
  + popularity_weight * 0.20
  + freshness_weight * 0.10
```

限流：

```text
同一知识点 1 小时最多爬 1 次
已有 >= 3 条不爬
1-2 条后台补充
0 条返回 fallback 并后台补充
```

### 下午要做：论坛、报告、OCR

修改：

```text
backend/agents/forum_agent.py
backend/agents/report_agent.py
backend/agents/mistake_agent.py
```

论坛 AI 输入：

```json
{
  "post": {},
  "author_profile": {
    "mastery_status": "不熟",
    "recent_memories": [],
    "common_errors": []
  },
  "comments_context": []
}
```

报告计划必须结构化：

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

OCR 权重：

```text
ocr_weight_increase =
base 3 + duplicate_bonus * 2 + severity_bonus * 1.5 + recency_bonus * 1
```

重复检测：

```text
相似度 > 0.8 -> 重复错误，weak_score 额外 +2
相似度 > 0.95 -> 完全重复，不新增错题，只更新时间
```

### 完成标准

- 视频爬虫失败不影响视频接口。
- 论坛 AI 能体现“结合你的学习情况”。
- 报告计划可点击生成题。
- OCR 错题写入 Chroma 或 fallback。

---

## Day 5：降级验收和说明文档

### 上午要做

逐项测试：

```text
无 LLM
无 ChromaDB
视频爬虫失败
OCR 不可用
```

每个 Agent 必须仍返回完整结构。

### 下午要做

新增或更新：

```text
docs/Agent流程说明.md
docs/RAG知识库说明.md
docs/项目答辩稿.md
```

说明内容：

- QA graph 节点。
- 出题 graph 节点。
- 批改 graph 节点。
- 错题 graph 节点。
- ChromaDB collection。
- fallback 策略。

### 完成标准

- P5 能完成降级测试。
- 答辩时能解释 Agent 和 RAG 怎么工作。

---

## 5. P3 每日自查清单

- 是否有 `agent_steps`？
- 是否有 `llm_used`？
- 是否有 `llm_error`？
- 无 LLM 是否可用？
- 无 Chroma 是否可用？
- 返回字段是否固定？
- 是否把输出 JSON 交给 P1/P4/P5？

## 6. P3 最终交付物

- ChromaDB 服务。
- RAG 检索服务。
- QA LangGraph。
- 出题 LangGraph。
- 批改 LangGraph。
- 错题分析 LangGraph。
- 视频爬虫。
- 论坛 AI 个性化。
- 报告结构化计划。
- Agent/RAG 说明文档。
