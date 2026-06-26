import os
import re
import json

# 1. 加载知识点JSON
with open("backend/data/seed_knowledge_points.json", "r", encoding="utf-8") as f:
    knowledge_points = json.load(f)

# 初始化空集合（修复：必须带()）
kp_name_set = set()
kp_section_set = set()
# 分开填充，不要嵌套add
for kp in knowledge_points:
    kp_name_set.add(kp["name"].strip())
    kp_section_set.add(kp["section"].strip())
# 合并两套合法标识：name细分小节 + section大章节
kp_all_valid = kp_name_set.union(kp_section_set)

subjects = {"数据结构", "计算机组成原理", "操作系统", "计算机网络"}

# 2. 校验目录
docs_dir = "backend/data/knowledge_docs"
errors = []
valid_docs = []

if not os.path.exists(docs_dir):
    errors.append(f"错误：目录不存在 {docs_dir}")
else:
    for filename in os.listdir(docs_dir):
        if not filename.endswith(".md"):
            continue
        pure_name = filename.replace(".md", "")
        name_parts = pure_name.split("_")
        if len(name_parts) < 2:
            errors.append(f"文件名格式错误：{filename}，规范：科目_章节名/小节名.md")
            continue
        
        doc_subject = "_".join(name_parts[:-1])
        doc_kp_identifier = name_parts[-1].strip()

        # 校验科目
        if doc_subject not in subjects:
            errors.append(f"科目非法：{filename}，合法科目：{subjects}")
        
        # 校验文件名知识点标识（section大章节 / name细分小节 均可）
        if doc_kp_identifier not in kp_all_valid:
            errors.append(
                f"知识点不存在：{filename}，标识「{doc_kp_identifier}」"
                f"不在json的section(大章节)、name(细分小节)中；"
                f"提示：section示例：线性表、树与二叉树；name示例：线性表的定义和基本操作"
            )
        
        # 读取文档头部字段
        file_path = os.path.join(docs_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            subject_match = re.search(r"subject: (.*)", content)
            kp_match = re.search(r"knowledge_point: (.*)", content)
            if not subject_match or not kp_match:
                errors.append(f"文档{filename}缺失subject/knowledge_point头部字段")
            else:
                doc_sub_content = subject_match.group(1).strip()
                doc_kp_content = kp_match.group(1).strip()
                # 校验文档内知识点字段
                if doc_kp_content not in kp_all_valid:
                    errors.append(
                        f"文档{filename}内部knowledge_point非法：「{doc_kp_content}」，"
                        f"只能使用json内section大章节 或 name细分小节"
                    )
                valid_docs.append({
                    "filename": filename,
                    "subject": doc_sub_content,
                    "knowledge_point": doc_kp_content,
                    "content": content
                })

# 3 输出结果
if errors:
    print("文档校验错误：")
    for err in errors:
        print(f"- {err}")
else:
    print(f"✅ 校验全部通过，有效文档数：{len(valid_docs)}")
    with open("backend/data/knowledge_docs_structured.json", "w", encoding="utf-8") as f:
        json.dump(valid_docs, f, ensure_ascii=False, indent=2)

# 调试打印：运行完查看所有合法section、排查匹配问题
print("\n===== 调试输出（核对json内所有大章节section）=====")
print("全部section集合：", sorted(kp_section_set))
print("\n全部细分name集合（前20条）：", list(kp_name_set)[:20])

