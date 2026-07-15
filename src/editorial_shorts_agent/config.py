from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TrendProviderName(StrEnum):
    FIXTURE = "fixture"
    YOUTUBE = "youtube"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ESA_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Editorial Shorts Agent"
    environment: str = "local"
    database_url: str = "sqlite+aiosqlite:///./editorial_shorts.db"
    trend_provider: TrendProviderName = TrendProviderName.FIXTURE
    youtube_api_key: SecretStr | None = None
    youtube_max_results: int = Field(default=25, ge=1, le=50)
    youtube_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
