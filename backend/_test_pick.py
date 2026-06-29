from agents.question_graph import _pick_seed_questions, _normalize_kp, _build_fallback

# 直接测试 _pick_seed_questions 修复后的行为
print("=== 测试 _pick_seed_questions(归一化后) ===")
for kp in ["指令集体系结构(ISA)", "指令集体系结构", "指令系统"]:
    picked = _pick_seed_questions("计算机组成原理", kp, "choice", 3)
    print(f"  KP='{kp}' → 抽到 {len(picked)} 道题")
    for it in picked:
        print(f"    {it.get('knowledge_point')}: {it.get('question_text','')[:80]}")

print("\n=== 测试 _build_fallback ===")
fb = _build_fallback("choice", "计算机组成原理", "指令集体系结构(ISA)", 3)
print(f"  fallback 共 {len(fb)} 道")
for it in fb:
    print(f"    source={it.get('source')}: {it.get('question_text','')[:100]}")
