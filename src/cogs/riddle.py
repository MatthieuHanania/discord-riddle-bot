"""Riddle management cog featuring slash commands, hybrid commands, and interactive views."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from src.ui.riddle_views import RiddleView

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.cogs.riddle")


class RiddleCog(commands.Cog, name="Énigme"):
    """Commandes liées à la gestion et résolution d'énigmes."""

    def __init__(self, bot: RiddleBot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="riddle",
        aliases=["enigme"],
        description="Affiche l'énigme active et notifie les joueurs ciblés.",
    )
    async def riddle_command(self, ctx: commands.Context) -> None:
        """Affiche la carte interactive de l'énigme avec bouton de réponse."""
        if not ctx.guild:
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un serveur.")
            return

        guild_data = await self.bot.storage.get_guild_data(ctx.guild.id)
        riddle_text = guild_data.get("riddle_text", "Aucune énigme configurée.")
        targets = set(guild_data.get("target_user_ids", []))

        embed = discord.Embed(
            title="🧩 Énigme en cours",
            description=f">>> ### \"{riddle_text}\"",
            color=discord.Color.blurple(),
        )

        if targets:
            mentions = " ".join(f"<@{uid}>" for uid in targets)
            embed.add_field(
                name=f"🎯 Joueurs ciblés ({len(targets)})",
                value=f"✨ {mentions}\n*Vous devez trouver la solution !*",
                inline=False,
            )
        else:
            embed.add_field(
                name="🎯 Joueurs ciblés",
                value="*Aucun joueur n'est ciblé pour le moment. Utilisez `/spy add @Membre` !*",
                inline=False,
            )

        embed.set_footer(
            text="💡 Cliquez sur 'Proposer une réponse' ci-dessous pour répondre discrètement."
        )

        view = RiddleView(self.bot)
        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)

    @app_commands.command(
        name="riddle_set",
        description="Définit une nouvelle énigme et sa réponse (Réservé aux gérants).",
    )
    @app_commands.describe(
        texte="L'énoncé de l'énigme à afficher publiquement",
        reponse="Le mot ou la phrase secrète qui valide l'énigme",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def set_riddle(
        self, interaction: discord.Interaction, texte: str, reponse: str
    ) -> None:
        """Permet de configurer une nouvelle énigme sans modifier de fichier JSON."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        await self.bot.storage.set_riddle(interaction.guild_id, texte, reponse)

        embed = discord.Embed(
            title="✅ Nouvelle énigme enregistrée !",
            description=(
                f"**Énoncé :**\n>>> {texte}\n\n"
                f"🤫 **Réponse secrète :** ||`{reponse}`||\n"
                f"*(Visible uniquement par vous)*"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="answer",
        aliases=["myanswer", "reponse"],
        description="Soumet une réponse à l'énigme active.",
    )
    @app_commands.describe(reponse="Votre tentative de réponse")
    async def answer_command(self, ctx: commands.Context, *, reponse: str) -> None:
        """Permet de répondre via une commande slash ou par préfixe."""
        if not ctx.guild:
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un serveur.")
            return

        guild_id = ctx.guild.id
        user_id = ctx.author.id

        targets = await self.bot.storage.get_targets(guild_id)
        if user_id not in targets:
            msg = "⚠️ Vous ne faites pas partie des joueurs ciblés par cette énigme !"
            if ctx.interaction:
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.send(msg)
            return

        is_correct, remaining_count, _ = await self.bot.storage.check_answer(
            guild_id, user_id, reponse
        )

        if is_correct:
            if ctx.interaction:
                await ctx.interaction.response.send_message(
                    "🎉 **Bravo tu as trouvé !**", ephemeral=True
                )
            else:
                try:
                    await ctx.message.delete()
                except discord.HTTPException:
                    pass

            if remaining_count > 0:
                remaining_targets = await self.bot.storage.get_targets(guild_id)
                mentions = " ".join(f"<@{uid}>" for uid in remaining_targets)
                await ctx.send(
                    f"🎉 {ctx.author.mention} a trouvé la réponse !\n"
                    f"👥 **Joueurs restants ({remaining_count}) :** {mentions}"
                )
            else:
                await ctx.send(
                    f"🎉 {ctx.author.mention} a trouvé la réponse !\n"
                    "🏆 **Félicitations, tous les joueurs ciblés ont trouvé !**"
                )
        else:
            if ctx.interaction:
                await ctx.interaction.response.send_message(
                    "❌ Cherche encore !", ephemeral=True
                )
            else:
                await ctx.send("cherche encore")


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(RiddleCog(bot))
