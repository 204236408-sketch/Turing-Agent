import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"


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


_WEAK_SECRETS = {"", "change-this-secret-in-production", "please-change-me"}


def _resolve_secret_key() -> str:
    value = _get("SECRET_KEY", "change-this-secret-in-production")
    if value not in _WEAK_SECRETS and len(value) >= 32:
        return value
    env = _get("APP_ENV", "dev")
    if env.lower() in {"prod", "production"}:
        raise RuntimeError(
            "SECRET_KEY must be set to a strong value (>=32 chars) in production via .env"
        )
    strong = os.urandom(32).hex()
    logging.warning(
        "SECRET_KEY is weak or default ('%s...'). Auto-generated temporary key in dev mode. "
        "Set SECRET_KEY in .env for persistence.",
        value[:16],
    )
    return strong


@dataclass(frozen=True)
class Settings:
    app_name: str = "Turing 408 Agent"
    app_env: str = _get("APP_ENV", "dev")
    debug: bool = _bool("DEBUG", True)

    database_url: str = _database_url("DATABASE_URL", f"sqlite:///{BASE_DIR / 'turing408.db'}")
    mysql_url: str = _get("MYSQL_URL", "")
    auto_migrate_on_startup: bool = _bool("AUTO_MIGRATE_ON_STARTUP", False)

    secret_key: str = _resolve_secret_key()
    access_token_expire_minutes: int = _int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)
    allow_demo_auth_fallback: bool = _bool("ALLOW_DEMO_AUTH_FALLBACK", False)

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

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


def validate_security_settings() -> None:
    if not settings.is_production:
        return
    if settings.secret_key in _WEAK_SECRETS or len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")
    if settings.allow_demo_auth_fallback:
        raise RuntimeError("ALLOW_DEMO_AUTH_FALLBACK must be disabled in production")
    if settings.auto_migrate_on_startup:
        raise RuntimeError("AUTO_MIGRATE_ON_STARTUP must be disabled in production")
    if settings.cors_origins == "*":
        raise RuntimeError(
            "CORS_ORIGINS must not be '*' in production. "
            "Set to comma-separated allowed origins (e.g. https://example.com)."
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
