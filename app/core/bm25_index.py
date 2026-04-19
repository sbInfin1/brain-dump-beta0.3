import re

from rank_bm25 import BM25Okapi

from app.storage.models import Note


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


class BM25Index:
    def __init__(self):
        self._notes: list[Note] = []
        self._bm25: BM25Okapi | None = None

    def build(self, notes: list[Note]) -> None:
        self._notes = list(notes)
        if not notes:
            self._bm25 = None
            return
        corpus = [_tokenize(n.content + " " + " ".join(n.tags)) for n in notes]
        self._bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> list[Note]:
        if not self._notes or self._bm25 is None:
            return []
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = [self._notes[i] for i in ranked[:top_k] if scores[i] > 0]
        if not results:
            # fallback: 3 most recent notes by created_at
            results = sorted(self._notes, key=lambda n: n.created_at, reverse=True)[:3]
        return results

    def add(self, note: Note) -> None:
        self._notes.append(note)
        corpus = [_tokenize(n.content + " " + " ".join(n.tags)) for n in self._notes]
        self._bm25 = BM25Okapi(corpus)

    @property
    def size(self) -> int:
        return len(self._notes)
