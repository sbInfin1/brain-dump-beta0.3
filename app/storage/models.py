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
