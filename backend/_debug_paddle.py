from pathlib import Path
from services.ocr_service import _get_paddle_engine, _preprocess_image, _paddle_lines
import time

eng = _get_paddle_engine()
print('engine:', eng)
# 用真实图片测试
test_path = Path('uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg')
print('test image:', test_path.exists(), test_path)

t = time.time()
lines = _paddle_lines(eng, test_path)
print(f'_paddle_lines 耗时 {time.time()-t:.1f}s, 共 {len(lines)} 行')
for ln in lines:
    print(f"  - {ln['score']:.3f}  {ln['text'][:60]}")
