from pathlib import Path
from pypdf import PdfReader
pdf = Path(r'C:\Users\Sophia\xwechat_files\wxid_i3ql5202z23o22_4a56\msg\file\2026-06\Rebirth of Turing- Web AI Agent System for 408 Exam(1).pdf')
reader = PdfReader(str(pdf))
print('PAGES', len(reader.pages))
text=[]
for i,p in enumerate(reader.pages):
    t=p.extract_text() or ''
    text.append(f'\n\n===== PAGE {i+1} =====\n{t}')
out=Path('tmp/pdf_rebirth_turing_extract.txt')
out.parent.mkdir(exist_ok=True)
out.write_text('\n'.join(text), encoding='utf-8')
print(out.resolve())
print(('\n'.join(text))[:16000])
