"""Riddle management cog featuring slash commands, hybrid commands, and interactive views."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import discord
from discord import app_commands
from discord.ext import commands

from src.ui.riddle_views import RiddleConfigModal, RiddleView

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.cogs.riddle")


class RiddleCog(commands.Cog, name="Énigme"):
    """Commandes liées à la gestion et résolution d'énigmes."""

    def __init__(self, bot: RiddleBot) -> None:
        self.bot = bot

    def build_riddle_embed(self, guild_data: dict[str, Any]) -> discord.Embed:
        """Constructs the standard riddle embed card from guild state."""
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
            text="💡 Cliquez sur les boutons ci-dessous pour révéler des indices ou proposer une réponse."
        )
        return embed

    async def refresh_active_message(self, guild_id: int) -> bool:
        """Updates the latest riddle card in the guild with live data and dynamic button states."""
        guild_data = await self.bot.storage.get_guild_data(guild_id)
        channel_id = guild_data.get("last_channel_id")
        message_id = guild_data.get("last_message_id")

        if not channel_id or not message_id:
            return False

        try:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(channel_id)

            if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
                return False

            message = await channel.fetch_message(message_id)
            embed = self.build_riddle_embed(guild_data)
            view = RiddleView.create_for_guild(self.bot, guild_data)
            await message.edit(embed=embed, view=view)
            logger.info("Successfully refreshed active riddle message %s in channel %s", message_id, channel_id)
            return True
        except Exception as e:
            logger.debug("Could not refresh active riddle message for guild %s: %s", guild_id, e)
            return False

    @app_commands.command(
        name="riddle",
        description="Affiche l'énigme active et notifie les joueurs ciblés.",
    )
    async def riddle_command(self, interaction: discord.Interaction) -> None:
        """Affiche la carte interactive de l'énigme avec boutons d'indices dynamiques et réponse."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande ne peut être utilisée que dans un serveur.", ephemeral=True
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        riddle_text = str(guild_data.get("riddle_text", "")).strip()

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

        embed = self.build_riddle_embed(guild_data)
        view = RiddleView.create_for_guild(self.bot, guild_data)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        if msg:
            await self.bot.storage.set_last_riddle_message(interaction.guild_id, msg.channel.id, msg.id)

    @app_commands.command(
        name="riddle_set",
        description="Ouvre une fenêtre pour définir une nouvelle énigme et ses indices.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def set_riddle(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Ouvre le formulaire pop-up permettant de configurer une nouvelle énigme."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        modal = RiddleConfigModal(self.bot, is_edit=False)
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="riddle_edit",
        description="Ouvre une fenêtre pré-remplie pour modifier l'énigme et ses indices.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def edit_riddle(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Ouvre le formulaire pop-up pré-rempli avec les paramètres actuels de l'énigme."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        modal = RiddleConfigModal(self.bot, guild_data=guild_data, is_edit=True)
        await interaction.response.send_modal(modal)

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
