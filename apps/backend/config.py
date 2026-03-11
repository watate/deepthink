from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    s3_bucket: str = "deepthink"
    s3_api: str = ""
    s3_api_access_key_id: str = ""
    s3_api_secret: str = ""
    s3_api_token: str = ""
    llm_model: str = "moonshotai/kimi-k2.5"
    default_num_questions: int = 2

    model_config = {"env_file": str(_ROOT / ".env"), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
