from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    data_dir: str = "./data"
    top_k: int = 5
    # intent_model: str = "google/gemma-3-27b-it:free"
    # answer_model: str = "google/gemma-3-27b-it:free"
    # intent_model: str = "moonshotai/kimi-k2.5"
    # answer_model: str = "moonshotai/kimi-k2.5"
    intent_model: str = "anthropic/claude-haiku-4.5"
    answer_model: str = "anthropic/claude-haiku-4.5"
    max_answer_tokens: int = 1024
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    model_config = {"env_file": ".env"}
