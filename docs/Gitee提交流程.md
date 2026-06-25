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

<<<<<<< HEAD
### 7.1 本地 rebase 冲突怎么解

出现冲突时，终端通常会提示哪些文件冲突。按下面流程做：

```powershell
git status --short
```

冲突文件里会出现类似内容：

```text
<<<<<<< HEAD
当前分支内容
=======
远端内容
>>>>>>> 分支名或提交号
```

处理步骤：

1. 找到冲突文件负责人一起看。
2. 保留正确内容，删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记。
3. 保存文件。
4. 跑相关测试或手工流程。
5. 标记冲突已解决。

```powershell
git add 冲突文件
git rebase --continue
```

如果发现自己不知道怎么合，立即中止，不要硬猜：

```powershell
git rebase --abort
```

### 7.2 推送被拒绝怎么处理

如果 `git push` 提示远端有新提交：

```powershell
git pull --rebase origin master
```

没有冲突时，再推送：

```powershell
git push origin master
```

有冲突时，按 7.1 处理。

### 7.3 Gitee 合并请求有冲突怎么处理

如果 Gitee 页面提示“存在冲突，无法自动合并”：

1. 不要关闭合并请求。
2. 本地切回自己的分支。
3. 拉取最新 `master` 并 rebase。

```powershell
git checkout 自己的分支
git fetch origin
git rebase origin/master
```

4. 解决冲突后推送自己的分支。

```powershell
git push origin 自己的分支
```

如果 Gitee 要求强制推送，先问组长。普通成员不要直接使用 `git push --force`。确实需要时，只能对自己的个人分支使用：

```powershell
git push --force-with-lease origin 自己的分支
```

禁止对 `master` 强推。

### 7.4 文档冲突怎么解

文档冲突按“谁维护谁主导”：

| 文档 | 主导人 | 处理原则 |
|---|---|---|
| `docs/接口文档.md` | P1 | 保留最新接口契约，旧字段移到变更记录 |
| `docs/验收清单.md` | P5 | 保留所有失败项，不删除别人记录的问题 |
| `docs/前端Mock替换清单.md` | P4 | 保留已接/未接状态，状态冲突找 P5 确认 |
| `docs/数据验收表.md` | P2 | 以最新导入结果为准，旧数量写入备注 |
| `docs/Agent流程说明.md` | P3 | 以当前代码返回结构为准 |

文档冲突解决后，也要在上传通知里说明：

```text
冲突文件：
解决方式：
已确认人：
是否需要重新验收：
```

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
