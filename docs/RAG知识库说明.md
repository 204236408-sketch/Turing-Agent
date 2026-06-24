# RAG 知识库说明

> P2/P3 共同维护。P2 负责文档内容，P3 负责入库和检索。

## Collection

| Collection | 内容 | 维护人 | 验收方式 |
|---|---|---|---|
| `knowledge_base_408` | 408 知识文档 | P2/P3 | 查询能返回来源 |
| `user_memory_vector` | 用户长期记忆 | P3 | 用户行为后可写入 |
| `mistake_summary` | 错题摘要 | P3 | 错因确认后可写入 |

## 文档格式

| 字段 | 含义 | 示例 |
|---|---|---|
| subject | 科目 | 操作系统 |
| knowledge_point | 知识点 | 页面置换算法 |
| title | 文档标题 | LRU 页面置换 |
| content | 正文 | 待填 |
| keywords | 关键词 | LRU,FIFO,缺页 |

## 每日验收

- 文档数量是否达到当天目标。
- 入库脚本是否能重复执行。
- 查询是否返回 `source/title/content/snippet`。
- Chroma 不可用时是否有 fallback。
