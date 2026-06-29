import sys
sys.path.insert(0, r'C:\Users\Sophia\Desktop\turing\backend')
from database import SessionLocal
from sqlalchemy import inspect
db = SessionLocal()
ins = inspect(db.bind)
for t in ['forum_ai_answer', 'forum_ai_answer_like', 'forum_ai_followup', 'forum_post', 'forum_comment', 'forum_like', 'forum_checkin']:
    print('---', t, '---')
    try:
        cols = ins.get_columns(t)
        for c in cols:
            print('  %-30s %s' % (c['name'], c['type']))
    except Exception as e:
        print('  ERROR:', e)
db.close()
