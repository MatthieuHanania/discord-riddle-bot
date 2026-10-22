"""Asynchronous and guild-isolated storage service.

Ensures that every Discord server has its own riddle and target user list,
persisting state safely without blocking the asyncio event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from src.config import GUILDS_DIR, LEGACY_DATA_FILE, config

logger = logging.getLogger("riddlebot.storage")


class StorageService:
    """Manages guild-specific state persistence asynchronously."""

    def __init__(self, guilds_dir: Path = GUILDS_DIR) -> None:
        self.guilds_dir = guilds_dir
        self.guilds_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[int, asyncio.Lock] = {}
        self._cache: dict[int, dict[str, Any]] = {}
        self._legacy_template: dict[str, Any] | None = None

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    def _load_legacy_template(self) -> dict[str, Any]:
        """Loads data from the old single-file data.json if present."""
        if self._legacy_template is not None:
            return self._legacy_template

        template = {
            "riddle_text": config.default_riddle_text,
            "riddle_answer": config.default_riddle_answer,
            "target_user_ids": [],
            "definition": "",
            "indicators": "",
            "fodder": "",
            "par": 4,
        }

        if LEGACY_DATA_FILE.exists():
            try:
                with open(LEGACY_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    template["riddle_text"] = data.get("riddle_text", template["riddle_text"])
                    template["riddle_answer"] = data.get("riddle_answer", template["riddle_answer"])
                    template["target_user_ids"] = list(data.get("target_user_ids", []))
                    template["definition"] = data.get("definition", "")
                    template["indicators"] = data.get("indicators", "")
                    template["fodder"] = data.get("fodder", "")
                    template["par"] = data.get("par", 4)
                    logger.info("Migrated legacy template from data.json")
            except Exception as e:
                logger.warning("Could not read legacy data.json: %s", e)

        self._legacy_template = template
        return self._legacy_template

    def _guild_file_path(self, guild_id: int) -> Path:
        return self.guilds_dir / f"{guild_id}.json"

    def _read_guild_file_sync(self, guild_id: int) -> dict[str, Any]:
        path = self._guild_file_path(guild_id)
        if not path.exists():
            default_data = self._load_legacy_template().copy()
            default_data["target_user_ids"] = list(default_data.get("target_user_ids", []))
            self._write_guild_file_sync(guild_id, default_data)
            return default_data

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("riddle_text", config.default_riddle_text)
                data.setdefault("riddle_answer", config.default_riddle_answer)
                data.setdefault("target_user_ids", [])
                data.setdefault("definition", "")
                data.setdefault("indicators", "")
                data.setdefault("fodder", "")
                data.setdefault("par", 4)
                return data
        except Exception as e:
            logger.error("Failed to read data for guild %s: %s", guild_id, e)
            return {
                "riddle_text": config.default_riddle_text,
                "riddle_answer": config.default_riddle_answer,
                "target_user_ids": [],
                "definition": "",
                "indicators": "",
                "fodder": "",
                "par": 4,
            }

    def _write_guild_file_sync(self, guild_id: int, data: dict[str, Any]) -> None:
        path = self._guild_file_path(guild_id)
        tmp_path = self.guilds_dir / f"{guild_id}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            tmp_path.replace(path)
        except Exception as e:
            logger.error("Failed to save data for guild %s: %s", guild_id, e)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    async def get_guild_data(self, guild_id: int) -> dict[str, Any]:
        """Returns the guild's state dictionary."""
        lock = self._get_lock(guild_id)
        async with lock:
            if guild_id in self._cache:
                return self._cache[guild_id]
            data = await asyncio.to_thread(self._read_guild_file_sync, guild_id)
            self._cache[guild_id] = data
            return data

    async def save_guild_data(self, guild_id: int) -> None:
        """Flushes the cached guild data to disk."""
        lock = self._get_lock(guild_id)
        async with lock:
            if guild_id in self._cache:
                data = self._cache[guild_id]
                await asyncio.to_thread(self._write_guild_file_sync, guild_id, data)

    async def set_riddle(
        self,
        guild_id: int,
        text: str,
        answer: str,
        definition: str = "",
        indicators: str = "",
        fodder: str = "",
        par: int = 4,
    ) -> None:
        """Sets a new riddle, hints, and par for the specified guild."""
        data = await self.get_guild_data(guild_id)
        data["riddle_text"] = text.strip()
        data["riddle_answer"] = answer.strip()
        data["definition"] = definition.strip()
        data["indicators"] = indicators.strip()
        data["fodder"] = fodder.strip()
        data["par"] = par
        await self.save_guild_data(guild_id)
        logger.info("Updated riddle for guild %s", guild_id)

    async def get_targets(self, guild_id: int) -> set[int]:
        """Returns the set of targeted user IDs."""
        data = await self.get_guild_data(guild_id)
        return set(data.get("target_user_ids", []))

    async def add_target(self, guild_id: int, user_id: int) -> bool:
        """Adds a user to the targets list. Returns True if added, False if already present."""
        data = await self.get_guild_data(guild_id)
        targets = set(data.get("target_user_ids", []))
        if user_id in targets:
            return False
        targets.add(user_id)
        data["target_user_ids"] = list(targets)
        await self.save_guild_data(guild_id)
        return True

    async def remove_target(self, guild_id: int, user_id: int) -> bool:
        """Removes a user from targets. Returns True if removed, False if not in list."""
        data = await self.get_guild_data(guild_id)
        targets = set(data.get("target_user_ids", []))
        if user_id not in targets:
            return False
        targets.remove(user_id)
        data["target_user_ids"] = list(targets)
        await self.save_guild_data(guild_id)
        return True

    async def clear_targets(self, guild_id: int) -> int:
        """Clears all targets for this guild. Returns number of removed targets."""
        data = await self.get_guild_data(guild_id)
        old_count = len(data.get("target_user_ids", []))
        data["target_user_ids"] = []
        await self.save_guild_data(guild_id)
        return old_count

    async def check_answer(
        self, guild_id: int, user_id: int, raw_answer: str
    ) -> tuple[bool, int, str]:
        """Checks if a user's answer matches the current riddle.

        Returns:
            (is_correct: bool, remaining_targets_count: int, riddle_answer: str)
        """
        data = await self.get_guild_data(guild_id)
        expected_answer = str(data.get("riddle_answer", "")).strip().lower()
        clean_attempt = raw_answer.strip().lstrip(":").replace("|", "").strip().lower()

        if expected_answer and expected_answer in clean_attempt:
            # Correct answer! Remove from targets
            targets = set(data.get("target_user_ids", []))
            if user_id in targets:
                targets.remove(user_id)
                data["target_user_ids"] = list(targets)
                await self.save_guild_data(guild_id)
            return True, len(targets), expected_answer

        targets_count = len(data.get("target_user_ids", []))
        return False, targets_count, expected_answer
