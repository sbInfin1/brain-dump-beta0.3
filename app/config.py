from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    google_client_id: str
    database_url: str
    top_k: int = 5
    # intent_model: str = "google/gemma-3-27b-it:free"
    # answer_model: str = "google/gemma-3-27b-it:free"
    # intent_model: str = "moonshotai/kimi-k2.5"
    # answer_model: str = "moonshotai/kimi-k2.5"
    intent_model: str = "anthropic/claude-haiku-4.5"
    answer_model: str = "anthropic/claude-haiku-4.5"
    max_answer_tokens: int = 1024
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = {"env_file": ".env"}
