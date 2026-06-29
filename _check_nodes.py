"""Debug: 手动 invoke graph 看中间状态。"""
import sys
sys.path.insert(0, r'C:\Users\Sophia\Desktop\turing\backend')
from database import SessionLocal
from models import ForumPost, User
from agents.forum_agent import (
    set_db, get_forum_graph, _build_forum_graph,
    detect_intent_node, load_history_node, retrieve_knowledge_node,
    retrieve_memory_node, generate_answer_node, validate_answer_node,
)
import json

db = SessionLocal()
post = db.query(ForumPost).filter(ForumPost.is_deleted == False).first()
user = db.query(User).first()
print(f"post: {post.id} '{post.title[:40]}'")
set_db(db)
state = {
    "user_id": user.id,
    "post": {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "subject": post.subject or "",
        "knowledge_point": post.knowledge_point or "",
    },
    "followup_question": "",
    "answer_id": None,
    "agent_steps": [],
}

# 手动跑每个节点
for fn in [detect_intent_node, load_history_node, retrieve_knowledge_node, retrieve_memory_node, generate_answer_node, validate_answer_node]:
    name = fn.__name__
    updates = fn(state)
    print(f"--- {name} 返回 keys: {list(updates.keys())}")
    if 'answer' in updates:
        a = updates['answer']
        print(f"  answer keys: {list(a.keys()) if isinstance(a, dict) else type(a)}")
        if isinstance(a, dict) and 'analysis' in a:
            print(f"  analysis[:50]: {a['analysis'][:50]}")
    state.update(updates)
    print(f"  state.answer keys: {list(state.get('answer', {}).keys())}")
    print(f"  state.subject: {state.get('subject')}, kp: {state.get('knowledge_point')}")
    print(f"  state.retrieval.grounded: {state.get('retrieval', {}).get('grounded')}")

print()
print("=== final state.answer ===")
print(json.dumps(state.get("answer", {}), ensure_ascii=False, indent=2)[:500])
db.close()
