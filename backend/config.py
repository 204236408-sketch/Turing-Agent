import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def _load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


_ENV_FILE = _load_dotenv(BASE_DIR / ".env")


def _get(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return _ENV_FILE.get(name, default)


def _bool(name: str, default: bool = False) -> bool:
    value = _get(name, str(default)).lower()
    return value in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(_get(name, str(default)))
    except ValueError:
        return default


def _database_url(name: str, default: str) -> str:
    value = _get(name, default)
    prefix = "sqlite:///"
    if not value.startswith(prefix) or value == "sqlite:///:memory:":
        return value

    db_path = value[len(prefix) :]
    if db_path.startswith(("/", "\\")) or (len(db_path) >= 2 and db_path[1] == ":"):
        return value

    resolved = (BASE_DIR / db_path).resolve().as_posix()
    return f"{prefix}{resolved}"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Turing 408 Agent"
    app_env: str = _get("APP_ENV", "dev")
    debug: bool = _bool("DEBUG", True)

    database_url: str = _database_url("DATABASE_URL", f"sqlite:///{BASE_DIR / 'turing408.db'}")
    mysql_url: str = _get("MYSQL_URL", "")

    secret_key: str = _get("SECRET_KEY", "change-this-secret-in-production")
    access_token_expire_minutes: int = _int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)

    siliconflow_api_key: str = _get("SILICONFLOW_API_KEY", "")
    siliconflow_base_url: str = _get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    siliconflow_model: str = _get("SILICONFLOW_MODEL", "Qwen/Qwen3.5-9B")
    llm_timeout_seconds: int = _int("LLM_TIMEOUT_SECONDS", 30)

    chroma_path: str = _get("CHROMA_PATH", str(BASE_DIR / "vector_store" / "chroma"))
    upload_dir: str = _get("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    report_dir: str = _get("REPORT_DIR", str(BASE_DIR / "outputs" / "reports"))

    cors_origins: str = _get("CORS_ORIGINS", "*")

    @property
    def active_database_url(self) -> str:
        return self.mysql_url or self.database_url

    @property
    def llm_enabled(self) -> bool:
        return bool(self.siliconflow_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
