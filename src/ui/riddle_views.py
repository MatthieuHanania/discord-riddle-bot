"""Modern Discord UI components: Interactive Buttons and Modals for RiddleBot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from src.bot import RiddleBot

logger = logging.getLogger("riddlebot.ui")


class RiddleAnswerModal(discord.ui.Modal, title="🧩 Proposer une réponse"):
    """Modal popup allowing users to privately submit their riddle guess."""

    answer_input = discord.ui.TextInput(
        label="Votre réponse :",
        placeholder="Entrez votre mot ou phrase de réponse...",
        min_length=1,
        max_length=120,
        style=discord.TextStyle.short,
        required=True,
    )

    def __init__(self, bot: RiddleBot) -> None:
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette action doit être effectuée au sein d'un serveur Discord.",
                ephemeral=True,
            )
            return

        guild_id = interaction.guild_id
        user_id = interaction.user.id
        raw_answer = self.answer_input.value

        targets = await self.bot.storage.get_targets(guild_id)
        if user_id not in targets:
            await interaction.response.send_message(
                "⚠️ **Vous ne faites pas partie des joueurs ciblés par cette énigme !**\n"
                "Demandez à un administrateur ou utilisez `/spy add @vous` pour être ciblé.",
                ephemeral=True,
            )
            return

        is_correct, remaining_count, _ = await self.bot.storage.check_answer(
            guild_id, user_id, raw_answer
        )

        if is_correct:
            # Send private confirmation first
            await interaction.response.send_message(
                "🎉 **Excellente déduction !** Votre réponse a été validée avec succès.",
                ephemeral=True,
            )

            # Announce publicly in the channel
            if remaining_count > 0:
                remaining_targets = await self.bot.storage.get_targets(guild_id)
                mentions = " ".join(f"<@{uid}>" for uid in remaining_targets)
                embed = discord.Embed(
                    title="🎉 Énigme résolue !",
                    description=(
                        f"👏 {interaction.user.mention} a trouvé la bonne réponse !\n\n"
                        f"👥 **Joueurs restants à devoir trouver ({remaining_count}) :**\n{mentions}"
                    ),
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="🏆 Victoire collective !",
                    description=(
                        f"👏 {interaction.user.mention} a trouvé la bonne réponse !\n\n"
                        "🎊 **Tous les joueurs ciblés ont désormais résolu l'énigme !**"
                    ),
                    color=discord.Color.gold(),
                )

            if interaction.channel and hasattr(interaction.channel, "send"):
                await interaction.channel.send(embed=embed)

        else:
            # Ephemeral response to avoid leaking guesses or spamming chat
            await interaction.response.send_message(
                f"❌ **Raté !** `{raw_answer}` n'est pas la bonne réponse. Cherche encore !",
                ephemeral=True,
            )


class RiddleView(discord.ui.View):
    """Persistent view with interactive buttons for the riddle card."""

    def __init__(self, bot: RiddleBot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Proposer une réponse",
        style=discord.ButtonStyle.success,
        emoji="🔑",
        custom_id="riddle:submit_answer_button",
        row=0,
    )
    async def submit_answer_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Opens the answer modal for the interacting user."""
        modal = RiddleAnswerModal(self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Règles & Aide",
        style=discord.ButtonStyle.secondary,
        emoji="ℹ️",
        custom_id="riddle:rules_button",
        row=0,
    )
    async def rules_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Shows private instructions on how the riddle game works."""
        embed = discord.Embed(
            title="📖 Comment jouer à l'énigme ?",
            description=(
                "1. **Indices :** Cliquez sur **Définition**, **Indicateurs** ou **Fodder** pour révéler des indices sans spoiler.\n"
                "2. **Ciblage :** Seuls les joueurs ajoutés à la liste cible (`/spy add @Joueur`) doivent répondre.\n"
                "3. **Répondre discrètement :** Cliquez sur le bouton vert **🔑 Proposer une réponse**.\n"
                "4. **Anti-Triche :** Votre proposition s'ouvre dans une fenêtre privée pop-up : personne d'autre ne voit vos essais.\n"
                "5. **Victoire :** Dès que vous trouvez le mot juste, vous êtes retiré de la liste cible et le serveur est notifié !"
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Définition",
        style=discord.ButtonStyle.primary,
        emoji="📖",
        custom_id="riddle:definition_button",
        row=1,
    )
    async def definition_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Displays the riddle definition hint privately to the user."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette action doit être effectuée au sein d'un serveur Discord.",
                ephemeral=True,
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        definition = guild_data.get("definition", "").strip()

        if not definition:
            await interaction.response.send_message(
                "ℹ️ Aucune définition n'a été configurée pour cette énigme.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📖 Indice : Définition",
            description=f">>> {definition}",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Indicateurs",
        style=discord.ButtonStyle.primary,
        emoji="🔍",
        custom_id="riddle:indicators_button",
        row=1,
    )
    async def indicators_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Displays the riddle indicators hint privately to the user."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette action doit être effectuée au sein d'un serveur Discord.",
                ephemeral=True,
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        indicators = guild_data.get("indicators", "").strip()

        if not indicators:
            await interaction.response.send_message(
                "ℹ️ Aucun indicateur n'a été configuré pour cette énigme.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🔍 Indice : Indicateurs",
            description=f">>> {indicators}",
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Fodder",
        style=discord.ButtonStyle.primary,
        emoji="🧩",
        custom_id="riddle:fodder_button",
        row=1,
    )
    async def fodder_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Displays the riddle fodder hint privately to the user."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette action doit être effectuée au sein d'un serveur Discord.",
                ephemeral=True,
            )
            return

        guild_data = await self.bot.storage.get_guild_data(interaction.guild_id)
        fodder = guild_data.get("fodder", "").strip()

        if not fodder:
            await interaction.response.send_message(
                "ℹ️ Aucun fodder n'a été configuré pour cette énigme.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🧩 Indice : Fodder",
            description=f">>> {fodder}",
            color=discord.Color.teal(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
