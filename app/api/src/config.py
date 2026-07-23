from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="athena", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    postgres_host: str | None = Field(default=None, alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str | None = Field(default=None, alias="POSTGRES_DB")
    postgres_user: str | None = Field(default=None, alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_schema: str = Field(default="public", alias="POSTGRES_SCHEMA")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    generation_model: str = Field(default="gpt-4.1-mini", alias="GENERATION_MODEL")

    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(alias="ELEVENLABS_VOICE_ID")
    elevenlabs_model_id: str = Field(default="eleven_v3", alias="ELEVENLABS_MODEL_ID")

    default_tickers: str = Field(default="NVDA,AAPL,MSFT,DIS,NFLX,SPOT", alias="DEFAULT_TICKERS")
    top_k_chunks: int = Field(default=6, alias="TOP_K_CHUNKS")

    @property
    def postgres_url(self) -> str:
        if self.database_url:
            if self.database_url.startswith("postgres://"):
                return self.database_url.replace("postgres://", "postgresql://", 1)
            return self.database_url

        if not all([self.postgres_host, self.postgres_db, self.postgres_user, self.postgres_password]):
            raise ValueError(
                "Database configuration missing: set DATABASE_URL or POSTGRES_HOST/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD"
            )

        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def ticker_list(self) -> list[str]:
        return [t.strip().upper() for t in self.default_tickers.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()