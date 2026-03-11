from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    s3_bucket: str = "deepthink"
    s3_api: str = ""
    s3_api_access_key_id: str = ""
    s3_api_secret: str = ""
    s3_api_token: str = ""
    llm_model: str = "anthropic/claude-sonnet-4"
    default_num_questions: int = 2

    model_config = {"env_file": "../../.env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
