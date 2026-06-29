"""Debug LangGraph stream 行为。"""
import sys
sys.path.insert(0, r'C:\Users\Sophia\Desktop\turing\backend')
from database import SessionLocal
from models import ForumPost, User
from agents.forum_agent import set_db, get_forum_graph
import json

db = SessionLocal()
post = db.query(ForumPost).filter(ForumPost.is_deleted == False).first()
user = db.query(User).first()
set_db(db)
initial_state = {
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
graph = get_forum_graph()
print('--- graph.stream ---')
for i, update in enumerate(graph.stream(initial_state)):
    print(f"step {i}: keys = {list(update.keys())}")
    for node_name, updates in update.items():
        print(f"  {node_name}: keys = {list(updates.keys()) if isinstance(updates, dict) else type(updates)}")
        if 'answer' in updates:
            a = updates['answer']
            print(f"    answer keys: {list(a.keys()) if isinstance(a, dict) else type(a)}")
print()
print('--- graph.invoke ---')
result = graph.invoke(initial_state)
print(f"result keys: {list(result.keys())}")
print(f"result.answer: {json.dumps(result.get('answer', {}), ensure_ascii=False)[:200]}")
print(f"result.subject: {result.get('subject')}")
db.close()
