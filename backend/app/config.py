from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    """Runtime configuration (TRD 6). Every field is overridable by an env var of the same name."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "aether_bust"
    MODEL_WEIGHTS_PATH: str = ""
    SEED: int = 26079
    CORS_ORIGINS: str = "http://localhost:5173"
    API_VERSION: str = "1.0.0"
    TORCH_NUM_THREADS: int = Field(default=1, ge=1)

    ARTIFACTS_DIR: str = str(BACKEND_ROOT / "artifacts")
    
    # Gemini Chatbot Config
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_PRO: str = "gemini-2.5-pro"
    GEMINI_MODEL_FAST: str = "gemini-2.5-flash"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _strip_origins(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def artifacts_path(self) -> Path:
        return Path(self.ARTIFACTS_DIR)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
