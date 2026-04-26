from psycopg2.extras import RealDictCursor

from app.storage.models import Note


class NoteStore:
    def __init__(self, user_email: str, pool):
        self._user = user_email
        self._pool = pool

    def _row_to_note(self, row) -> Note:
        return Note(
            id=row["id"],
            content=row["content"],
            created_at=row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            tags=list(row["tags"]),
            source=row["source"],
        )

    def load(self) -> list[Note]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, content, created_at, tags, source FROM notes "
                    "WHERE user_email = %s ORDER BY created_at",
                    (self._user,),
                )
                return [self._row_to_note(r) for r in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def save(self, note: Note) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO notes (id, user_email, content, created_at, tags, source) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (note.id, self._user, note.content, note.created_at, note.tags, note.source),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_all(self) -> list[Note]:
        return self.load()

    def get_by_id(self, note_id: str) -> Note | None:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, content, created_at, tags, source FROM notes "
                    "WHERE user_email = %s AND id = %s",
                    (self._user, note_id),
                )
                row = cur.fetchone()
            return self._row_to_note(row) if row else None
        finally:
            self._pool.putconn(conn)

    def delete(self, note_id: str) -> bool:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM notes WHERE user_email = %s AND id = %s",
                    (self._user, note_id),
                )
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            self._pool.putconn(conn)
