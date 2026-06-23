# API 契约清单

依据技术方案优先冻结：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/home/overview`
- `GET /api/knowledge/graph`
- `GET /api/mastery/list`
- `GET /api/mastery/summary`
- `POST /api/qa/chat`
- `POST /api/questions/generate`
- `POST /api/answers/check`
- `POST /api/mistakes/cause-confirm`
- `GET /api/mistakes`
- `POST /api/ocr/upload`
- `POST /api/ocr/analyze`
- `POST /api/mistakes/analyze`
- `GET /api/reports/overview`
- `POST /api/reports/generate`
- `GET /api/forum/posts`
- `POST /api/forum/posts`
- `POST /api/forum/posts/{id}/comments`
- `POST /api/forum/posts/{id}/ai-answer`
- `POST /api/forum/posts/{id}/ai-followup`

统一响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
