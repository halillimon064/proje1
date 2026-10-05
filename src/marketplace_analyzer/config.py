"""Application configuration loaded from YAML and environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml


@dataclass(frozen=True)
class AppConfig:
    data: dict[str, Any]

    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", self.data["database"]["url"])


def load_config(path: str | Path = "settings.yaml", env_path: str | Path = ".env") -> AppConfig:
    load_dotenv(env_path, override=False)
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if "database" not in data or "import" not in data:
        raise ValueError("Yapılandırmada database ve import bölümleri bulunmalıdır.")
    return AppConfig(data=data)
