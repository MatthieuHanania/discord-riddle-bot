"""Configuration management for RiddleBot.

Loads environment variables from .env and provides strongly-typed configuration settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GUILDS_DIR = DATA_DIR / "guilds"
ROASTS_FILE = DATA_DIR / "roasts.json"

# Load local environment variables
load_dotenv(dotenv_path=BASE_DIR / ".env")


@dataclass(frozen=True)
class Config:
    """Application configuration container."""

    token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    dev_guild_id: int | None = field(
        default_factory=lambda: int(os.getenv("DEV_GUILD_ID")) if os.getenv("DEV_GUILD_ID") else None
    )
    default_riddle_text: str = field(
        default_factory=lambda: os.getenv("RIDDLE_TEXT", "")
    )
    default_riddle_answer: str = field(
        default_factory=lambda: os.getenv("RIDDLE_ANSWER", "")
    )

    def validate(self) -> None:
        """Validates critical settings."""
        if not self.token or self.token == "YOUR_DISCORD_TOKEN_HERE":
            raise ValueError(
                "DISCORD_TOKEN is missing or invalid in .env file! "
                "Please configure your bot token before starting."
            )


# Global singleton instance
config = Config()
