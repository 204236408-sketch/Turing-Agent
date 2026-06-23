"""Environment-backed application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    database_url: str = "mysql+pymysql://root:password@127.0.0.1:3306/turing408"
    cors_origins: list[str] = ["http://127.0.0.1:5500", "http://localhost:5500"]
    llm_provider: str = "mock"
    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    chroma_path: str = "./vector_store/chroma"
    upload_path: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

