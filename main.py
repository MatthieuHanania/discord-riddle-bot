"""Entry point for RiddleBot.

Initializes structured logging and starts the Discord bot lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from src.bot import RiddleBot
from src.config import config


def setup_logging() -> None:
    """Configures structured console logging."""
    # Ensure Windows console supports UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    log_format = "[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence overly verbose third-party logs
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.INFO)


async def main() -> None:
    """Validates configuration and launches the bot."""
    setup_logging()
    logger = logging.getLogger("riddlebot.main")

    try:
        config.validate()
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)

    logger.info("Starting RiddleBot...")
    bot = RiddleBot()

    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[+] RiddleBot gracefully stopped by user.")
