"""重新分析 _all_kp.txt 中的 BAD 案例（修复版）"""
import re

with open("c:/Users/Sophia/Desktop/turing/backend/_all_kp.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 用一个明确的行起始标志切分
lines = content.split("\n")
issues = []
current = None
for line in lines:
    m = re.match(r"\[(.+?)\] '(.+?)' \(kp_name='(.+?)'\)", line)
    if m:
        if current:
            issues.append(current)
        subject, section, name = m.group(1), m.group(2), m.group(3)
        current = {
            "subject": subject, "section": section, "name": name,
            "is_bad": False, "top1": None, "missing": [],
        }
        continue
    if current is None:
        continue
    if "[BAD]" in line:
        current["is_bad"] = True
    elif "Top1:" in line:
        m2 = re.search(r"Top1: score=([\d.]+) kp=\[(.+?)\]", line)
        if m2:
            current["top1"] = (float(m2.group(1)), m2.group(2))
    elif "漏掉的高分匹配" in line:
        current["expect_missing"] = True
    elif current.get("expect_missing"):
        m3 = re.search(r"score=(\d+).*kp=\[(.+?)\]", line)
        if m3:
            current["missing"].append((int(m3.group(1)), m3.group(2)))
if current:
    issues.append(current)

bad_count = sum(1 for i in issues if i["is_bad"])
missing_count = sum(1 for i in issues if i["missing"])
print(f"总 KP: {len(issues)}, BAD: {bad_count}, 漏掉强匹配: {missing_count}")

# 按 subject 统计
from collections import defaultdict
by_subject = defaultdict(lambda: {"total": 0, "bad": 0, "missing": 0})
for i in issues:
    by_subject[i["subject"]]["total"] += 1
    if i["is_bad"]:
        by_subject[i["subject"]]["bad"] += 1
    if i["missing"]:
        by_subject[i["subject"]]["missing"] += 1

print("\n按科目统计：")
for s, c in sorted(by_subject.items()):
    print(f"  {s}: 总={c['total']}, BAD={c['bad']}, 漏强={c['missing']}")

print("\n" + "=" * 80)
print("BAD 案例分类（按 (subject, section) 分组）：")
from collections import Counter
patterns = Counter()
for i in issues:
    if i["is_bad"]:
        # 简化: 找 section 模式
        key = f"{i['subject']} / {i['section']}"
        patterns[key] += 1

# 展示高频问题
for (k, c) in patterns.most_common(40):
    print(f"  ({c}次) {k}")
