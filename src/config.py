"""Configuration management for Storyplex Analytics."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://storyplex:storyplex_dev@localhost:5432/storyplex"

    # LLM Settings
    anthropic_api_key: Optional[str] = None
    llm_model: str = "claude-sonnet-4-20250514"  # Fast and capable
    llm_max_tokens: int = 2048

    # Rate limiting defaults (requests per second)
    ao3_rate_limit: float = 0.2  # 1 request per 5 seconds (AO3 is sensitive)
    default_rate_limit: float = 1.0

    # Scraper settings
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    request_timeout: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
