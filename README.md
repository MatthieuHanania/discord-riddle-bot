# Discord Bot - Riddle & Target User Detector

A Python Discord Bot (`discord.py`) featuring direct tag/mention commands (`@RiddleBot`), target user monitoring, and interactive riddle answering.

Designed to be **safely shared or pushed to GitHub** without exposing sensitive credentials or tokens.

---

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env` File)
Copy `.env.example` to `.env`:

**Windows (Command Prompt / PowerShell):**
```cmd
copy .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

Open the newly created `.env` file in a text editor and paste your Discord Bot Token:
```env
DISCORD_TOKEN=your_secret_discord_token
RIDDLE_TEXT=Bible's central motto: turning the other cheek(s)? (6)
RIDDLE_ANSWER=bottom
```

---

## ⚙️ Discord Developer Portal Configuration

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create an Application, then go to the **Bot** menu.
3. Retrieve your token via **Reset Token** (to paste into your `.env` file).
4. ⚠️ **IMPORTANT**: Under **Privileged Gateway Intents**, **ENABLE** `MESSAGE CONTENT INTENT`.
5. Under **OAuth2 > URL Generator**, select the `bot` scope and permissions `Send Messages`, `Read Message History`, `View Channels`, then use the generated URL to invite the bot to your server.

---

## 🚀 Running the Bot

Run the bot script:
```bash
python bot.py
```

---

## 🎮 Commands & Features (Always Active)

The bot is **always active** and triggered directly by tagging `@RiddleBot` in Discord:

- **`@RiddleBot hello`**: Displays presentation guide embed card.
- **`@RiddleBot spy @User`**: Sets the target user for the riddle.
- **`@RiddleBot riddle`** (or **`@RiddleBot enigme`**): Displays the riddle and pings the target user.
- **`@RiddleBot myanswer <réponse>`** (or **`@RiddleBot myanswer: <réponse>`**): Submits an answer for the riddle.

---

## 📤 Pushing to GitHub Safely

Your `.env` file is excluded in `.gitignore` and will **never** be pushed to GitHub.
