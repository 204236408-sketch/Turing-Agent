# Agent 流程说明

> P3 维护，P1/P4/P5 按此接接口、展示步骤和写测试。

## 统一返回字段

| 字段 | 类型 | 含义 | 为空时 |
|---|---|---|---|
| `agent_steps` | array | Agent 每一步执行摘要 | `[]` |
| `llm_used` | boolean | 是否调用 LLM | `false` |
| `llm_error` | string | LLM 错误信息 | `""` |
| `fallback_used` | boolean | 是否使用降级逻辑 | `false` |

## Agent 清单

| Agent | 函数入口 | 输入 | 输出 | fallback |
|---|---|---|---|---|
| QA | 待填 | 待填 | 待填 | 待填 |
| 出题 | 待填 | 待填 | 待填 | 待填 |
| 批改 | 待填 | 待填 | 待填 | 待填 |
| 错题分析 | 待填 | 待填 | 待填 | 待填 |
| 论坛 AI | 待填 | 待填 | 待填 | 待填 |
| 报告计划 | 待填 | 待填 | 待填 | 待填 |

## 降级要求

- 无 LLM：返回结构完整，说明 `fallback_used=true`。
- 无 ChromaDB：走 MySQL 关键词或空结果，不抛 500。
- 数据为空：返回空数组和可理解原因。
