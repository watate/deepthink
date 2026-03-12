from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    s3_bucket: str = "deepthink"
    s3_api: str = ""
    s3_api_access_key_id: str = ""
    s3_api_secret: str = ""
    s3_api_token: str = ""
    llm_model: str = "claude-sonnet-4-6"
    openrouter_providers: str = ""
    default_num_questions: int = 2

    model_config = {"env_file": str(_ROOT / ".env"), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
