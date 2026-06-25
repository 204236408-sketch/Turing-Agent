# PDF 技术方案差距审计报告

审计对象：当前项目实现 vs《Rebirth of Turing - Web AI Agent System for 408 Exam》PDF 技术方案。

结论：当前项目已经具备 FastAPI 后端、原生前端、基础登录、首页、问答、出题、批改、错题、OCR、论坛、报告等可演示闭环，但整体仍偏“本地演示版”。PDF 中要求的真实 MySQL 生产链路、ChromaDB 向量库、LangChain/LangGraph Agent 编排、完整知识库/RAG、视频爬虫、完整数据资源、严格掌握度规则、去 Mock 前端和完整验收还没有全部落地。

## 1. Agent 框架与流程编排

PDF 要求：

- 使用 LangChain 连接知识库检索、大模型调用、Prompt 和输出解析。
- 使用 LangGraph 管理问答、出题、批改、错题分析等 Agent 流程。
- agents 目录保存不同 Agent 的流程编排代码。

当前实现：

- `backend/agents/*.py` 是自定义轻量 Python 函数。
- `backend/services/llm_service.py` 直接用 `urllib.request` 调硅基流动 OpenAI 兼容接口。
- `backend/requirements.txt` 中没有 `langchain`、`langgraph`、`langchain-openai`、`langchain-community`。

差距：

- 目前不是基于 LangChain/LangGraph 的标准 Agent 工作流。
- `agent_steps` 多为手写描述，不是由图节点执行记录自然生成。
- 出题、批改、错题分析之间没有统一状态图编排。

建议：

- P3 主负责，先接入 QA + RAG 的 LangGraph 流程。
- 第二步接智能出题和批改。
- 保持现有接口 JSON 不变，由 P1 做适配，P5 增加无 LLM、无 ChromaDB、节点失败测试。

## 2. RAG 与 ChromaDB

PDF 要求：

- MySQL 保存业务数据，ChromaDB 保存 408 知识库、用户记忆、错题摘要。
- `rag_service.py` 负责 ChromaDB 检索增强生成。
- `chroma_service.py` 负责 ChromaDB Collection 初始化、写入、查询和重建。
- 脚本 `import_knowledge_to_chroma.py` 将 408 知识点导入 ChromaDB。

当前实现：

- `backend/services/chroma_service.py` 返回 `enabled: False`，模式是 `local-placeholder`。
- `upsert_document()` 只返回预览，`stored: False`，没有真实写入。
- `backend/services/rag_service.py` 只做关键词和硬编码规则匹配。
- 当前没有 `backend/data/knowledge_docs/`，没有 Markdown 知识库文档。

差距：

- 没有真实 ChromaDB Collection。
- 没有 embedding、chunk、向量写入、向量检索。
- 问答和智能出题没有真正检索 PDF 要求的 `knowledge_base_408`。
- 用户记忆也没有写入 `user_memory_vector`。

建议：

- P2 提供至少 20 份知识库 Markdown 文档。
- P3 实现 ChromaDB collection：`knowledge_base_408`、`user_memory_vector`、`mistake_summary`。
- P3 实现导入、重建、查询和降级检索。
- P5 测试 ChromaDB 可用和不可用两种情况。

## 3. 数据资源完整度

PDF 要求：

- 408 四科完整知识结构。
- 至少覆盖较完整的知识点、题库、视频、知识库文档。
- 首页知识图谱、智能推荐、RAG、报告都依赖真实数据。

当前实现：

- `backend/services/seed_service.py` 内置 4 科和 20 多个简化知识点。
- `backend/data/seed_knowledge_points.json` 只有 3 个知识点。
- `backend/data/seed_questions.json` 只有 1 道题。
- `backend/data/seed_video_resources.json` 只有 1 条视频。
- 没有 `backend/data/knowledge_docs/`。

差距：

- 数据量远低于 PDF 和五人分工方案要求。
- 智能推荐、报告、RAG 很容易变成围绕少数演示点的固定结果。
- 前端知识图谱仍有大量静态结构。

建议：

- P2 补齐 408 四科知识点、题库、视频资源和知识库 Markdown。
- P1/P3/P4 不应再依赖少量固定演示数据证明真实能力。

## 4. MySQL 生产数据库

PDF 要求：

- 业务数据库使用 MySQL。
- `database.py` 负责 MySQL 连接。
- 部署时 Nginx + 后端 + MySQL 形成云端服务。

当前实现：

- 默认使用 SQLite。
- `.env.example` 里 MySQL 是注释示例。
- `deploy/docker-compose.yml` 只有 backend 服务，环境变量仍是 SQLite。
- 当前没有可用的 MySQL service、迁移脚本、备份脚本。

差距：

- 还不是 PDF 中的 MySQL 生产形态。
- SQLite 到 MySQL 迁移、云端导入、备份没有落地。

建议：

- P1/P2 增加 MySQL compose、迁移脚本、备份脚本。
- P5 做 MySQL 空库导入和后端重启数据不丢测试。

## 5. 知识问答 Agent

PDF 要求：

- 支持连续追问。
- 自动识别科目和知识点。
- 从 ChromaDB 检索 408 知识。
- 读取最近 5-10 条 conversation_message。
- 读取 user_memory、knowledge_mastery。
- 生成结构化回答。
- 写入问答记录，可转智能出题。

当前实现：

- `qa_agent.py` 会读取简化知识检索和用户记忆。
- 没有读取最近 5-10 条历史消息作为上下文。
- 没有读取 `knowledge_mastery` 后参与回答。
- 没有真实 ChromaDB 检索。
- 回答主体是 HTML 字符串，不是 PDF 示例那种完整结构化对象。

差距：

- “连续追问”和“结构化 Agent 回答”不充分。
- RAG 是简化关键词检索。
- LangChain/LangGraph 未接入。

建议：

- P3 用 LangGraph 改造 QA 链路：意图识别 -> 检索知识 -> 读取记忆 -> 读取掌握状态 -> 生成回答 -> 校验 -> fallback。
- P4 展示检索来源、Agent 步骤、追问建议。

## 6. 智能出题 Agent

PDF 要求：

- 自由选择出题和智能推荐出题。
- 智能推荐来源包括 `knowledge_mastery`、`mistake`、`qa_record`、`user_memory`。
- 检索 ChromaDB 408 知识库。
- 大模型生成题目并保存 session/question。
- 包含薄弱点强化、最近错题复练、高频提问专项、已掌握知识点复测、四科综合。

当前实现：

- `question_agent.py` 能调用 LLM 生成题目，也有 fallback。
- `recommendation_service.py` 有推荐逻辑，但主要基于当前数据库简化数据。
- 没有 `qa_record` 表，只有 conversation 记录。
- 没有 ChromaDB 检索。
- 出题校验较弱，主要检查题干是否包含目标关键词。

差距：

- 智能推荐没有完整使用 PDF 要求的数据源。
- 高频提问专项依赖 `qa_record` 的逻辑未实现。
- 生成题目的质量校验、去重、保存策略仍简化。

建议：

- P3/P1 明确推荐模式和数据来源。
- P3 引入 LangGraph 出题流程：分析用户状态 -> 选知识点 -> 检索上下文 -> 生成 -> 校验 -> 保存 -> fallback。

## 7. 答题批改 Agent

PDF 要求：

- 判断答案、给出反馈、推荐错因、写入答题记录。
- 批改结果后要触发掌握度变化、错题确认和后续训练。

当前实现：

- 选择题只按标准答案首字母判定。
- 填空/简答用宽松字符串包含判断。
- LLM 只生成反馈和候选错因。
- 没有基于题型的严格评分 rubrics。
- 没有 LangGraph 串联“批改 -> 错因 -> 掌握度 -> 错题本”的完整状态图。

差距：

- 批改能力仍偏简单。
- 推荐错因与知识点掌握、历史错题、RAG 结合不充分。

建议：

- P3 为选择题、填空题、简答题、综合题分别设计批改节点。
- P5 补不同题型的批改测试。

## 8. 掌握 / 不熟 / 不会 / 薄弱点规则

PDF 要求：

- 状态包括未学、掌握、不熟、不会、薄弱点。
- `weak_score` 来自 wrong_count、不熟次数、不会次数、OCR 错题、AI 错因、QA、论坛、正确次数、掌握次数。
- 最终优先级：未学只在无行为时成立；薄弱点 > 不会 > 不熟 > 掌握。
- 点击“不熟”进入不熟题本；点击“不会”进入不会题本；点击“掌握”从题本移出。

当前实现：

- `mastery_service.py` 已实现一版 weak_score 和 final_status。
- 但 `elif mastery.user_mark_status == "不会"` 放在薄弱点判断前，会让手动“不会”优先于薄弱点。
- OCR 分析里先 `user_mark_status = "不会"`，但没有清晰题本状态和知识点状态分离。
- 题本由 `Mistake.mastery_status` 查询，和 `KnowledgeMastery.final_status` 是两套状态。

差距：

- PDF 的优先级未严格遵守。
- “题本状态”和“知识点掌握状态”边界不够清晰。
- 不会题本规则如果完全按 PDF 可能过重：一次点击不会就长期停留，缺少复练后移出/降级规则。

更合理建议：

- 题本规则按“题目级最新状态”管理：`Mistake.mastery_status` 或最新 `AnswerRecord.mastery_feedback` 决定是否在不熟/不会题本。
- 知识点状态按聚合规则管理：`KnowledgeMastery.final_status` 决定知识图谱颜色。
- 点击“掌握”应把对应 mistake 从不熟/不会题本移出或标记 resolved。
- 复练答对 2 次可从“不会”降为“不熟”，连续答对 3 次可移出题本。
- “薄弱点”不应是一个题本，而应是知识点级高风险标签。

## 9. OCR 与错题分析

PDF 要求：

- PaddleOCR 识别题目文字。
- 错题分析 Agent 生成错因分析、复习建议、同类训练建议。
- 写入 MySQL mistake、user_memory。
- 写入 ChromaDB mistake_summary。

当前实现：

- `ocr_service.py` 会尝试 PaddleOCR，失败后 fallback。
- `mistake_agent.py` 能写入 mistake 和 user_memory。
- 没有写入 ChromaDB mistake_summary。
- 没有 OCR 结果人工校正后的结构化题目入库。

差距：

- OCR 到 ChromaDB 的记忆链路缺失。
- OCR 错题重复检测和同类训练建议不完整。

建议：

- P3 补 `mistake_summary` 向量写入。
- P1/P4 补 OCR 校正后保存为题目/错题的接口和页面状态。

## 10. 视频推荐与爬虫

PDF 要求：

- 视频推荐、手动爬取、点击统计。
- 视频爬虫搜索、解析、评分、入库、限流。
- 题目详情根据 subject + knowledge_point 推荐视频。

当前实现：

- `video_router.py` 只返回本地 `VideoResource`。
- `/api/videos/crawl` 返回“开发版不爬取外站”。
- `question_router.py` 的题目视频只按 subject 查询，没有按 knowledge_point 精准过滤。
- 没有 `video_crawler_service.py` 和 `crawl_videos.py`。

差距：

- 没有真实爬虫、评分、去重、限流、入库。
- 题目视频推荐粒度不足。

建议：

- P3 实现视频爬虫服务和评分。
- P1 修改题目视频接口为 subject + knowledge_point 优先，空数据再同科目 fallback。

## 11. 前端去 Mock 与真实化

PDF 要求：

- 前端保留 version-b 风格，但后续接口替换 Mock。
- 核心区域应来自真实接口。

当前实现：

- `app.js` 顶部仍有本地 demo 题。
- 首页、知识图谱、部分统计、前端 fallback 仍有固定值。
- 批改失败时会展示本地模拟批改。
- 页面中还有“本地演示题无法写入后端”等分支。

差距：

- 还没有完成去 Mock。
- 用户可能看到看似真实但实际是 fallback 的数据。

建议：

- P4 输出 Mock 替换清单并逐项替换。
- 接口失败时显示空状态/错误提示，不再展示固定假数据冒充真实数据。

## 12. 论坛 AI 与个性化

PDF 要求：

- 论坛 AI 小助手结合帖子分析、评论上下文和用户画像回答。
- 论坛行为进入长期记忆和掌握状态。

当前实现：

- `forum_agent.py` 只根据标题、内容、科目、知识点生成回答。
- 没有明显读取用户画像、历史评论上下文。
- forum_count 会参与 weak_score，但论坛内容语义没有进入 ChromaDB 或 user_memory。

差距：

- 论坛 AI 个性化较弱。
- 论坛与长期记忆/知识掌握的联动还浅。

建议：

- P3 扩展论坛 Agent 输入：用户画像、近期弱点、帖子评论上下文。
- P1/P5 增加论坛 AI 个性化测试。

## 13. 学习报告

PDF 要求：

- 统计答题、错题、论坛、知识点掌握状态和长期记忆。
- 生成学习报告和复习计划。

当前实现：

- `report_agent.py` 已聚合 answer_record、mistake、user_memory、knowledge_mastery。
- `forum_focus` 大多是 LLM 推断或 fallback，并没有真实统计论坛行为。
- 报告导出以浏览器打印为主，未见后端 PDF 文件生成。

差距：

- 报告部分实现了基础能力，但论坛、视频、趋势图和导出仍简化。

建议：

- P1/P3 补论坛统计、视频建议来源、报告导出文件。
- P4 报告页面全部改为真实数据。

## 14. 测试与验收

PDF 要求：

- 自动化测试、接口验收、页面验收、部署验收、最终清单。
- 测试外部服务不可用时的 fallback。

当前实现：

- 已有 `tests/test_*.py`，覆盖部分核心接口。
- 没有看到 `docs/验收清单.md`。
- 缺 ChromaDB、LangGraph、MySQL、视频爬虫、真实 RAG 的测试。

差距：

- 当前测试适合演示版，不足以证明 PDF 完整方案落地。

建议：

- P5 增加真实 RAG、无 ChromaDB、无 LLM、MySQL 迁移、视频爬虫失败、前端去 Mock 验收。

## 优先级建议

第一优先级：

1. P2 补完整数据资源和知识库 Markdown。
2. P3 接入 ChromaDB 和 QA + RAG 的 LangChain/LangGraph。
3. P4 去除核心 Mock，确保页面数据来自后端。

第二优先级：

1. P3 改造智能出题和批改为 LangGraph 流程。
2. P1/P2 完成 MySQL compose、迁移、备份。
3. P1/P3 完成错题相似检索和题本规则修正。

第三优先级：

1. 视频爬虫与定时任务。
2. 论坛 AI 个性化。
3. 后端报告文件导出。

## 最终判断

当前项目是“可运行演示版 + 部分深化功能”，不是 PDF 中“完整真实 Agent 系统”的严格落地版。

如果要严格对齐 PDF，核心补齐点是：

- LangChain/LangGraph Agent 编排。
- 真实 ChromaDB/RAG。
- 完整 408 知识库、题库、视频和知识库文档。
- MySQL 生产链路。
- 去 Mock 前端。
- 视频爬虫。
- 不熟/不会/薄弱点规则的题目级与知识点级分离。
- 完整验收清单和降级测试。
