from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    target_url: str = "https://quotes.toscrape.com/js/"
    headless_mode: bool = Field(
        default=True,
        validation_alias=AliasChoices("HEADLESS", "HEADLESS_MODE"),
    )
    database_url: str = "sqlite+aiosqlite:///extracted_data.db"
    database_path: Path = Path("extracted_data.db")
    report_dir: Path = Path("reports")
    log_file: Path = Path("logs/pipeline.jsonl")

settings = Settings()