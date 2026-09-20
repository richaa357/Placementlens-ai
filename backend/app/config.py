"""Application configuration.

All settings can be overridden through environment variables (see .env.example).
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PlacementLens AI"
    # SQLite by default for development; point at PostgreSQL in production.
    database_url: str = f"sqlite:///{BACKEND_DIR / 'placementlens.db'}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Dataset used to seed the database on first start. The bundled dataset is a
    # clearly labelled DEMONSTRATION dataset - see app/data/demo_dataset.json.
    dataset_path: str = str(DATA_DIR / "demo_dataset.json")
    dataset_is_demo: bool = True

    # Semantic analysis. sentence-transformers is optional (large download); when
    # it is unavailable the pipeline falls back to a Word2Vec / TF-IDF-SVD model
    # trained on the local corpus. See app/nlp/embeddings.py.
    enable_sentence_transformers: bool = False
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
