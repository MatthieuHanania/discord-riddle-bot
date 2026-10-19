"""Service for handling punchlines and roasts."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path

from src.config import ROASTS_FILE

logger = logging.getLogger("riddlebot.roasts")

DEFAULT_ROASTS = [
    "Ton niveau est tellement bas que même le Wi-Fi du voisin ne veut pas te capter.",
    "T'as le charisme d'un PNJ dans un jeu des années 90.",
    "Si l'incompétence était une discipline olympique, tu serais porte-drapeau.",
    "Booba t'aurait éteint avec un seul freestyle de 15 secondes.",
    "Ton cerveau tourne sous Windows 95 avec une connexion ADSL 56k.",
]


class RoastService:
    """Provides randomized roasts loaded from JSON."""

    def __init__(self, file_path: Path = ROASTS_FILE) -> None:
        self.file_path = file_path
        self._roasts: list[str] = []
        self.load_roasts()

    def load_roasts(self) -> None:
        """Loads roasts from disk."""
        if not self.file_path.exists():
            self._roasts = DEFAULT_ROASTS.copy()
            logger.warning("Roasts file %s not found, using defaults", self.file_path)
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    self._roasts = [str(r) for r in data]
                    logger.info("Loaded %d roasts from %s", len(self._roasts), self.file_path)
                    return
        except Exception as e:
            logger.error("Error reading %s: %s", self.file_path, e)

        self._roasts = DEFAULT_ROASTS.copy()

    def get_random_roast(self) -> str:
        """Returns a random punchline."""
        if not self._roasts:
            return "T'as même pas assez de stats pour mériter une vraie punchline."
        return random.choice(self._roasts)

    def count(self) -> int:
        return len(self._roasts)
