from typing import Any, TypedDict


class AgentStep(TypedDict, total=False):
    name: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str


class QAState(TypedDict, total=False):
    user_id: int
    conversation_id: int | None
    question: str
    subject: str
    knowledge_point: str
    history: list[dict]
    retrieved_knowledge: list[dict]
    seed_questions: list[dict]
    retrieval: dict
    memories_used: list[dict]
    mastery: dict
    answer: dict
    suggested_followups: list[str]
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str
    answer_valid: bool


class QuestionState(TypedDict, total=False):
    user_id: int
    mode: str
    subject: str
    knowledge_point: str
    scope: str
    chapter: str
    chapter_id: int | None
    prompt_knowledge_point: str
    target_points: list[str]
    difficulty: str
    question_type: str
    count: int
    context: list[dict]
    questions: list[dict]
    session_id: int
    config: str
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str
    mastery_text: str
    mistake_summary: str
    misconception_profile: dict[str, Any]
    raw_questions: list[dict]
    variant_type: str
    llm_result: Any
    questions_valid: bool
    loose_mode: bool


class AnswerCheckState(TypedDict, total=False):
    user_id: int
    question_id: int
    user_answer: str
    question: dict
    is_correct: bool
    score: float
    feedback: str
    feedback_value: str
    recommended_causes: list[str]
    answer_record_id: int
    mastery: dict
    normalized_answer: str
    suggested_error_types: list[str]
    llm_result: Any
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str


class MistakeState(TypedDict, total=False):
    user_id: int
    answer_record_id: int
    error_types: list[str]
    user_note: str
    evidence_source: str
    agent_suggested_types: list[str]
    mistake_id: int
    memory_id: int
    similar_mistakes: list[dict]
    record_id: int
    record_subject: str
    record_kp: str
    record_user_answer: str
    record_std_answer: str
    record_feedback: str
    record_question_id: int
    error_type: str
    error_reason: str
    suggestion: str
    memory_content: str
    llm_result: Any
    chroma_stored: bool
    mastery_status: str
    weak_score: float
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str
