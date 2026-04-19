from fastapi import Header, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import Settings

_settings = Settings()


async def get_current_user(authorization: str = Header(...)) -> str:
    try:
        token = authorization.removeprefix("Bearer ").strip()
        payload = id_token.verify_oauth2_token(
            token, google_requests.Request(), _settings.google_client_id
        )
        return payload["email"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
