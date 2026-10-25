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

    @app_commands.command(
        name="riddle",
        description="Affiche l'énigme active et notifie les joueurs ciblés.",
    )
    async def riddle_command(self, interaction: discord.Interaction) -> None:
        """Affiche la carte interactive de l'énigme avec bouton de réponse."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande ne peut être utilisée que dans un serveur.", ephemeral=True
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        riddle_text = str(guild_data.get("riddle_text", "")).strip()
        targets = set(guild_data.get("target_user_ids", []))

        if not riddle_text:
            embed = discord.Embed(
                title="🧩 Aucune énigme active",
                description=(
                    "Il n'y a aucune énigme configurée pour le moment sur ce serveur.\n\n"
                    "💡 Un gestionnaire peut en définir une avec la commande `/riddle_set` !"
                ),
                color=discord.Color.orange(),
            )
            await interaction.response.send_message(embed=embed)
            return

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
        await interaction.response.send_message(embed=embed, view=view)

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

    @app_commands.command(
        name="answer",
        description="Soumet une réponse à l'énigme active.",
    )
    @app_commands.describe(reponse="Votre tentative de réponse")
    async def answer_command(self, interaction: discord.Interaction, reponse: str) -> None:
        """Permet de répondre via une commande slash privée."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande ne peut être utilisée que dans un serveur.", ephemeral=True
            )
            return

        guild_id = interaction.guild_id
        user_id = interaction.user.id

        guild_data = await self.bot.storage.get_guild_data(guild_id)
        if not str(guild_data.get("riddle_text", "")).strip() or not str(guild_data.get("riddle_answer", "")).strip():
            await interaction.response.send_message(
                "⚠️ Aucune énigme n'est actuellement active sur ce serveur.", ephemeral=True
            )
            return

        targets = await self.bot.storage.get_targets(guild_id)
        if user_id not in targets:
            await interaction.response.send_message(
                "⚠️ Vous ne faites pas partie des joueurs ciblés par cette énigme !", ephemeral=True
            )
            return

        is_correct, remaining_count, _ = await self.bot.storage.check_answer(
            guild_id, user_id, reponse
        )

        if is_correct:
            await interaction.response.send_message(
                "🎉 **Bravo tu as trouvé !**", ephemeral=True
            )

            if interaction.channel and hasattr(interaction.channel, "send"):
                if remaining_count > 0:
                    remaining_targets = await self.bot.storage.get_targets(guild_id)
                    mentions = " ".join(f"<@{uid}>" for uid in remaining_targets)
                    await interaction.channel.send(
                        f"🎉 {interaction.user.mention} a trouvé la réponse !\n"
                        f"👥 **Joueurs restants ({remaining_count}) :** {mentions}"
                    )
                else:
                    await interaction.channel.send(
                        f"🎉 {interaction.user.mention} a trouvé la réponse !\n"
                        "🏆 **Félicitations, tous les joueurs ciblés ont trouvé !**"
                    )
        else:
            await interaction.response.send_message(
                "❌ Cherche encore !", ephemeral=True
            )


async def setup(bot: RiddleBot) -> None:
    await bot.add_cog(RiddleCog(bot))
