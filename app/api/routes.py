import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_user_store
from app.auth import get_current_user
from app.core.bm25_index import BM25Index
from app.core.pipeline import Pipeline, QueryResult, StoreResult
from app.storage.note_store import NoteStore


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/api/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    store_pair: tuple[NoteStore, BM25Index] = Depends(get_user_store),
):
    store, index = store_pair
    pipeline: Pipeline = request.app.state.pipeline
    result = await pipeline.handle(body.message.strip(), store, index)

    if isinstance(result, StoreResult):
        return JSONResponse({"type": "stored", "note": result.note.model_dump()})

    async def event_stream():
        try:
            async for chunk in result.stream:
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/notes")
async def list_notes(
    request: Request,
    store_pair: tuple[NoteStore, BM25Index] = Depends(get_user_store),
    tag: Optional[str] = None,
    q: Optional[str] = None,
):
    store, index = store_pair
    notes = store.get_all()
    if tag:
        notes = [n for n in notes if tag.lower() in [t.lower() for t in n.tags]]
    if q:
        notes = index.search(q, top_k=20)
    return [n.model_dump() for n in notes]


@router.delete("/api/notes/{note_id}")
async def delete_note(
    note_id: str,
    store_pair: tuple[NoteStore, BM25Index] = Depends(get_user_store),
):
    store, index = store_pair
    if not store.delete(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    index.build(store.get_all())
    return {"deleted": note_id}


@router.get("/api/health")
async def health(
    store_pair: tuple[NoteStore, BM25Index] = Depends(get_user_store),
):
    store, index = store_pair
    return {"note_count": len(store.get_all()), "index_size": index.size}
