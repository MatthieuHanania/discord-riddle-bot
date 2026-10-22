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

    # Legacy prefix command fallback for backwards compatibility (@Bot spy ...)
    @commands.command(name="spy", aliases=["target"])
    async def prefix_spy(
        self, ctx: commands.Context, action_or_user: str | None = None, user: discord.User | None = None
    ) -> None:
        """Commande classique par préfixe pour gérer les cibles."""
        if not ctx.guild:
            await ctx.send("❌ Réservé aux serveurs.")
            return

        guild_id = ctx.guild.id
        bot_tag = f"@{self.bot.user.name}"

        if action_or_user is None or action_or_user.lower() in ["list", "show"]:
            targets = await self.bot.storage.get_targets(guild_id)
            if not targets:
                await ctx.send(f"ℹ️ Aucun joueur n'est ciblé actuellement. Utilisez `{bot_tag} spy @Membre` !")
            else:
                mentions = " ".join(f"<@{uid}>" for uid in targets)
                await ctx.send(f"🎯 **Joueurs ciblés actuels ({len(targets)}) :** {mentions}")
            return

        action_lower = action_or_user.lower()
        if action_lower in ["reset", "clear"]:
            count = await self.bot.storage.clear_targets(guild_id)
            await ctx.send(f"🔄 Liste réinitialisée : {count} joueur(s) retiré(s).")
            return

        if action_lower in ["add"]:
            if user is None:
                await ctx.send(f"⚠️ Mentionnez un membre à ajouter ! Ex: `{bot_tag} spy add @Membre`")
                return
            target_to_add = user
        elif action_lower in ["remove", "rm", "del", "delete"]:
            if user is None:
                await ctx.send(f"⚠️ Mentionnez un membre à retirer ! Ex: `{bot_tag} spy remove @Membre`")
                return
            removed = await self.bot.storage.remove_target(guild_id, user.id)
            if removed:
                await ctx.send(f"🗑️ {user.mention} a été retiré de la liste des joueurs ciblés !")
            else:
                await ctx.send(f"⚠️ {user.mention} n'était pas dans la liste.")
            return
        else:
            try:
                target_to_add = await commands.UserConverter().convert(ctx, action_or_user)
            except commands.BadArgument:
                await ctx.send(
                    f"⚠️ Syntaxe invalide. Utilisez `/spy` ou `{bot_tag} spy @Membre`."
                )
                return

        added = await self.bot.storage.add_target(guild_id, target_to_add.id)
        if added:
            await ctx.send(f"🎯 {target_to_add.mention} a été ajouté aux joueurs ciblés !")
        else:
            await ctx.send(f"ℹ️ {target_to_add.mention} est déjà dans la liste.")

    @commands.command(name="resetspy", aliases=["clearspy", "unspy"])
    async def prefix_reset_spy(self, ctx: commands.Context) -> None:
        """Réinitialise tous les joueurs ciblés."""
        if not ctx.guild:
            return
        count = await self.bot.storage.clear_targets(ctx.guild.id)
        await ctx.send(f"🔄 Tous les joueurs ciblés ({count}) ont été réinitialisés !")


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(SpyCog(bot))
