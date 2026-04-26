from fastapi import Depends, Request

from app.auth import get_current_user
from app.core.bm25_index import BM25Index
from app.storage.note_store import NoteStore


def get_user_store(
    user: str = Depends(get_current_user),
    request: Request = None,
) -> tuple[NoteStore, BM25Index]:
    stores: dict[str, tuple[NoteStore, BM25Index]] = request.app.state.user_stores
    if user not in stores:
        store = NoteStore(user_email=user, pool=request.app.state.db_pool)
        index = BM25Index()
        index.build(store.load())
        stores[user] = (store, index)
    return stores[user]
