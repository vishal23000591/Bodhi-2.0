from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "bodhi"

    openrouter_api_key: str = ""
    openrouter_chat_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    openrouter_embed_model: str = "nvidia/nemotron-3-embed-1b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080

    chroma_persist_dir: str = "./chroma_data"
    upload_dir: str = "./uploads"

    min_chars_per_page: int = 30
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
