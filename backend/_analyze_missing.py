"""详细展示 '漏掉强匹配' 的案例"""
import re
with open("c:/Users/Sophia/Desktop/turing/backend/_all_kp.txt", "r", encoding="utf-8") as f:
    content = f.read()
lines = content.split("\n")
current = None
issues = []
for line in lines:
    m = re.match(r"\[(.+?)\] '(.+?)' \(kp_name='(.+?)'\)", line)
    if m:
        if current and current.get("missing"):
            issues.append(current)
        subject, section, name = m.group(1), m.group(2), m.group(3)
        current = {
            "subject": subject, "section": section, "name": name,
            "is_bad": False, "top1": None, "missing": [], "items": [],
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
    elif re.match(r"\s*#", line):
        m3 = re.search(r"#([\d.]+) kp=\[(.+?)\]", line)
        if m3:
            current["items"].append((float(m3.group(1)), m3.group(2)))
    elif "漏掉的高分匹配" in line:
        current["expect_missing"] = True
    elif current.get("expect_missing"):
        m4 = re.search(r"score=(\d+).*kp=\[(.+?)\]", line)
        if m4:
            current["missing"].append((int(m4.group(1)), m4.group(2)))
if current and current.get("missing"):
    issues.append(current)

print(f"漏掉强匹配的 KP 数: {len(issues)}\n")
for i in issues:
    print(f"  [{i['subject']}] {i['section']!r} (name={i['name']!r})")
    score, top1_kp = i["top1"] if i["top1"] else (0, "?")
    print(f"    Top1: score={score} kp=[{top1_kp}]")
    for s, kp in i["items"]:
        print(f"    返回: kp=[{kp}]")
    for s, kp in i["missing"]:
        print(f"    漏掉: score={s} kp=[{kp}]")
    print()
