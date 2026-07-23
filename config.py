from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CampusConecta AI")
    environment: str = os.getenv("ENVIRONMENT", "development")
    data_path: Path = Path(
        os.getenv("DATA_PATH", str(BASE_DIR / "data" / "servicios_estudiantiles.csv"))
    )
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    top_k: int = int(os.getenv("TOP_K", "4"))
    min_relevance: float = float(os.getenv("MIN_RELEVANCE", "0.05"))
    allow_fallback: bool = os.getenv("ALLOW_FALLBACK", "true").lower() == "true"


settings = Settings()
