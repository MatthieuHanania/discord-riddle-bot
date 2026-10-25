"""General commands: help, ping, and bot presentation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.cogs.general")


class GeneralCog(commands.Cog, name="Général"):
    """Commandes d'information, d'aide et de diagnostic."""

    def __init__(self, bot: RiddleBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Affiche le guide complet du bot et la liste des commandes.",
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Affiche le panneau d'aide détaillé du bot."""
        embed = discord.Embed(
            title="🤖 **RiddleBot — Guide & Commandes**",
            description=(
                "Bienvenue sur **RiddleBot** ! Un bot moderne d'énigmes interactives et de divertissement.\n"
                "Toutes les fonctionnalités s'utilisent via les commandes slash (`/`)."
            ),
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="🧩 1. Énigmes interactives",
            value=(
                "• `/riddle` : Affiche l'énigme active et notifie les joueurs ciblés.\n"
                "• **Bouton 'Proposer une réponse'** : Ouvre un pop-up privé sans spoiler le salon !\n"
                "• `/answer <texte>` : Soumet une réponse directement par commande.\n"
                "• `/riddle_set <texte> <réponse>` : *(Admin)* Configure une nouvelle énigme."
            ),
            inline=False,
        )

        embed.add_field(
            name="🎯 2. Ciblage des joueurs",
            value=(
                "• `/spy add @Membre` : Ajoute un joueur à la liste cible.\n"
                "• `/spy remove @Membre` : Retire un joueur de la liste.\n"
                "• `/spy list` : Affiche les joueurs qui doivent encore répondre.\n"
                "• `/spy clear` : Réinitialise toute la liste des cibles."
            ),
            inline=False,
        )

        embed.add_field(
            name="🔥 3. Fun & Clash",
            value="• `/roast @Membre` : Envoie une punchline amicale et percutante !",
            inline=False,
        )

        embed.add_field(
            name="⚙️ 4. Diagnostic",
            value="• `/ping` : Affiche la latence du bot et l'état de connexion.",
            inline=False,
        )

        embed.set_footer(
            text="RiddleBot • Développé en Python moderne avec discord.py et uv 🚀"
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ping",
        description="Vérifie la latence et l'état du bot.",
    )
    async def ping_command(self, interaction: discord.Interaction) -> None:
        """Vérifie la latence de l'API Discord."""
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"Latence de l'API Discord : **`{latency_ms} ms`**",
            color=discord.Color.green() if latency_ms < 150 else discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Répond gentiment lorsque quelqu'un mentionne le bot seul."""
        if message.author.bot:
            return

        # Check if the message is purely a mention of the bot
        if (
            self.bot.user in message.mentions
            and len(message.content.strip().split()) == 1
        ):
            await message.channel.send(
                f"👋 Bonjour {message.author.mention} ! Utilisez `/help` pour voir le guide complet !"
            )


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(GeneralCog(bot))
