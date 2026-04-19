import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.core.answer import AnswerGenerator
from app.core.bm25_index import BM25Index
from app.core.intent import IntentClassifier
from app.storage.models import Note
from app.storage.note_store import NoteStore


@dataclass
class StoreResult:
    note: Note


@dataclass
class QueryResult:
    retrieved_notes: list[Note]
    stream: AsyncIterator[str]


PipelineResult = StoreResult | QueryResult


class Pipeline:
    def __init__(
        self,
        classifier: IntentClassifier,
        answer_gen: AnswerGenerator,
        top_k: int = 5,
    ):
        self._classifier = classifier
        self._answer_gen = answer_gen
        self._top_k = top_k

    async def handle(self, message: str, store: NoteStore, index: BM25Index) -> PipelineResult:
        intent = await self._classifier.classify(message)

        if intent.intent == "store":
            note = Note.from_user_input(content=intent.content, tags=intent.tags)
            await asyncio.to_thread(store.save, note)
            index.add(note)
            return StoreResult(note=note)

        retrieved = index.search(intent.content, top_k=self._top_k)
        stream = await self._answer_gen.stream(intent.content, retrieved)
        return QueryResult(retrieved_notes=retrieved, stream=stream)
