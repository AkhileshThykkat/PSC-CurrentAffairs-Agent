from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./psc_agent.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma:2b"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    semantic_similarity_threshold: float = 0.90
    faiss_index_path: str = "./data/faiss.index"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
