from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ms-cadastro-funcionario"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "technova_funcionarios"
    mongo_server_selection_timeout_ms: int = 5000
    mongo_connect_timeout_ms: int = 5000
    mongo_operation_timeout_ms: int = 5000
    idempotency_retention_seconds: int = 86400
    idempotency_lease_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
