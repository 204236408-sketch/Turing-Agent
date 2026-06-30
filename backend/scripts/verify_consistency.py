"""一次性 e2e 校验脚本：对比首页图谱与知识点导航页在同一用户下，章节状态/百分比是否一致。"""
import json
from pathlib import Path

home = json.loads(Path("c:/Users/Sophia/Desktop/turing/_qa_shots/home_overview_after.json").read_text(encoding="utf-8"))
subject = json.loads(Path("c:/Users/Sophia/Desktop/turing/_qa_shots/subject_graph_after.json").read_text(encoding="utf-8"))

home_data = home.get("data", home)
subj_data = subject.get("data", subject)

kg = home_data.get("knowledge_graph", home_data)
print("home 顶层 keys:", list(home_data.keys())[:20])
print("kg 顶层 keys:", list(kg.keys()))

# 提取首页 数据结构 章节
home_chapters = {}
for item in (kg.get("subjects", {}) or {}).get("数据结构", []):
    home_chapters[item["name"]] = {
        "status": item["status"],
        "mastery_percent": item.get("mastery_percent", -1),
        "knowledge_count": item.get("knowledge_count", -1),
    }

# 提取导航页 数据结构 章节
subj_chapters = {}
for ch in subj_data.get("chapters", []):
    subj_chapters[ch["name"]] = {
        "status": ch["status"],
        "mastery_percent": ch.get("mastery_percent", -1),
        "knowledge_count": ch.get("knowledge_count", -1),
    }

all_keys = set(home_chapters) | set(subj_chapters)
mismatches = []
for k in sorted(all_keys):
    h = home_chapters.get(k)
    s = subj_chapters.get(k)
    line = f"{k!r}: home={h} | nav={s}"
    if h and s:
        if h["status"] != s["status"] or h["mastery_percent"] != s["mastery_percent"] or h["knowledge_count"] != s["knowledge_count"]:
            mismatches.append(line)
    else:
        mismatches.append(line + " <-- 缺失")

print(f"home 章节数 = {len(home_chapters)} | nav 章节数 = {len(subj_chapters)}")
print(f"首页 summary: {kg.get('summary')}")
print(f"导航页 status_distribution: {subj_data.get('status_distribution')}")
if mismatches:
    print(f"差异共 {len(mismatches)} 条：")
    for m in mismatches[:30]:
        print(" -", m)
else:
    print("两套页面在 状态/百分比/知识点数 上完全一致")

