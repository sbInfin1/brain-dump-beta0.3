import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.core.pipeline import Pipeline, QueryResult, StoreResult


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/api/chat")
async def chat(body: ChatRequest, request: Request):
    pipeline: Pipeline = request.app.state.pipeline
    result = await pipeline.handle(body.message.strip())

    if isinstance(result, StoreResult):
        return JSONResponse({
            "type": "stored",
            "note": result.note.model_dump(),
        })

    # QueryResult → SSE stream
    async def event_stream():
        try:
            async for chunk in result.stream:
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/notes")
async def list_notes(request: Request, tag: Optional[str] = None, q: Optional[str] = None):
    from app.core.bm25_index import BM25Index
    store = request.app.state.store
    notes = store.get_all()
    if tag:
        notes = [n for n in notes if tag.lower() in [t.lower() for t in n.tags]]
    if q:
        index: BM25Index = request.app.state.index
        notes = index.search(q, top_k=20)
    return [n.model_dump() for n in notes]


@router.delete("/api/notes/{note_id}")
async def delete_note(note_id: str, request: Request):
    store = request.app.state.store
    index = request.app.state.index
    deleted = store.delete(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    # rebuild index after deletion
    index.build(store.get_all())
    return {"deleted": note_id}


@router.get("/api/health")
async def health(request: Request):
    store = request.app.state.store
    index = request.app.state.index
    return {"note_count": len(store.get_all()), "index_size": index.size}
