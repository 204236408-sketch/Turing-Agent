# Agent 流程说明

> P3 维护，P1/P4/P5 按此接接口、展示步骤和写测试。

## 统一返回字段

| 字段 | 类型 | 含义 | 为空时 |
|---|---|---|---|
| `agent_steps` | array | Agent 每一步执行摘要 | `[]` |
| `llm_used` | boolean | 是否调用 LLM | `false` |
| `llm_error` | string | LLM 错误信息 | `""` |
| `fallback_used` | boolean | 是否使用降级逻辑 | `false` |

## 统一返回说明

所有 Agent 返回均包含 `agent_steps`/`llm_used`/`llm_error`。
`agent_steps` 每项含 `name`/`input_summary`/`output_summary`/`duration_ms`/`status`。

---

## QA 问答 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/qa_agent.py` → `backend/agents/qa_graph.py` |
| **函数** | `answer_question(db, user_id, question, conversation_id=None)` |
| **输入** | `{user_id, question, conversation_id?}` |
| **输出** | `{answer, subject, knowledge_point, retrieved_knowledge, memories, suggested_followups, agent_steps, llm_used, llm_error}` |
| **Graph 节点** | `detect_intent` → `load_history` → `retrieve_knowledge` → `retrieve_memory` → `load_mastery` → `generate_answer` → `validate_answer` → `fallback_answer` |
| **无 LLM** | `fallback_answer` 节点返回模板回答，`llm_used=false` |
| **无 ChromaDB** | `retrieve_knowledge` 走 MySQL `KnowledgePoint` 关键词匹配 |
| **追问** | 长度 < 10 或含"为什么/然后/举个例子"等关键词 → 继承上一轮 subject/kp |
| **agent_steps 示例** | 8 步：意图识别→加载历史→检索知识→检索记忆→加载掌握度→生成回答→校验→完成 |

---

## 出题 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/question_agent.py` → `backend/agents/question_graph.py` |
| **函数** | `generate_questions(db, user_id, mode, subject, knowledge_point, difficulty, question_type, count, recommendation_reason="")` |
| **输入** | `{user_id, mode, subject, knowledge_point, difficulty, question_type, count, recommendation_reason?}` |
| **输出** | `{session_id, config, questions[], agent_steps, llm_used, llm_error}` |
| **Graph 节点** | `analyze_user_state` → `select_target` → `retrieve_question_context` → `generate_questions` → `validate_questions` → `save_questions` → `fallback_questions` |
| **题目校验** | 题干非空、选择题4选项、有标准答案、有解析、subject/kp 匹配目标 |
| **无 LLM** | `fallback_questions` 按题型返回模板题（含 LRU/Cache 等经典题） |
| **超时** | LLM 超时 60s → 自动走 fallback |
| **agent_steps 示例** | 7 步：分析状态→选择目标→检索上下文→生成→校验→保存→完成 |

---

## 批改 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/answer_check_agent.py` → `backend/agents/answer_graph.py` |
| **函数** | `check_answer(db, user_id, question_id, user_answer)` |
| **输入** | `{user_id, question_id, user_answer}` |
| **输出** | `{answer_record_id, is_correct, feedback, mastery, suggested_error_types[], agent_steps, llm_used, llm_error}` |
| **Graph 节点** | `load_question` → `check_objective_answer` → `llm_feedback` → `recommend_causes` → `update_answer_record` → `update_mastery` → `fallback_check` |
| **客观判分** | 选择题按答案首字母判定；填空/简答宽松字符串包含 |
| **错因推荐** | 固定 `["审题错误","计算错误"]` + `common_mistakes` 提取 1-2 个 + 最近高频错因 1 个 + LLM 提取 0-1 个 |
| **无 LLM** | `fallback_check` 提供模板反馈和固定错因 |
| **agent_steps 示例** | 7 步：加载题目→客观判分→LLM反馈→推荐错因→更新记录→更新掌握度→完成 |

---

## 错题分析 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/mistake_agent.py` → `backend/agents/mistake_graph.py` |
| **函数** | `confirm_cause(db, user_id, answer_record_id, error_types, user_note, evidence_source)` |
| **输入** | `{user_id, answer_record_id, error_types, user_note, evidence_source}` |
| **输出** | `{mistake_id, message, mastery_status, weak_score, agent_steps, llm_used, llm_error}` |
| **Graph 节点** | `load_answer_record` → `analyze_error` → `write_mistake` → `write_memory` → `write_chroma_summary` → `recommend_retrain` |
| **无 LLM** | `analyze_error` 使用 fallback dict，错因/建议走模板 |
| **无 ChromaDB** | `write_chroma_summary` 标记 `stored=false`，不阻塞写入流程 |
| **额外函数** | `analyze_ocr_text(db, user_id, text, subject, knowledge_point, user_answer)` — OCR 文本分析，返回 `{mistake_id, memory_id, analysis, llm_used, llm_error}` |
| **agent_steps 示例** | 6 步：加载记录→分析错因→写错题→写记忆→写向量→推荐复练 |

---

## 论坛 AI Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/forum_agent.py` |
| **函数** | `ai_answer_for_post(title, content, subject, knowledge_point="", author_profile=None)` |
| **输入** | `{title, content, subject, knowledge_point?, author_profile:{mastery_status, recent_memories, common_errors}?}` |
| **输出** | `{answer(HTML), agent_steps, llm_used, llm_error}` |
| **无 LLM** | 返回结构化模板回答（含问题定位+建议+核心思路） |
| **个性化** | `author_profile` 提供掌握度+近期记忆+常见错因，LLM 结合画像回答 |
| **agent_steps 示例** | 2 步：解析帖子→生成回答 |

---

## 报告 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/report_agent.py` |
| **函数** | `generate_report(db, user_id)` |
| **输入** | `{user_id}` |
| **输出** | `{id, title, summary, weak_points, main_error_type, qa_focus, forum_focus, video_suggestion, plan[], memories[], agent_steps, llm_used, llm_error}` |
| **无 LLM** | 基于数据库真实聚合的模板报告（累计答题/正确数/薄弱点） |
| **plan 格式** | `[{step, subject, knowledge_point, action, count, difficulty, estimated_minutes, reason}]` |
| **agent_steps 示例** | 2 步：采集数据→生成报告 |

---

## 智能提示 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/hint_agent.py` |
| **函数** | `generate_hints(mastery_status, subject, knowledge_point, question_text, standard_answer="", explanation="")` |
| **输入** | `{mastery_status, subject, knowledge_point, question_text, standard_answer?, explanation?}` |
| **输出** | `{mode(label), hints[], agent_steps, llm_used, llm_error, duration_ms}` |
| **掌握度模式** | 薄弱点→详细引导, 不熟→适中提示, 不会/未学→教学模式, 掌握→验证模式 |
| **无 LLM** | 按掌握度返回 3-5 条分级模板提示 |
| **agent_steps 示例** | 2 步：识别模式→生成提示 |

---

## 每日计划 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/plan_agent.py` |
| **函数** | `generate_daily_plan(recent_answers, recent_mistakes, recent_memories, weak_points=None)` |
| **输入** | `{recent_answers[], recent_mistakes[], recent_memories[], weak_points[]?}` |
| **输出** | `{plan[], agent_steps, llm_used, llm_error, duration_ms}` |
| **plan 格式** | `[{step, subject, knowledge_point, action, count, difficulty, estimated_minutes, reason}]` |
| **无 LLM** | 返回 2 步模板计划（操作系统+计算机网络） |
| **agent_steps 示例** | 2 步：采集数据→生成计划 |

---

## 会话摘要 Agent

| 项目 | 内容 |
|------|------|
| **文件** | `backend/agents/summary_agent.py` |
| **函数** | `generate_conversation_summary(messages)` |
| **输入** | `{messages[{role, content}]}`（取最近 8 条） |
| **输出** | `{title, summary, followup_suggestions[3], agent_steps, llm_used, llm_error, duration_ms}` |
| **无 LLM** | 返回模板摘要 "408 问答" + 3 条通用追问建议 |
| **空消息** | 返回 "空白会话" + `["开始 408 学习提问吧"]` |
| **agent_steps 示例** | 2 步：校验输入→生成摘要 |

---

## 降级策略汇总

| 场景 | 行为 | 不出现的情况 |
|------|------|-------------|
| **无 LLM** (API Key 无效/网络超时) | 各 Agent 返回模板/聚合数据，`llm_used=false`，`agent_steps` 标记 degraded | 不抛 500，不返回空字符串 |
| **无 ChromaDB** (未安装/路径无效) | `chroma_service.enabled=false`，RAG 走 MySQL 关键词或空数组 | 不抛 500，`query_documents` 返回 `items=[]` |
| **视频爬虫失败** (B站 API 不可用) | 返回已有视频数据或空列表，`crawl_triggered=false` | 不影响视频接口 |
| **OCR 不可用** (PaddleOCR 未安装) | `ocr_available=false`，用户可手动输入或校正 | 不阻塞页面流程 |
| **数据为空** | 返回空数组/空字符串 + `agent_steps` 说明 | 不返回 `null` 或抛异常 |
