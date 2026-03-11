from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv("../../.env")

from config import get_settings  # noqa: E402
from routes import router  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if not settings.openrouter_api_key:
        print("WARNING: OPENROUTER_API_KEY is not set — LLM calls will fail")
    if not settings.s3_api:
        print("WARNING: S3_API is not set — S3 operations will fail")
    yield


app = FastAPI(title="DeepThink API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
