from collections.abc import AsyncIterator
from datetime import datetime, timezone

from openai import OpenAI

from app.storage.models import Note


_EMPTY_SYSTEM = (
    "You are a personal knowledge assistant. "
    "The user's note collection is currently empty. "
    "Tell them to add some notes first by typing something like "
    "'Remember that...' or 'Note: ...' or 'Todo: ...'"
)

_ANSWER_SYSTEM_TEMPLATE = """\
You are a personal knowledge assistant. Today's date is {today}.
Answer the user's question using ONLY the information in the notes below. \
If a note uses relative words like "today", "tomorrow", or "this week", interpret them \
relative to the date the note was saved (shown in parentheses), NOT today's date. \
If the notes do not contain enough information to answer, say so clearly. \
Be concise. Cite which notes you draw from (Note 1, Note 2, etc.).

Notes:
---
{notes_section}
---"""


class AnswerGenerator:
    def __init__(self, client: OpenAI, model: str, max_tokens: int):
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def stream(self, query: str, context_notes: list[Note]) -> AsyncIterator[str]:
        if context_notes:
            notes_section = "\n\n".join(
                f"Note {i + 1} (saved {n.created_at[:10]}):\n{n.content}"
                for i, n in enumerate(context_notes)
            )
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            system = _ANSWER_SYSTEM_TEMPLATE.format(today=today, notes_section=notes_section)
        else:
            system = _EMPTY_SYSTEM

        return self._stream_chunks(query, system)

    async def _stream_chunks(self, query: str, system: str) -> AsyncIterator[str]:
        stream = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=0.3,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ],
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
