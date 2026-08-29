import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from local .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "/riddlebot")

# Configure Discord gateway intents (Message Content Intent required)
intents = discord.Intents.default()
intents.message_content = True

# Primary trigger mechanism: Mentioning @RiddleBot directly in Discord (with fallbacks)
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(
        f"{COMMAND_PREFIX.strip()} ",
        f"{COMMAND_PREFIX.strip()}",
        f"{COMMAND_PREFIX.strip().lstrip('/')} ",
        f"{COMMAND_PREFIX.strip().lstrip('/')}",
        "!"
    ),
    intents=intents
)

# Remove default help command to allow custom help alias
bot.remove_command("help")

# Target user ID (set dynamically in Discord via @RiddleBot spy @User)
TARGET_USER_ID = None

RIDDLE_TEXT = os.getenv("RIDDLE_TEXT", "Le détective anglais est a moitié enfermé")
ANSWER = os.getenv("RIDDLE_ANSWER", "lock")


@bot.event
async def on_ready():
    print(f"[+] Bot successfully connected as {bot.user} (ID: {bot.user.id})")
    print(f"[+] Trigger mode: Mention '@{bot.user.name}' directly in Discord")
    print(f"[+] Target User ID: {TARGET_USER_ID if TARGET_USER_ID else 'NOT SET (Use @Bot spy @User)'}")
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
        name="🎯 1. Cibler un Joueur (Spy)",
        value=f"• `@{bot_name} spy @Membre` : Définit la personne ciblée par l'énigme.",
        inline=False
    )
    
    embed.add_field(
        name="🧩 2. Poser l'Énigme",
        value=f"• `@{bot_name} riddle` (ou `enigme`) : Affiche l'énigme et mentionne le joueur ciblé.",
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
    """Displays the riddle and mentions the targeted user if configured."""
    bot_tag = f"@{bot.user.name}"
    if TARGET_USER_ID:
        await ctx.send(
            f"✨ <@{TARGET_USER_ID}> trouve la solution à l'énigme suivante :\n"
            f"> 🧩 **\"{RIDDLE_TEXT}\"**\n\n"
            f"💡 *Pour répondre, taggue-moi et écris :* `{bot_tag} myanswer <ta_réponse>` *(ex: `{bot_tag} myanswer bottom`)*"
        )
    else:
        await ctx.send(
            f"🧩 **Énigme :**\n"
            f"> **\"{RIDDLE_TEXT}\"**\n\n"
            f"⚠️ *(Aucun joueur n'est ciblé. Taggez-moi avec `{bot_tag} spy @Membre` pour en choisir un !)*"
        )


@bot.command(name="spy", aliases=["target"])
async def set_spy_target(ctx, user: discord.User):
    """Sets the target user to monitor using @mention or User ID."""
    global TARGET_USER_ID
    TARGET_USER_ID = user.id
    await ctx.send(f"🎯 Le joueur ciblé est désormais {user.mention} (ID: `{user.id}`) !")


@bot.command(name="myanswer", aliases=["answer", "reponse", "myanswer:"])
async def check_answer(ctx, *, user_answer: str = ""):
    """Checks the user's submitted answer for the riddle."""
    bot_tag = f"@{bot.user.name}"
    if not TARGET_USER_ID:
        await ctx.send(f"⚠️ Aucun joueur n'est ciblé pour le moment. Taggez-moi avec `{bot_tag} spy @Membre` !")
        return

    if ctx.author.id != TARGET_USER_ID:
        await ctx.send("⚠️ Seul le joueur ciblé peut soumettre une réponse !")
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
        print("[-] ERROR: DISCORD_TOKEN is not configured.")
        print("[!] Please run the setup script first: python setup.py")
    else:
        bot.run(TOKEN)
