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
    memories_used: list[dict]
    mastery: dict
    answer: dict
    suggested_followups: list[str]
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str


class QuestionState(TypedDict, total=False):
    user_id: int
    mode: str
    subject: str
    knowledge_point: str
    difficulty: str
    question_type: str
    count: int
    context: list[dict]
    questions: list[dict]
    session_id: int
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str


class AnswerCheckState(TypedDict, total=False):
    user_id: int
    question_id: int
    user_answer: str
    question: dict
    is_correct: bool
    score: float
    feedback: dict
    recommended_causes: list[str]
    answer_record_id: int
    mastery: dict
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str


class MistakeState(TypedDict, total=False):
    user_id: int
    answer_record_id: int
    error_types: list[str]
    user_note: str
    mistake_id: int
    memory_id: int
    similar_mistakes: list[dict]
    agent_steps: list[AgentStep]
    llm_used: bool
    llm_error: str
