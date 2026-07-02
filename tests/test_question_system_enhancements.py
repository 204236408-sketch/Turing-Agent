from p5_helpers import assert_success


def test_question_request_normalizes_frontend_labels():
    from backend.schemas import QuestionGenerateRequest

    payload = QuestionGenerateRequest(
        subject="计组",
        knowledge_point="指令系统",
        difficulty="真题难度",
        question_type="单选题",
        count=1,
    )

    assert payload.subject == "计算机组成原理"
    assert payload.difficulty == "较难"
    assert payload.question_type == "选择题"


def test_hybrid_retrieve_matches_section_name(db_session):
    from models import KnowledgePoint, Subject
    from services.hybrid_retriever import hybrid_retrieve

    subject = db_session.query(Subject).filter(Subject.name == "操作系统").first()
    if not subject:
        subject = Subject(name="操作系统", description="408 操作系统")
        db_session.add(subject)
        db_session.flush()

    exists = (
        db_session.query(KnowledgePoint)
        .filter(
            KnowledgePoint.subject == "操作系统",
            KnowledgePoint.name == "内存管理",
            KnowledgePoint.section == "页面置换算法",
            KnowledgePoint.is_deleted == False,
        )
        .first()
    )
    if not exists:
        db_session.add(
            KnowledgePoint(
                subject_id=subject.id,
                subject="操作系统",
                parent_name="操作系统",
                name="内存管理",
                section="页面置换算法",
                level=3,
                content="页面置换算法在缺页且无空闲页框时选择淘汰页，常见算法包括 FIFO、LRU、OPT 和 Clock。",
                common_mistakes="混淆缺页中断和页面置换；误以为命中也会发生置换。",
                keywords="页面置换算法,FIFO,LRU,OPT,Clock,缺页",
                is_high_frequency=True,
            )
        )
        db_session.flush()

    result = hybrid_retrieve(
        db_session,
        "操作系统 页面置换算法",
        limit=3,
        subject_filter="操作系统",
        kp_filter="页面置换算法",
        use_rerank=False,
    )

    assert result["items"]
    joined = "\n".join(item.get("content", "") for item in result["items"])
    assert "页面" in joined and "置换" in joined


def test_mixed_question_generation_returns_multiple_types(auth_client):
    body = assert_success(
        auth_client.post(
            "/api/questions/generate",
            json={
                "mode": "知识点专项",
                "subject": "操作系统",
                "knowledge_point": "页面置换算法",
                "difficulty": "自适应",
                "question_type": "混合",
                "count": 3,
            },
        )
    )
    questions = body["data"]["questions"]
    assert len(questions) == 3
    assert len({q["variant_type"] for q in questions}) >= 2


def test_misconception_profile_injects_trap_option():
    from agents.question_graph import _apply_misconception_traps, _trap_option_for_error

    trap = _trap_option_for_error("规则混淆", "总把 LRU 和 FIFO 的淘汰依据混在一起", "页面置换算法")
    question = {
        "question_text": "LRU 页面置换算法淘汰哪类页面？",
        "options": ["A. 最近最长时间未访问的页面", "B. 最早进入内存的页面", "C. 编号最大的页面", "D. 访问次数最多的页面"],
        "standard_answer": "A",
        "explanation": "LRU 按最近访问时间判断。",
        "easy_mistakes": "",
    }

    out = _apply_misconception_traps(
        [question],
        {"items": [{"error_type": "规则混淆", "trap_option": trap, "target_hint": "混淆了 LRU 与 FIFO 的淘汰依据。"}]},
    )[0]

    assert trap in "\n".join(out["options"])
    assert "规则混淆" in out["easy_mistakes"]
    assert trap in out["explanation"]
