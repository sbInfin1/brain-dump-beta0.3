import json
import re
from dataclasses import dataclass, field
from typing import Literal

from openai import OpenAI


_STORE_SIGNALS = re.compile(
    r"^(remember|note|save|add|log|todo|task)\b|"
    r"\b(remember that|remember this|note that|save this|add this)\b|"
    r"^#\w+",
    re.IGNORECASE,
)

_CLASSIFY_PROMPT = """\
You are an intent classifier for a personal note-taking system.
Classify the user message as either "store" (saving information) or "query" (asking a question).
If "store", extract the clean note content and relevant tags (1-3 short lowercase words).
If "query", return the original message as content with empty tags.

Respond ONLY with valid JSON matching this schema:
{"intent": "store" | "query", "content": "<text>", "tags": ["tag1", "tag2"]}"""


@dataclass
class IntentResult:
    intent: Literal["store", "query"]
    content: str
    tags: list[str] = field(default_factory=list)


class IntentClassifier:
    def __init__(self, client: OpenAI, model: str):
        self._client = client
        self._model = model

    async def classify(self, message: str) -> IntentResult:
        is_obvious_store = bool(_STORE_SIGNALS.search(message))

        if is_obvious_store:
            system = (
                "Extract the clean note content and 1-3 relevant tags from the message. "
                "Strip filler words like 'remember that', 'note:', 'save this', etc. "
                "Respond ONLY with valid JSON: "
                '{"intent": "store", "content": "<clean text>", "tags": ["tag1"]}'
            )
        else:
            system = _CLASSIFY_PROMPT

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=256,
                temperature=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": message},
                ],
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL)
            parsed = json.loads(raw)
            return IntentResult(
                intent=parsed.get("intent", "query"),
                content=parsed.get("content", message),
                tags=parsed.get("tags", []),
            )
        except Exception:
            return IntentResult(intent="query", content=message, tags=[])
