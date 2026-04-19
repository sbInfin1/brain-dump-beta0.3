from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from app.api.routes import router
from app.config import Settings
from app.core.answer import AnswerGenerator
from app.core.intent import IntentClassifier
from app.core.pipeline import Pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )

    classifier = IntentClassifier(client=client, model=settings.intent_model)
    answer_gen = AnswerGenerator(
        client=client,
        model=settings.answer_model,
        max_tokens=settings.max_answer_tokens,
    )
    pipeline = Pipeline(
        classifier=classifier,
        answer_gen=answer_gen,
        top_k=settings.top_k,
    )

    app.state.pipeline = pipeline
    app.state.user_stores = {}  # lazily populated per user on first request

    yield


app = FastAPI(title="Brain Dump v3", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
