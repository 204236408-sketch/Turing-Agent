"""Debug: 验证 generate_answer_node 收到的 state。"""
import sys
sys.path.insert(0, r'C:\Users\Sophia\Desktop\turing\backend')
from database import SessionLocal
from models import ForumPost, User
from agents.forum_agent import (
    set_db, get_forum_graph,
    detect_intent_node, load_history_node, retrieve_knowledge_node,
    retrieve_memory_node, generate_answer_node, validate_answer_node,
)
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
print("initial post.title:", initial_state['post']['title'][:30])
print("initial post.subject:", initial_state['post']['subject'])
print()

# 跑 stream 看每步
graph = get_forum_graph()
final_state = dict(initial_state)
for update in graph.stream(initial_state):
    for node_name, node_updates in update.items():
        print(f"--- {node_name} ---")
        print(f"  输入 state.subject: {final_state.get('subject')}")
        print(f"  输入 state.kp: {final_state.get('knowledge_point')}")
        print(f"  输入 state.retrieval.grounded: {final_state.get('retrieval', {}).get('grounded')}")
        print(f"  返回 keys: {list(node_updates.keys())}")
        if 'answer' in node_updates:
            a = node_updates['answer']
            if isinstance(a, dict):
                print(f"  answer.subject_kp: {a.get('subject_kp')}")
                print(f"  answer.analysis[:80]: {a.get('analysis', '')[:80]}")
        # 累积
        final_state.update(node_updates)
        print(f"  累积后 state.subject: {final_state.get('subject')}")
        print(f"  累积后 state.kp: {final_state.get('knowledge_point')}")
        print()
db.close()
