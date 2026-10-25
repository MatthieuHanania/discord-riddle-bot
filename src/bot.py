"""Custom Discord Bot subclass with setup_hook, cog management, and error handling."""

from __future__ import annotations

import logging
import discord
from discord import app_commands
from discord.ext import commands

from src.config import config
from src.services.roast_service import RoastService
from src.services.storage import StorageService
from src.ui.riddle_views import RiddleView

logger = logging.getLogger("riddlebot.bot")

INITIAL_EXTENSIONS = [
    "src.cogs.general",
    "src.cogs.riddle",
    "src.cogs.spy",
    "src.cogs.roast",
]


class RiddleBot(commands.Bot):
    """Modern modular Discord Bot managing riddles, target tracking, and roasts."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None,
        )

        self.storage = StorageService()
        self.roasts = RoastService()

    async def setup_hook(self) -> None:
        """Called before the bot logs in. Loads cogs, persistent views, and syncs tree."""
        logger.info("Initializing bot setup hook...")

        # Load all modular cogs
        for extension in INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
                logger.info("Loaded extension: %s", extension)
            except Exception as e:
                logger.error("Failed to load extension %s: %s", extension, e, exc_info=True)

        # Register persistent UI views so buttons work even after a restart
        self.add_view(RiddleView(self))

        # Register tree error handler
        self.tree.on_error = self.on_app_command_error

        # Sync Slash Commands (App Commands)
        if config.dev_guild_id:
            dev_guild = discord.Object(id=config.dev_guild_id)
            self.tree.copy_global_to(guild=dev_guild)
            await self.tree.sync(guild=dev_guild)
            logger.info("Slash commands synced INSTANTLY to dev guild: %s", config.dev_guild_id)
        else:
            await self.tree.sync()
            logger.info("Slash commands synced globally.")

    async def on_ready(self) -> None:
        """Fires when the bot connection is established."""
        guild_count = len(self.guilds)
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Connected to %d guild(s)", guild_count)

        # Set rich presence activity
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="/riddle • /help",
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handles errors from slash command interactions."""
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ Vous n'avez pas la permission d'utiliser cette commande."
        else:
            logger.error("Slash command error in %s: %s", interaction.command, error, exc_info=True)
            msg = "⚠️ Une erreur est survenue lors de l'exécution de la commande."

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
