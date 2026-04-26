import uuid
from datetime import datetime, timezone
from pydantic import BaseModel


class Note(BaseModel):
    id: str
    content: str
    created_at: str
    tags: list[str]
    source: str = "chat"

    @classmethod
    def from_user_input(cls, content: str, tags: list[str]) -> "Note":
        return cls(
            id=uuid.uuid4().hex,
            content=content,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            tags=tags,
        )


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

    @classmethod
    def new(cls, role: str, content: str) -> "ChatMessage":
        return cls(
            id=uuid.uuid4().hex,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
