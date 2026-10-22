"""Roast and punchline cog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.cogs.roast")


class RoastCog(commands.Cog, name="Divertissement"):
    """Commandes humoristiques et clashs amicaux."""

    def __init__(self, bot: RiddleBot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="roast",
        aliases=["clash", "diss"],
        description="Envoie une punchline amicale bien sentie à un ami.",
    )
    @app_commands.describe(membre="Le membre à roaster")
    async def roast_command(
        self, ctx: commands.Context, membre: discord.Member | None = None
    ) -> None:
        """Envoie un roast aléatoire."""
        if membre is None:
            msg = "🔥 Mentionnez un ami à roaster ! Exemple : `/roast @Ami`"
            if ctx.interaction:
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.send(msg)
            return

        punchline = self.bot.roasts.get_random_roast()
        embed = discord.Embed(
            description=f"🔥 {membre.mention} **{punchline}**",
            color=discord.Color.red(),
        )

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(RoastCog(bot))
