from psycopg2.extras import RealDictCursor

from app.storage.models import ChatMessage


class MessageStore:
    def __init__(self, user_email: str, pool):
        self._user = user_email
        self._pool = pool

    def save(self, msg: ChatMessage) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (id, user_email, role, content, created_at) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (msg.id, self._user, msg.role, msg.content, msg.created_at),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def load_all(self) -> list[ChatMessage]:
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, role, content, created_at FROM messages "
                    "WHERE user_email = %s ORDER BY created_at",
                    (self._user,),
                )
                return [
                    ChatMessage(
                        id=r["id"],
                        role=r["role"],
                        content=r["content"],
                        created_at=r["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    )
                    for r in cur.fetchall()
                ]
        finally:
            self._pool.putconn(conn)
