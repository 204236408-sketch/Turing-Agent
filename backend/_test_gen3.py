"""直接看后端 HTTP 返回的 raw body"""
import json
import requests

r = requests.post('http://127.0.0.1:8000/api/auth/login',
                  json={'account': 'demo@turing408.ai', 'password': '123456'},
                  timeout=10)
token = r.json().get('data', {}).get('access_token')
H = {'Authorization': f'Bearer {token}'}

# OCR 错题后
r = requests.post('http://127.0.0.1:8000/api/questions/generate', headers=H, json={
    'mode': '自由选择',
    'subject': '计算机组成原理',
    'knowledge_point': '指令集体系结构',
    'difficulty': '中等',
    'question_type': '选择题',
    'count': 3,
    'reference_text': '下列哪一项不属于影响指令字长的 ISA 特性? A.是否采用定长指令字格式 B.是否采用微程序控制器 C.是否采用单总线数据通路 D.是否采用 RISC 架构',
    'reference_answer': 'B.是否采用微程序控制器',
    'source': 'ocr',
}, timeout=180)

print('HTTP', r.status_code)
print('=== raw body ===')
print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:3000])
