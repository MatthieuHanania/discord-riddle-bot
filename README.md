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

Open the newly created `.env` file in a text editor and add your Discord Bot Token:
```env
DISCORD_TOKEN=votre_token_secret_discord
RIDDLE_TEXT=Le détective anglais est a moitié enfermé
RIDDLE_ANSWER=lock
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

Commands to publish your repository:
```bash
git init
git add .
git commit -m "Initial commit - Clean Discord Bot"
git branch -M main
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```
