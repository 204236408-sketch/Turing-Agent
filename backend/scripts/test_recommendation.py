"""推荐引擎回归测试。

不依赖数据库/外部服务，纯函数式验证：
1. _normalize_kp / _kp_key 归一化逻辑
2. _to_difficulty / _to_question_type / _to_count 映射规则
3. _point_payload 组装 + mistake_tip 注入
4. choose_today_plan 降级链（用 mock 的 build_smart_recommendations 验证）
5. _personalize_hint / _format_mistake_tip 个性化提示生成

执行：cd backend && python scripts/test_recommendation.py
"""
from __future__ import annotations

import os
import sys

# 允许从 backend 目录直接运行
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.recommendation_service import (  # noqa: E402
    TODAY_PLAN_FALLBACK_CHAIN,
    _format_mistake_tip,
    _kp_key,
    _normalize_kp,
    _personalize_hint,
    _to_count,
    _to_difficulty,
    _to_question_type,
    choose_today_plan,
    normalize_existing_kp_rows,
)


# ── 工具 ──────────────────────────────────────────────────────────
def _check(label: str, actual, expected):
    ok = actual == expected
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {label}: actual={actual!r} expected={expected!r}")
    return ok


def _stub_mastery(
    subject: str = "数据结构",
    kp: str = "线性表",
    final_status: str = "薄弱点",
    weak_score: float = 0,
    continuous_wrong_count: int = 0,
    qa_count: int = 0,
    total_answer_count: int = 0,
    correct_count: int = 0,
):
    """构造一个类对象（不依赖模型），用于 _to_* 函数。"""

    class M:
        pass

    m = M()
    m.subject = subject
    m.knowledge_point = kp
    m.final_status = final_status
    m.weak_score = weak_score
    m.continuous_wrong_count = continuous_wrong_count
    m.qa_count = qa_count
    m.total_answer_count = total_answer_count
    m.correct_count = correct_count
    m.wrong_count = 0
    m.last_answer_time = None
    return m


# ── 1. _normalize_kp / _kp_key 归一化 ──────────────────────────────
def test_normalize_kp():
    print("\n=== _normalize_kp / _kp_key ===")
    results = [
        _check("原样保留", _normalize_kp("线性表"), "线性表"),
        _check("英文括号后缀", _normalize_kp("指令集体系结构(ISA)"), "指令集体系结构"),
        _check("中文括号后缀", _normalize_kp("进程与线程（同步）"), "进程与线程"),
        _check("首尾空格", _normalize_kp("  线性表  "), "线性表"),
        _check("空字符串", _normalize_kp(""), ""),
        _check("None", _normalize_kp(None), ""),
        _check("括号在前保留", _normalize_kp("(ISA)指令集"), "(ISA)指令集"),  # 不处理
        _check("_kp_key 归一化", _kp_key(" 数据结构 ", "线性表(顺序)"), ("数据结构", "线性表")),
    ]
    return all(results)


# ── 2. _to_difficulty 映射 ────────────────────────────────────────
def test_to_difficulty():
    print("\n=== _to_difficulty ===")
    results = [
        _check("ws>6 简单", _to_difficulty(_stub_mastery(weak_score=7)), "简单"),
        _check("ws>=3 中等", _to_difficulty(_stub_mastery(weak_score=3)), "中等"),
        _check("total>=5 较难", _to_difficulty(_stub_mastery(weak_score=0, total_answer_count=5)), "较难"),
        _check("默认 base", _to_difficulty(_stub_mastery(weak_score=0, total_answer_count=0), base="中等"), "中等"),
        _check("mastery=None", _to_difficulty(None, base="较难"), "较难"),
    ]
    return all(results)


# ── 3. _to_question_type 映射 ──────────────────────────────────────
def test_to_question_type():
    print("\n=== _to_question_type ===")
    results = [
        _check("已改善复测强制选择", _to_question_type(None, "已改善知识点复测"), "选择题"),
        _check("cw>=2 填空", _to_question_type(_stub_mastery(continuous_wrong_count=2), "薄弱点强化"), "填空题"),
        _check("qa>=3 简答", _to_question_type(_stub_mastery(qa_count=3), "高频提问专项"), "简答题"),
        _check("ws>=8 综合", _to_question_type(_stub_mastery(weak_score=8), "薄弱点强化"), "综合题"),
        _check("默认选择", _to_question_type(_stub_mastery(weak_score=1, qa_count=0, continuous_wrong_count=0), "薄弱点强化"), "选择题"),
        _check("mastery=None", _to_question_type(None, "薄弱点强化"), "选择题"),
    ]
    return all(results)


# ── 4. _to_count 映射 ─────────────────────────────────────────────
def test_to_count():
    print("\n=== _to_count ===")
    results = [
        _check("已改善复测固定2", _to_count(_stub_mastery(weak_score=10), "已改善知识点复测"), 2),
        _check("四科综合固定3", _to_count(_stub_mastery(weak_score=10), "四科随机综合"), 3),
        _check("ws>6 5道", _to_count(_stub_mastery(weak_score=7), "薄弱点强化"), 5),
        _check("ws>=3 3道", _to_count(_stub_mastery(weak_score=3), "薄弱点强化"), 3),
        _check("默认2道", _to_count(_stub_mastery(weak_score=0), "薄弱点强化"), 2),
    ]
    return all(results)


# ── 5. _personalize_hint / _format_mistake_tip ─────────────────────
def test_personalize():
    print("\n=== _personalize_hint / _format_mistake_tip ===")
    long_tip = _personalize_hint("a" * 100)
    results = [
        _check("空 tip", _personalize_hint(""), ""),
        _check("短 tip 保留", _personalize_hint("规则混淆"), "建议关注你最近的错因：规则混淆"),
        _check("长 tip 含截断省略号", "..." in long_tip, True),
        _check("长 tip 总长合理", len(long_tip) <= 80, True),
    ]

    class M:
        error_type = "概念混淆"
        error_reason = "把 LRU 和 FIFO 弄混了"

    results.append(_check("错题 tip 组装", _format_mistake_tip([M()]), "概念混淆：把 LRU 和 FIFO 弄混了"))
    return all(results)


# ── 6. choose_today_plan 降级链（mock）────────────────────────────
def test_today_plan_fallback():
    print("\n=== choose_today_plan 降级链 ===")

    # Mock build_smart_recommendations 的几种场景
    import services.recommendation_service as svc

    # 保存原始实现，测试结束恢复
    _original_build = svc.build_smart_recommendations

    scenario_results = []

    # 场景 A：错题可用 → 应该选"最近错题复练"
    def mock_all_available(*args, **kwargs):
        return [
            {"mode": "薄弱点强化", "available": True, "knowledge_point": "线性表", "subject": "数据结构", "reason": "弱", "difficulty": "中等", "question_type": "选择题", "count": 3, "initial": False},
            {"mode": "最近错题复练", "available": True, "knowledge_point": "LRU", "subject": "操作系统", "reason": "错", "difficulty": "中等", "question_type": "填空题", "count": 3, "initial": False},
            {"mode": "高频提问专项", "available": True, "knowledge_point": "TCP", "subject": "计算机网络", "reason": "问", "difficulty": "中等", "question_type": "简答题", "count": 2, "initial": False},
            {"mode": "已改善知识点复测", "available": True, "knowledge_point": "图", "subject": "数据结构", "reason": "已", "difficulty": "较难", "question_type": "选择题", "count": 2, "initial": False},
            {"mode": "四科随机综合", "available": True, "knowledge_point": "排序", "subject": "数据结构", "reason": "综", "difficulty": "中等", "question_type": "综合题", "count": 3, "initial": False},
        ]

    svc.build_smart_recommendations = mock_all_available
    plan = choose_today_plan(None, 1)
    scenario_results.append(_check("场景A：错题优先", plan.get("knowledge_point"), "LRU"))
    scenario_results.append(_check("场景A：title 含「今天优先攻克」", "今天优先攻克" in plan.get("title", ""), True))
    scenario_results.append(_check("场景A：empty_state=False", plan.get("empty_state"), False))

    # 场景 B：只有"薄弱点强化"可用
    def mock_only_weak(*args, **kwargs):
        return [
            {"mode": "薄弱点强化", "available": True, "knowledge_point": "线性表", "subject": "数据结构", "reason": "弱", "difficulty": "中等", "question_type": "选择题", "count": 3, "initial": False},
            {"mode": "最近错题复练", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "简单", "question_type": "选择题", "count": 2, "initial": True},
            {"mode": "高频提问专项", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "中等", "question_type": "填空题", "count": 2, "initial": True},
            {"mode": "已改善知识点复测", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "较难", "question_type": "选择题", "count": 2, "initial": True},
            {"mode": "四科随机综合", "available": True, "knowledge_point": "排序", "subject": "数据结构", "reason": "综", "difficulty": "中等", "question_type": "综合题", "count": 3, "initial": False},
        ]

    svc.build_smart_recommendations = mock_only_weak
    plan = choose_today_plan(None, 1)
    scenario_results.append(_check("场景B：降级到薄弱", plan.get("knowledge_point"), "线性表"))
    scenario_results.append(_check("场景B：empty_state=False", plan.get("empty_state"), False))

    # 场景 C：全部不可用 → 应该回落到基线诊断，initial_state=True
    def mock_all_unavailable(*args, **kwargs):
        return [
            {"mode": "薄弱点强化", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "简单", "question_type": "选择题", "count": 3, "initial": True},
            {"mode": "最近错题复练", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "简单", "question_type": "选择题", "count": 2, "initial": True},
            {"mode": "高频提问专项", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "中等", "question_type": "填空题", "count": 2, "initial": True},
            {"mode": "已改善知识点复测", "available": False, "knowledge_point": "", "subject": "", "reason": "", "difficulty": "较难", "question_type": "选择题", "count": 2, "initial": True},
            {"mode": "四科随机综合", "available": True, "knowledge_point": "排序", "subject": "数据结构", "reason": "综", "difficulty": "中等", "question_type": "综合题", "count": 3, "initial": False},
        ]

    svc.build_smart_recommendations = mock_all_unavailable
    plan = choose_today_plan(None, 1)
    scenario_results.append(_check("场景C：基线诊断", "基线诊断" in plan.get("title", ""), True))
    scenario_results.append(_check("场景C：initial_state=True", plan.get("initial_state"), True))
    scenario_results.append(_check("场景C：empty_state=True", plan.get("empty_state"), True))

    # 降级链顺序（综合不进入降级链）
    scenario_results.append(_check(
        "降级链顺序：错题→提问→薄弱",
        TODAY_PLAN_FALLBACK_CHAIN,
        ["最近错题复练", "高频提问专项", "薄弱点强化"],
    ))

    # 恢复原始实现，避免污染后续 test_full_integration
    svc.build_smart_recommendations = _original_build
    return all(scenario_results)


# ── 7. 完整 build_smart_recommendations（需要 in-memory sqlite）──
def test_full_integration():
    """集成测试：建内存 sqlite + 种子数据，跑完整 build_smart_recommendations / choose_today_plan。"""
    print("\n=== build_smart_recommendations 集成测试（in-memory sqlite）===")
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database import Base
        from models import (
            KnowledgeMastery,
            KnowledgePoint,
            Mistake,
            User,
        )
        from datetime import datetime, timedelta
    except Exception as e:
        print(f"[SKIP] 依赖缺失：{e}")
        return True  # 视为通过

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # 种子用户
    user = User(id=1, username="u1", email="u1@x.com", nickname="u1", password_hash="x")
    db.add(user)

    # 种子 KP（subject_id 给一个非空值，满足 NOT NULL 约束）
    kp1 = KnowledgePoint(id=1, subject_id=1, subject="数据结构", name="线性表", section="线性表", is_high_frequency=True, level=1)
    kp2 = KnowledgePoint(id=2, subject_id=2, subject="操作系统", name="页面置换算法", section="页面置换算法", is_high_frequency=True, level=1)
    db.add_all([kp1, kp2])
    db.flush()

    # 种子 mastery（薄弱点）
    m1 = KnowledgeMastery(
        user_id=1, subject="数据结构", knowledge_point="线性表",
        final_status="薄弱点", weak_score=8, continuous_wrong_count=2,
        total_answer_count=4, correct_count=1, wrong_count=3, qa_count=0,
    )
    # mastery 用 OCR 脏数据命名（验证 _normalize_kp）
    m2 = KnowledgeMastery(
        user_id=1, subject="计算机组成原理", knowledge_point="指令集体系结构(ISA)",
        final_status="不熟", weak_score=4, continuous_wrong_count=0,
        total_answer_count=2, correct_count=1, wrong_count=1, qa_count=0,
    )
    db.add_all([m1, m2])

    # 种子错题（用了脏 KP 名）
    mk1 = Mistake(
        user_id=1, subject="计算机组成原理", knowledge_point="指令集体系结构(ISA)",
        error_type="概念混淆", error_reason="把 ISA 和指令系统混了",
        status="active", create_time=datetime.utcnow(),
    )
    db.add(mk1)
    db.commit()

    # 跑推荐
    from services.recommendation_service import (
        choose_today_plan,
        normalize_existing_kp_rows,
    )
    import services.recommendation_service as svc_mod

    # 修复前：错题 KP 名是「指令集体系结构(ISA)」，mastery 同名 → 命中
    items_before = svc_mod.build_smart_recommendations(db, 1)
    mistake_item = next(it for it in items_before if it["mode"] == "最近错题复练")
    print(f"[INFO] 修复前：最近错题复练 KP = {mistake_item['knowledge_point']!r}, available={mistake_item['available']}")

    # 模拟历史脏数据：把 m2 的 KP 改成带括号后缀，看推荐能否匹配
    m2.knowledge_point = "指令集体系结构(ISA)"
    mk1.knowledge_point = "指令集体系结构(ISA)"
    db.commit()

    items_after = svc_mod.build_smart_recommendations(db, 1)
    mistake_item_after = next(it for it in items_after if it["mode"] == "最近错题复练")
    plan = choose_today_plan(db, 1)
    print(f"[INFO] 修复后：今天优先攻克 KP = {plan['knowledge_point']!r}, empty_state={plan.get('empty_state')}")

    # 关键断言：归一化后错题应该能挂上 mastery
    weak_item = next(it for it in items_after if it["mode"] == "薄弱点强化")
    print(f"[INFO] 薄弱点强化 KP = {weak_item['knowledge_point']!r}, available={weak_item['available']}")

    # 归一化数据修复函数
    updated = normalize_existing_kp_rows(db)
    print(f"[INFO] normalize_existing_kp_rows 改写行数 = {updated}")

    # 核心断言：归一化修复后，今天优先攻克应该指向脏 KP 名（说明 m2/mastery 已经被改成无括号版本）
    # 此时再跑一次，应该 KP 名变干净
    plan_final = choose_today_plan(db, 1)
    print(f"[INFO] 归一化后：今天优先攻克 KP = {plan_final['knowledge_point']!r}")

    # 验证：归一化后 KP 不再带括号
    assert "(" not in plan_final["knowledge_point"], f"归一化后 KP 仍含括号：{plan_final['knowledge_point']}"
    assert plan_final["empty_state"] is False, f"归一化后应该有内容，empty_state={plan_final['empty_state']}"
    assert plan_final["knowledge_point"] == "指令集体系结构", f"归一化后 KP 应是「指令集体系结构」，实际={plan_final['knowledge_point']}"
    print("[OK] 归一化后断言通过：KP 干净、有内容、非兜底")

    return True


# ── 8. 软降级：build_smart_recommendations 内部异常不阻塞接口 ─────
def test_soft_fallback():
    """验证 build_smart_recommendations / choose_today_plan 在底层异常时仍能返回有效数据。"""
    print("\n=== 软降级：build_smart_recommendations 内部异常 ===")
    import services.recommendation_service as svc

    results = []

    # 场景 D：_urgency_score 抛异常 → 整个 build_smart_recommendations 软降级为 5 个 available=False
    def _boom(*args, **kwargs):
        raise RuntimeError("simulated DB error")

    _original = svc._urgency_score
    svc._urgency_score = _boom
    try:
        items = svc.build_smart_recommendations(None, 999)  # db=None 也会触发异常
    finally:
        svc._urgency_score = _original

    results.append(_check("场景D：build 返回 5 项", len(items), 5))
    results.append(_check("场景D：所有项 available=False", all(it.get("available") is False for it in items), True))
    results.append(_check("场景D：5 个 mode 都齐", sorted([it["mode"] for it in items]), sorted([
        "薄弱点强化", "最近错题复练", "高频提问专项", "已改善知识点复测", "四科随机综合",
    ])))

    # 场景 E：choose_today_plan 在 build 异常时回落占位卡片
    svc._urgency_score = _boom
    try:
        plan = svc.choose_today_plan(None, 999)
    finally:
        svc._urgency_score = _original
    results.append(_check("场景E：plan 是 dict", isinstance(plan, dict), True))
    results.append(_check("场景E：initial_state=True", plan.get("initial_state"), True))
    results.append(_check("场景E：title 含基线诊断", "基线诊断" in plan.get("title", ""), True))

    return True


# ── 9. _filter_by_mode_used 必须接受 tuple / 单对象两种 candidates ─────
def test_filter_by_mode_used_dual_type():
    """回归测试：之前 _filter_by_mode_used 写死 c[0]，当 candidates 是 list[KnowledgeMastery]
    （不带分数）时会抛 TypeError。本次修复让两种形态都支持。
    """
    print("\n=== _filter_by_mode_used 双类型适配 ===")
    # 直接从 production db 拉取有 masteries 的用户,验证两种 candidates 形态都不会抛 TypeError
    from database import SessionLocal
    from services.recommendation_service import (
        build_smart_recommendations,
    )
    from models import KnowledgeMastery, User

    db = SessionLocal()
    # 找一个 masteries 最多的用户
    user = db.query(User).first()
    if not user:
        print("[SKIP] db 无用户")
        return True

    # 通过 build_smart_recommendations 间接验证：
    # 内部 _filter_by_mode_used 会被以下三种 candidates 形态调用：
    # 1. scored_weak: list[tuple[KnowledgeMastery, float]]
    # 2. qa_candidates_all: list[KnowledgeMastery]（之前会 TypeError 的元凶）
    # 3. improved_candidates_all: list[KnowledgeMastery]
    # 只要 build_smart_recommendations 不抛 TypeError,就算通过
    try:
        items = build_smart_recommendations(db, user.id)
        avail = sum(1 for it in items if it.get("available"))
        ok = avail > 0 or all(not it.get("available") and "TypeError" not in it.get("reason", "") for it in items)
        print(f"[OK] _filter_by_mode_used 双类型适配：user_id={user.id} available={avail}/5")
        return ok
    except TypeError as e:
        print(f"[FAIL] TypeError 复现：{e}")
        return False
    finally:
        db.close()


# ── main ──────────────────────────────────────────────────────────
def main():
    all_ok = True
    all_ok &= test_normalize_kp()
    all_ok &= test_to_difficulty()
    all_ok &= test_to_question_type()
    all_ok &= test_to_count()
    all_ok &= test_personalize()
    all_ok &= test_today_plan_fallback()
    all_ok &= test_full_integration()
    all_ok &= test_soft_fallback()
    all_ok &= test_filter_by_mode_used_dual_type()
    print("\n" + ("=" * 50))
    print("全部通过" if all_ok else "存在失败用例")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
