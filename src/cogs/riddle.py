"""Riddle management cog featuring slash commands, hybrid commands, and interactive views."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

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

    def build_riddle_embed(self, guild_data: dict[str, Any]) -> discord.Embed:
        """Constructs the standard riddle embed card from guild state."""
        riddle_text = guild_data.get("riddle_text", "Aucune énigme configurée.")
        targets = set(guild_data.get("target_user_ids", []))
        par = guild_data.get("par", 4)

        embed = discord.Embed(
            title="🧩 Énigme en cours",
            description=f">>> ### \"{riddle_text}\"",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="⛳ Par",
            value=f"**{par}** essai{'s' if par > 1 else ''}",
            inline=True,
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

    @commands.hybrid_command(
        name="riddle",
        aliases=["enigme"],
        description="Affiche l'énigme active et notifie les joueurs ciblés.",
    )
    async def riddle_command(self, ctx: commands.Context) -> None:
        """Affiche la carte interactive de l'énigme avec boutons d'indices dynamiques et réponse."""
        if not ctx.guild:
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un serveur.")
            return

        guild_data = await self.bot.storage.get_guild_data(ctx.guild.id)
        embed = self.build_riddle_embed(guild_data)
        view = RiddleView.create_for_guild(self.bot, guild_data)

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed, view=view)
            msg = await ctx.interaction.original_response()
        else:
            msg = await ctx.send(embed=embed, view=view)

        if msg:
            await self.bot.storage.set_last_riddle_message(ctx.guild.id, msg.channel.id, msg.id)

    @app_commands.command(
        name="riddle_set",
        description="Définit une nouvelle énigme avec sa définition, ses indicateurs, son fodder et son par.",
    )
    @app_commands.describe(
        texte="L'énoncé de l'énigme à afficher publiquement",
        reponse="Le mot ou la phrase secrète qui valide l'énigme",
        definition="La définition du mot à deviner (ex: 9-12)",
        indicateurs="Les indicateurs / opérations (ex: - (deletion) and + (addition))",
        fodder="Le matériau / lettres de base (ex: '12', '55', and 'n'. (substitute))",
        par="Nombre moyen d'essais attendu par joueur (défaut : 4)",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def set_riddle(
        self,
        interaction: discord.Interaction,
        texte: str,
        reponse: str,
        definition: str,
        indicateurs: str,
        fodder: str,
        par: app_commands.Range[int, 1, 100] = 4,
    ) -> None:
        """Permet de configurer une nouvelle énigme et ses indices sans modifier de fichier JSON."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        await self.bot.storage.set_riddle(
            interaction.guild_id,
            text=texte,
            answer=reponse,
            definition=definition,
            indicators=indicateurs,
            fodder=fodder,
            par=par,
        )

        refreshed = await self.refresh_active_message(interaction.guild_id)
        refresh_note = "\n*(La carte de l'énigme affichée a été actualisée en direct !)*" if refreshed else ""

        embed = discord.Embed(
            title="✅ Nouvelle énigme enregistrée !",
            description=(
                f"**Énoncé :**\n>>> {texte}\n\n"
                f"🤫 **Réponse secrète :** ||`{reponse}`||\n"
                f"📖 **Définition :** {definition}\n"
                f"🔍 **Indicateurs :** {indicateurs}\n"
                f"🧩 **Fodder :** {fodder}\n"
                f"⛳ **Par :** {par} essai{'s' if par > 1 else ''}\n"
                f"{refresh_note}\n\n"
                f"*(Visible uniquement par vous)*"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="riddle_edit",
        description="Modifie un ou plusieurs éléments de l'énigme (définition, indicateurs, fodder, etc.).",
    )
    @app_commands.describe(
        definition="Nouvelle définition du mot à deviner",
        indicateurs="Nouveaux indicateurs / opérations",
        fodder="Nouveau fodder / lettres de base",
        par="Nouveau par (nombre moyen d'essais attendu)",
        texte="Nouvel énoncé de l'énigme",
        reponse="Nouvelle réponse secrète",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def edit_riddle(
        self,
        interaction: discord.Interaction,
        definition: str | None = None,
        indicateurs: str | None = None,
        fodder: str | None = None,
        par: app_commands.Range[int, 1, 100] | None = None,
        texte: str | None = None,
        reponse: str | None = None,
    ) -> None:
        """Permet de modifier unitairement ou collectivement des éléments de l'énigme."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        if all(v is None for v in [definition, indicateurs, fodder, par, texte, reponse]):
            await interaction.response.send_message(
                "⚠️ Veuillez renseigner au moins un champ à modifier (définition, indicateurs, fodder, etc.).",
                ephemeral=True,
            )
            return

        data = await self.bot.storage.edit_riddle(
            interaction.guild_id,
            text=texte,
            answer=reponse,
            definition=definition,
            indicators=indicateurs,
            fodder=fodder,
            par=par,
        )

        refreshed = await self.refresh_active_message(interaction.guild_id)
        refresh_note = "\n*(La carte de l'énigme affichée et ses boutons ont été actualisés en direct !)*" if refreshed else ""

        details = []
        if texte is not None:
            details.append(f"**Énoncé :** >>> {texte}")
        if reponse is not None:
            details.append(f"🤫 **Réponse :** ||`{reponse}`||")
        if definition is not None:
            details.append(f"📖 **Définition :** {definition}")
        if indicateurs is not None:
            details.append(f"🔍 **Indicateurs :** {indicateurs}")
        if fodder is not None:
            details.append(f"🧩 **Fodder :** {fodder}")
        if par is not None:
            details.append(f"⛳ **Par :** {par} essai{'s' if par > 1 else ''}")

        embed = discord.Embed(
            title="✏️ Énigme mise à jour !",
            description="\n".join(details) + f"\n{refresh_note}\n\n*(Visible uniquement par vous)*",
            color=discord.Color.teal(),
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
