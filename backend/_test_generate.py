"""测试 /api/questions/generate 在 OCR 错题场景下是否返回非空题目。"""
import json
import requests

r = requests.post('http://127.0.0.1:8000/api/auth/login',
                  json={'account': 'demo@turing408.ai', 'password': '123456'},
                  timeout=10)
token = r.json().get('data', {}).get('access_token')
H = {'Authorization': f'Bearer {token}'}

# OCR 错题后,用户用 指令集体系结构(ISA) 调用
r = requests.post('http://127.0.0.1:8000/api/questions/generate', headers=H, json={
    'mode': '自由选择',
    'subject': '计算机组成原理',
    'knowledge_point': '指令集体系结构(ISA)',
    'difficulty': '中等',
    'question_type': '选择题',
    'count': 3,
}, timeout=180)
print('HTTP', r.status_code)
data = r.json()
print('keys:', list(data.keys()) if isinstance(data, dict) else 'not dict')
print('llm_used:', data.get('llm_used'))
questions = data.get('questions', [])
print('questions count:', len(questions) if isinstance(questions, list) else 'not list')
print('warning:', data.get('warning'))
print('config:', data.get('config'))
print('recommendation:', data.get('recommendation'))
print('error:', data.get('error'))
if questions:
    print('first q text:', (questions[0].get('question_text') or questions[0].get('title') or '')[:200])
