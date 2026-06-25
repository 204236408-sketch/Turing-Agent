# Gitee 提交流程

> 每个人每天完成自己的工作后，按这份流程上传。目标是：只上传自己负责的文件，不上传缓存和本地数据，尽量减少冲突。

当前仓库远程地址：

```text
origin https://gitee.com/qian-lupan/the-reborn-me-is-turing
```

当前主分支：

```text
master
```

## 1. 每天开始前先同步

```powershell
git checkout master
git pull --rebase origin master
```

如果这一步报冲突，先不要继续开发，找组长或对应文件负责人确认。

## 2. 推荐使用个人分支

每个人每天开自己的分支，格式：

```text
p角色-day天数-任务
```

示例：

```powershell
git checkout -b p1-day2-home-api
git checkout -b p2-day3-question-data
git checkout -b p3-day2-rag
git checkout -b p4-day3-question-page
git checkout -b p5-day4-video-tests
```

做完后推到 Gitee：

```powershell
git push -u origin 分支名
```

然后在 Gitee 上发起合并请求，由组长合并到 `master`。

## 3. 如果必须直接提交到 master

只有组长允许时才直接提交 `master`。步骤如下：

```powershell
git checkout master
git pull --rebase origin master
git status --short
```

只添加自己负责的文件，不要使用 `git add .`。

示例：

```powershell
git add backend/routers/question_router.py docs/接口文档.md
git commit -m "P1 Day3: 完善出题和批改接口"
git pull --rebase origin master
git push origin master
```

## 4. 每个角色只提交自己的范围

| 角色 | 通常提交 | 不要随便提交 |
|---|---|---|
| P1 | `backend/routers/`、`backend/schemas.py`、`backend/config.py`、`deploy/`、`docs/接口文档.md` | P2 数据文件、P4 页面大改 |
| P2 | `database/`、`backend/models.py`、`backend/data/`、`backend/scripts/seed_data.py`、`docs/数据验收表.md` | P3 Agent 逻辑、P4 页面 |
| P3 | `backend/agents/`、`backend/services/chroma_service.py`、`backend/services/rag_service.py`、`backend/services/video_crawler_service.py`、`docs/Agent流程说明.md`、`docs/RAG知识库说明.md` | P1 路由契约、P4 页面 |
| P4 | `frontend/`、根目录前端入口文件、`docs/前端Mock替换清单.md`、`docs/前端验收记录.md` | 后端模型、数据库脚本 |
| P5 | `tests/`、`docs/验收清单.md`、`docs/上线风险清单.md`、`docs/前端验收记录.md` | 业务代码大改，除非修测试夹具 |

## 5. 提交前必须检查

```powershell
git status --short
```

不要提交这些文件：

```text
__pycache__/
*.pyc
*.log
.env
*.db
tmp/
uploads/ocr_images/
backend/uploads/ocr_images/
backend/vector_store/
backend/outputs/
```

如果它们已经出现在 `git status`，不要 `git add` 它们。只添加明确要交付的文件路径。

## 6. 提交信息格式

```text
P角色 Day天数: 做了什么
```

示例：

```text
P1 Day2: 补首页和 QA 接口契约
P2 Day3: 扩充题库和错因样例
P3 Day2: 接入 RAG fallback
P4 Day3: 出题页接真实批改接口
P5 Day4: 增加视频和论坛验收测试
```

## 7. 冲突处理规则

如果 `git pull --rebase` 或推送时报冲突：

1. 先停止继续改代码。
2. 用 `git status --short` 看冲突文件。
3. 找该文件当天负责人一起处理。
4. 只解决自己理解的冲突，不猜别人逻辑。
5. 解决后跑相关测试或手工流程。
6. 在提交说明里写清“解决了哪个文件冲突”。

常见冲突归属：

| 文件 | 优先处理人 |
|---|---|
| `backend/models.py`、`database/schema.sql` | P2 + P1 |
| `backend/routers/*.py` | P1 |
| `backend/agents/*.py`、`backend/services/rag_service.py` | P3 |
| `frontend/app.js`、`frontend/styles.css` | P4 |
| `tests/*.py`、`docs/验收清单.md` | P5 |
| `docs/接口文档.md` | P1 + 相关接口使用者 |

## 8. 每晚上传顺序

为了减少冲突，每晚按这个顺序上传：

1. P2 先上传表结构和数据样例。
2. P3 再上传 Agent/RAG/爬虫。
3. P1 再上传接口和部署配置。
4. P4 再上传页面接入。
5. P5 最后上传测试和验收清单。

如果某个人当天没有完成，也要在群里说明“今天不上传”或“只上传文档/样例”，避免下游一直等。

## 9. 上传后通知格式

```text
角色：
分支：
提交号：
主要文件：
下游需要看：
是否影响接口/字段：
是否需要 P5 重新验收：
```
