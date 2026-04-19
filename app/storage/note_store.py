import json
import os
from pathlib import Path

from app.storage.models import Note


class NoteStore:
    def __init__(self, data_dir: Path):
        self._dir = data_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._notes_file = self._dir / "notes.json"
        self._log_file = self._dir / "notes.jsonl"

    def load(self) -> list[Note]:
        if not self._notes_file.exists():
            return []
        with open(self._notes_file) as f:
            raw = json.load(f)
        return [Note(**n) for n in raw]

    def save(self, note: Note) -> None:
        notes = self.load()
        notes.append(note)
        tmp = self._notes_file.with_suffix(".tmp.json")
        with open(tmp, "w") as f:
            json.dump([n.model_dump() for n in notes], f, indent=2)
        os.replace(tmp, self._notes_file)
        with open(self._log_file, "a") as f:
            f.write(note.model_dump_json() + "\n")

    def get_all(self) -> list[Note]:
        return self.load()

    def get_by_id(self, note_id: str) -> Note | None:
        return next((n for n in self.load() if n.id == note_id), None)

    def delete(self, note_id: str) -> bool:
        notes = self.load()
        filtered = [n for n in notes if n.id != note_id]
        if len(filtered) == len(notes):
            return False
        tmp = self._notes_file.with_suffix(".tmp.json")
        with open(tmp, "w") as f:
            json.dump([n.model_dump() for n in filtered], f, indent=2)
        os.replace(tmp, self._notes_file)
        return True
