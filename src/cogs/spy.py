"""Target user (spy) management cog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.cogs.spy")


class SpyCog(commands.Cog, name="Ciblage"):
    """Gestion des joueurs ciblés par les énigmes."""

    def __init__(self, bot: RiddleBot) -> None:
        self.bot = bot

    # Slash command group: /spy
    spy_group = app_commands.Group(name="spy", description="Gestion des joueurs ciblés pour l'énigme")

    @spy_group.command(name="add", description="Ajoute un membre à la liste des joueurs ciblés")
    @app_commands.describe(membre="Le membre Discord à cibler")
    async def slash_spy_add(
        self, interaction: discord.Interaction, membre: discord.Member
    ) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("❌ Réservé aux serveurs.", ephemeral=True)
            return

        added = await self.bot.storage.add_target(interaction.guild_id, membre.id)
        if added:
            await interaction.response.send_message(
                f"🎯 {membre.mention} a été ajouté aux joueurs ciblés !",
            )
        else:
            await interaction.response.send_message(
                f"ℹ️ {membre.mention} est déjà dans la liste des joueurs ciblés.",
                ephemeral=True,
            )

    @spy_group.command(name="remove", description="Retire un membre de la liste des joueurs ciblés")
    @app_commands.describe(membre="Le membre Discord à retirer")
    async def slash_spy_remove(
        self, interaction: discord.Interaction, membre: discord.Member
    ) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("❌ Réservé aux serveurs.", ephemeral=True)
            return

        removed = await self.bot.storage.remove_target(interaction.guild_id, membre.id)
        if removed:
            await interaction.response.send_message(
                f"🗑️ {membre.mention} a été retiré de la liste des cibles.",
            )
        else:
            await interaction.response.send_message(
                f"⚠️ {membre.mention} ne faisait pas partie de la liste.",
                ephemeral=True,
            )

    @spy_group.command(name="list", description="Affiche tous les joueurs actuellement ciblés")
    async def slash_spy_list(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("❌ Réservé aux serveurs.", ephemeral=True)
            return

        targets = await self.bot.storage.get_targets(interaction.guild_id)
        if not targets:
            await interaction.response.send_message(
                "ℹ️ **Aucun joueur n'est ciblé pour le moment.** Utilisez `/spy add @Membre` !"
            )
            return

        mentions = "\n".join(f"• <@{uid}>" for uid in targets)
        embed = discord.Embed(
            title=f"🎯 Joueurs ciblés actuels ({len(targets)})",
            description=mentions,
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    @spy_group.command(name="clear", description="Réinitialise et vide la liste des cibles")
    async def slash_spy_clear(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("❌ Réservé aux serveurs.", ephemeral=True)
            return

        count = await self.bot.storage.clear_targets(interaction.guild_id)
        await interaction.response.send_message(
            f"🔄 Liste réinitialisée : **{count}** joueur(s) retiré(s) de la liste."
        )


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(SpyCog(bot))
