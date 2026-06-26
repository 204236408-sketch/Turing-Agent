from enum import Enum


class SubjectName(str, Enum):
    DS = "数据结构"
    CO = "计算机组成原理"
    OS = "操作系统"
    CN = "计算机网络"

    @classmethod
    def list(cls) -> list[str]:
        return [m.value for m in cls]


class MasteryStatus(str, Enum):
    UNLEARNED = "未学"
    WEAK = "薄弱点"
    UNKNOWN = "不会"
    UNFAMILIAR = "不熟"
    MASTERED = "掌握"

    @classmethod
    def list(cls) -> list[str]:
        return [m.value for m in cls]


class Difficulty(str, Enum):
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"


class QuestionType(str, Enum):
    CHOICE = "选择题"
    COMPREHENSIVE = "综合题"
    SHORT_ANSWER = "简答题"


class GenerationMode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"
    WEAK_POINT = "weak_point"


class QuestionSource(str, Enum):
    SEED = "seed"
    AGENT_MOCK = "agent_mock"


class MistakeInputType(str, Enum):
    SYSTEM = "系统出题"
    MANUAL = "手动录入"


class MistakeStatus(str, Enum):
    ACTIVE = "active"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class MemoryType(str, Enum):
    WEAK_POINT = "weak_point"
    RECITE = "recite"


class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    STAGE = "stage"
