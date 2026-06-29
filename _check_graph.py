"""直接跑后端 run_forum_graph 看实际返回。"""
import sys
sys.path.insert(0, r'C:\Users\Sophia\Desktop\turing\backend')
from database import SessionLocal
from models import ForumPost, User
from agents.forum_agent import run_forum_graph, set_db
import json

db = SessionLocal()
# 找一个帖子
post = db.query(ForumPost).filter(ForumPost.is_deleted == False).first()
if not post:
    print("没有帖子")
    sys.exit(0)
print(f"测试帖子: id={post.id} title={post.title[:50]} content={post.content[:50]}")
# 找一个用户
user = db.query(User).first()
print(f"用户: id={user.id if user else None}")
# 跑 graph
set_db(db)
post_dict = {
    "id": post.id,
    "title": post.title,
    "content": post.content,
    "subject": post.subject or "",
    "knowledge_point": post.knowledge_point or "",
}
result = run_forum_graph(db=db, post=post_dict, user_id=user.id if user else 0)
print("=== result keys ===")
print(list(result.keys()))
print("=== answer ===")
print(json.dumps(result.get("answer", {}), ensure_ascii=False, indent=2)[:1000])
print("=== retrieval ===")
print(json.dumps(result.get("retrieval", {}), ensure_ascii=False, indent=2)[:500])
print("=== user_profile ===")
print(json.dumps(result.get("user_profile", {}), ensure_ascii=False, indent=2)[:500])
print("=== subject/kp ===")
print(f"subject={result.get('subject')}, kp={result.get('knowledge_point')}")
print("=== llm_used/llm_error ===")
print(f"used={result.get('llm_used')}, err={result.get('llm_error')}")
print("=== agent_steps ===")
for s in result.get("agent_steps", []):
    print(f"  [{s.get('status')}] {s.get('name')}: {s.get('output_summary','')[:100]}")
db.close()
