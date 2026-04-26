from contextlib import asynccontextmanager

import psycopg2
import psycopg2.pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.api.routes import router
from app.config import Settings
from app.core.answer import AnswerGenerator
from app.core.intent import IntentClassifier
from app.core.pipeline import Pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    pool = psycopg2.pool.ThreadedConnectionPool(1, 10, settings.database_url)
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    tags TEXT[] NOT NULL DEFAULT '{}',
                    source TEXT NOT NULL DEFAULT 'chat'
                );
                CREATE INDEX IF NOT EXISTS idx_notes_user_email ON notes(user_email);
            """)
        conn.commit()
    finally:
        pool.putconn(conn)

    app.state.db_pool = pool

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
    app.state.user_stores = {}

    yield

    pool.closeall()


app = FastAPI(title="Brain Dump v3", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

app.include_router(router)
