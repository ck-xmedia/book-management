import os
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    APP_ENV: str = "dev"
    DATA_DIR: Path = Path("./data")
    DATA_FILE: str = "books.json"
    DATA_LOCK_FILE: str = "books.json.lock"
    MAX_FILE_SIZE_MB: int = 10
    ENABLE_BACKUPS: bool = True
    BACKUP_EVERY_N_WRITES: int = 50
    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            APP_ENV=os.getenv("APP_ENV", "dev"),
            DATA_DIR=Path(os.getenv("DATA_DIR", "./data")),
            DATA_FILE=os.getenv("DATA_FILE", "books.json"),
            DATA_LOCK_FILE=os.getenv("DATA_LOCK_FILE", "books.json.lock"),
            MAX_FILE_SIZE_MB=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            ENABLE_BACKUPS=os.getenv("ENABLE_BACKUPS", "true").lower() in ("1", "true", "yes"),
            BACKUP_EVERY_N_WRITES=int(os.getenv("BACKUP_EVERY_N_WRITES", "50")),
            CORS_ORIGINS=os.getenv("CORS_ORIGINS", "*"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        )


def get_settings() -> Settings:
    return Settings.from_env()
