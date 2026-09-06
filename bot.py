import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv, set_key, unset_key, find_dotenv

# Ensure UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from local .env file
ENV_FILE = find_dotenv() or ".env"
load_dotenv(ENV_FILE)

TOKEN = os.getenv("DISCORD_TOKEN")

# Configure Discord gateway intents (Message Content Intent required)
intents = discord.Intents.default()
intents.message_content = True

# Primary trigger mechanism: Mentioning @RiddleBot directly in Discord
bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    intents=intents
)

# Remove default help command to allow custom help alias
bot.remove_command("help")

# Target user IDs set (loaded from .env if present, or managed dynamically in Discord)
raw_target_ids = os.getenv("TARGET_USER_IDS") or os.getenv("TARGET_USER_ID", "")
TARGET_USER_IDS = set()
if raw_target_ids:
    for item in raw_target_ids.split(","):
        item = item.strip()
        if item.isdigit():
            TARGET_USER_IDS.add(int(item))

RIDDLE_TEXT = os.getenv("RIDDLE_TEXT", "Le détective anglais est a moitié enfermé")
ANSWER = os.getenv("RIDDLE_ANSWER", "lock")


def save_targets_to_env():
    """Saves current TARGET_USER_IDS to .env and cleans up legacy single TARGET_USER_ID key."""
    if TARGET_USER_IDS:
        ids_str = ",".join(str(uid) for uid in TARGET_USER_IDS)
        set_key(ENV_FILE, "TARGET_USER_IDS", ids_str)
        try:
            unset_key(ENV_FILE, "TARGET_USER_ID")
        except Exception:
            pass
    else:
        try:
            unset_key(ENV_FILE, "TARGET_USER_IDS")
            unset_key(ENV_FILE, "TARGET_USER_ID")
        except Exception:
            pass


@bot.event
async def on_ready():
    print(f"[+] Bot successfully connected as {bot.user} (ID: {bot.user.id})")
    print(f"[+] Trigger mode: Mention '@{bot.user.name}' directly in Discord")
    if TARGET_USER_IDS:
        print(f"[+] Target User IDs: {', '.join(str(u) for u in TARGET_USER_IDS)}")
    else:
        print("[+] Target User IDs: NONE (Use @Bot spy @User)")
    print("--------------------------------------------------")


@bot.command(name="hello", aliases=["help", "info", "guide", "hi"])
async def show_hello(ctx):
    """Presents the bot and explains how to use all commands."""
    bot_name = bot.user.name
    embed = discord.Embed(
        title="🤖 **RiddleBot — Guide & Présentation**",
        description=(
            "Bonjour ! Je suis votre bot d'énigme interactif (toujours actif).\n"
            "Taggez-moi simplement dans Discord pour m'utiliser :"
        ),
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎯 1. Cibler des Joueurs (Spy / Reset)",
        value=(
            f"• `@{bot_name} spy @Membre` (ou `spy add @Membre`) : Ajoute un joueur ciblée dans `.env`.\n"
            f"• `@{bot_name} spy remove @Membre` : Retire un joueur de la liste ciblée.\n"
            f"• `@{bot_name} spy list` : Affiche la liste des joueurs ciblés.\n"
            f"• `@{bot_name} resetspy` (ou `spy reset`) : Supprime tous les joueurs ciblés."
        ),
        inline=False
    )
    
    embed.add_field(
        name="🧩 2. Poser l'Énigme",
        value=f"• `@{bot_name} riddle` (ou `enigme`) : Affiche l'énigme et mentionne les joueurs ciblés.",
        inline=False
    )
    
    embed.add_field(
        name="🔑 3. Soumettre une Réponse",
        value=(
            f"• `@{bot_name} myanswer <réponse>` (ex: `@{bot_name} myanswer bottom` ou `@{bot_name} myanswer:bottom`)\n"
            "• Si c'est correct : le bot répond `bravo tu as trouvé`.\n"
            "• Sinon : le bot répond `cherche encore`."
        ),
        inline=False
    )
    
    embed.set_footer(text="RiddleBot • Toujours actif — Amusez-vous bien !")
    await ctx.send(embed=embed)


@bot.command(name="riddle", aliases=["enigme"])
async def show_riddle(ctx):
    """Displays the riddle and mentions all targeted users if configured."""
    bot_tag = f"@{bot.user.name}"
    if TARGET_USER_IDS:
        mentions = " ".join(f"<@{uid}>" for uid in TARGET_USER_IDS)
        await ctx.send(
            f"✨ {mentions} trouvez la solution à l'énigme suivante :\n"
            f"> 🧩 **\"{RIDDLE_TEXT}\"**\n\n"
            f"💡 *Pour répondre, taggue-moi et écris :* `{bot_tag} myanswer <ta_réponse>` *(ex: `{bot_tag} myanswer bottom`)*"
        )
    else:
        await ctx.send(
            f"🧩 **Énigme :**\n"
            f"> **\"{RIDDLE_TEXT}\"**\n\n"
            f"⚠️ *(Aucun joueur n'est ciblé. Taggez-moi avec `{bot_tag} spy @Membre` pour en ajouter !)*"
        )


async def _show_spy_list(ctx):
    bot_tag = f"@{bot.user.name}"
    if not TARGET_USER_IDS:
        await ctx.send(f"ℹ️ Aucun joueur n'est ciblé pour le moment. Taggez-moi avec `{bot_tag} spy @Membre` !")
        return
    mentions = " ".join(f"<@{uid}>" for uid in TARGET_USER_IDS)
    await ctx.send(f"🎯 **Joueurs ciblés actuels ({len(TARGET_USER_IDS)}) :** {mentions}")


@bot.command(name="spy", aliases=["target"])
async def spy_command(ctx, action_or_user: str = None, user: discord.User = None):
    """
    Manages target users (spy list).
    Usage:
      @Bot spy @User
      @Bot spy add @User
      @Bot spy remove @User
      @Bot spy list
      @Bot spy reset
    """
    global TARGET_USER_IDS
    bot_tag = f"@{bot.user.name}"

    if action_or_user is None:
        await _show_spy_list(ctx)
        return

    action_lower = action_or_user.lower()

    if action_lower in ["list", "show"]:
        await _show_spy_list(ctx)
        return

    if action_lower in ["reset", "clear"]:
        await reset_spy_target(ctx)
        return

    if action_lower in ["add"]:
        if user is None:
            await ctx.send(f"⚠️ Veuillez mentionner un membre à ajouter ! Exemple : `{bot_tag} spy add @Membre`")
            return
        target_to_add = user
    elif action_lower in ["remove", "rm", "del", "delete"]:
        if user is None:
            await ctx.send(f"⚠️ Veuillez mentionner un membre à retirer ! Exemple : `{bot_tag} spy remove @Membre`")
            return
        if user.id not in TARGET_USER_IDS:
            await ctx.send(f"⚠️ {user.mention} n'était pas dans la liste des membres ciblés.")
            return
        TARGET_USER_IDS.remove(user.id)
        save_targets_to_env()
        await ctx.send(f"🗑️ {user.mention} a été retiré de la liste des joueurs ciblés !")
        return
    else:
        # Try to parse action_or_user directly as a User mention / ID
        target_user = None
        try:
            target_user = await commands.UserConverter().convert(ctx, action_or_user)
        except commands.BadArgument:
            pass

        if target_user:
            target_to_add = target_user
        else:
            await ctx.send(
                f"⚠️ Commande spy invalide.\n"
                f"💡 Utilisations possibles :\n"
                f"• `{bot_tag} spy @Membre` ou `{bot_tag} spy add @Membre`\n"
                f"• `{bot_tag} spy remove @Membre`\n"
                f"• `{bot_tag} spy list`\n"
                f"• `{bot_tag} spy reset`"
            )
            return

    if target_to_add.id in TARGET_USER_IDS:
        await ctx.send(f"ℹ️ {target_to_add.mention} est déjà dans la liste des joueurs ciblés !")
        return

    TARGET_USER_IDS.add(target_to_add.id)
    save_targets_to_env()
    await ctx.send(f"🎯 {target_to_add.mention} (ID: `{target_to_add.id}`) a été ajouté aux joueurs ciblés et sauvegardé !")


@bot.command(name="resetspy", aliases=["reset_spy", "unspy", "clearspy"])
async def reset_spy_target(ctx):
    """Clears all spy target users and removes them from .env."""
    global TARGET_USER_IDS
    if not TARGET_USER_IDS:
        await ctx.send("ℹ️ Aucun joueur n'est ciblé actuellement.")
        return

    TARGET_USER_IDS.clear()
    save_targets_to_env()
    await ctx.send("🔄 Tous les joueurs ciblés ont été réinitialisés et supprimés de la configuration !")


@bot.command(name="myanswer", aliases=["answer", "reponse", "myanswer:"])
async def check_answer(ctx, *, user_answer: str = ""):
    """Checks the user's submitted answer for the riddle."""
    bot_tag = f"@{bot.user.name}"
    if not TARGET_USER_IDS:
        await ctx.send(f"⚠️ Aucun joueur n'est ciblé pour le moment. Taggez-moi avec `{bot_tag} spy @Membre` !")
        return

    if ctx.author.id not in TARGET_USER_IDS:
        await ctx.send("⚠️ Seuls les joueurs ciblés peuvent soumettre une réponse !")
        return

    # Strip optional leading colon or space
    clean_answer = user_answer.lstrip(":").strip()
    if not clean_answer:
        await ctx.send(f"⚠️ Veuillez fournir une réponse ! Exemple : `{bot_tag} myanswer bottom`")
        return

    if ANSWER.lower() in clean_answer.lower():
        await ctx.send("bravo tu as trouvé")
    else:
        await ctx.send("cherche encore")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Handles invalid or unknown commands."""
    bot_tag = f"@{bot.user.name}"
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            f"❌ Désolé, je n'ai pas compris cette commande.\n"
            f"💡 Taggez-moi avec `{bot_tag} hello` pour voir le guide et les commandes !"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        if ctx.command and ctx.command.name in ["spy", "target"]:
            await ctx.send(f"⚠️ Veuillez mentionner un membre à cibler ! Exemple : `{bot_tag} spy @Membre`")
        else:
            await ctx.send(f"⚠️ Argument manquant pour cette commande.")
    else:
        print(f"[!] Command error: {error}")


@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by bots (including this bot)
    if message.author.bot:
        return

    # Process Discord bot commands first
    await bot.process_commands(message)

    # Check if message is just a direct mention of the bot alone (e.g. @RiddleBot)
    if bot.user in message.mentions and len(message.content.strip().split()) <= 1:
        await message.channel.send(
            f"👋 Bonjour ! Taggez-moi avec `@{bot.user.name} hello` pour afficher le guide complet du bot !"
        )
        return


if __name__ == "__main__":
    if not TOKEN or TOKEN == "YOUR_DISCORD_TOKEN_HERE":
        print("[-] ERROR: DISCORD_TOKEN is not configured in .env file.")
        print("[!] Please copy .env.example to .env and insert your Discord Bot Token.")
    else:
        bot.run(TOKEN)
