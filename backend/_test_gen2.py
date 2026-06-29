"""手动调用 generate_questions,看 LLM + 流水线输出"""
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('question_graph')

from database import SessionLocal
from agents.question_agent import generate_questions

t = time.time()
db = SessionLocal()
try:
    data = generate_questions(
        db, 1, '自由选择', '计算机组成原理', '指令集体系结构',
        '中等', '选择题', 3,
        reference_text='下列哪一项不属于影响指令字长的 ISA 特性? A.是否采用定长指令字格式 B.是否采用微程序控制器 C.是否采用单总线数据通路 D.是否采用 RISC 架构',
        reference_answer='B.是否采用微程序控制器(定长指令字格式 RISC 体系属于 ISA 范畴,而微程序控制器与单总线数据通路属于 CPU 实现,不影响指令字长)'
    )
    print('=== Result ===')
    print('session_id:', data.get('session_id'))
    print('questions count:', len(data.get('questions', [])))
    print('llm_used:', data.get('llm_used'))
    print('llm_error:', data.get('llm_error'))
    for q in data.get('questions', []):
        print(f'  Q: {q.get("question_text","")[:140]}')
        print(f'  A: {q.get("standard_answer")}')
    print('Agent Steps:')
    for s in data.get('agent_steps', []):
        print(f'  - {s["name"]}: {s["output_summary"][:160]}')
    print(f'Total: {time.time()-t:.1f}s')
finally:
    db.close()
