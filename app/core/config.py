"""
Configuration management for the FastAPI application
"""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "LegendaryCorp AI Assistant"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5252, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"

    # ChromaDB Visualizer
    chroma_db_visualizer: bool = Field(default=False, env="CHROMA_DB_VISUALIZER")

    # API Documentation
    enable_redoc: bool = Field(default=False, env="ENABLE_REDOC")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_api_base: str = Field(
        default="https://api.openai.com/v1", env="OPENAI_API_BASE"
    )

    # HuggingFace
    tokenizers_parallelism: str = Field(default="false", env="TOKENIZERS_PARALLELISM")
    hf_hub_disable_telemetry: str = Field(default="1", env="HF_HUB_DISABLE_TELEMETRY")
    transformers_offline: str = Field(default="0", env="TRANSFORMERS_OFFLINE")

    # Security
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")

    # Performance
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")

    # Database
    chroma_db_path: str = Field(default="./chroma_db", env="CHROMA_DB_PATH")
    knowledge_docs_path: str = Field(
        default="./knowledge-docs", env="KNOWLEDGE_DOCS_PATH"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        validate_assignment=True
    )


# Global settings instance
settings = Settings()
