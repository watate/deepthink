import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")

from .config import get_settings  # noqa: E402
from .routes import router  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if not settings.anthropic_api_key and not settings.openrouter_api_key:
        print(
            "WARNING: No LLM API key set (ANTHROPIC_API_KEY or OPENROUTER_API_KEY) — LLM calls will fail"
        )
    elif settings.anthropic_api_key:
        print("Using Anthropic provider")
    else:
        print("Using OpenRouter provider")
    if not settings.s3_api:
        print("WARNING: S3_API is not set — S3 operations will fail")
    yield


app = FastAPI(title="DeepThink API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
