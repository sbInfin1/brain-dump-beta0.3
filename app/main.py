from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from app.api.routes import router
from app.config import Settings
from app.core.answer import AnswerGenerator
from app.core.bm25_index import BM25Index
from app.core.intent import IntentClassifier
from app.core.pipeline import Pipeline
from app.storage.note_store import NoteStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )

    store = NoteStore(settings.data_path)
    index = BM25Index()
    notes = store.load()
    index.build(notes)

    classifier = IntentClassifier(client=client, model=settings.intent_model)
    answer_gen = AnswerGenerator(
        client=client,
        model=settings.answer_model,
        max_tokens=settings.max_answer_tokens,
    )
    pipeline = Pipeline(
        classifier=classifier,
        bm25_index=index,
        note_store=store,
        answer_gen=answer_gen,
        top_k=settings.top_k,
    )

    app.state.store = store
    app.state.index = index
    app.state.pipeline = pipeline

    yield


app = FastAPI(title="Brain Dump v3", lifespan=lifespan)
app.include_router(router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
