# 🧩 RiddleBot — Interactive Discord Riddle & Game Bot

[![CI](https://github.com/MatthieuHanania/discord-riddle-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthieuHanania/discord-riddle-bot/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-v2.x-5865F2.svg?style=flat&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9.svg?style=flat&logo=rust&logoColor=white)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, scalable Discord bot built with **Python 3.10+**, **`discord.py` 2.x**, and managed with **`uv`** (with standard `requirements.txt` support for cloud hosts like **Wispbyte**).  
Features **pure Slash Commands (`/`)**, **Interactive Buttons & Modal pop-ups** (anti-cheat answer submissions and spoiler-free hints), **live message & button updates**, **guild-isolated state persistence**, and a **modular Cogs architecture**.

---

## ✨ Features

- 🧩 **Interactive Riddles (`/riddle`):**
  - Sends a styled card with the active riddle and targeted players (or a clean empty-state prompt if no riddle is configured yet).
  - **"🔑 Proposer une réponse" Button:** Opens a private Discord Modal window to submit guesses discreetly.
  - **"📖 Définition", "🔍 Indicateurs", "🧩 Fodder" Buttons:** Players can reveal breakdown clues privately via ephemeral messages without spoiling the puzzle for others. Buttons automatically enable or disable depending on which clues are configured!
  - **Dynamic Real-Time Clue Updates (`/riddle_edit`):** Opens a pre-filled Discord Modal popup displaying all current riddle fields (`Énoncé`, `Réponse`, `Définition`, `Indicateurs`, `Fodder`). Edit any field directly and the active riddle card and its buttons update live in the Discord channel!
  - **Interactive Configuration (`/riddle_set`):** Opens a clean Discord Modal form to configure a new riddle and its clues without typing long command arguments.
  - **Anti-Cheat / Anti-Spoiler:** Guesses submitted through the modal, `/answer`, and clue buttons are handled privately with ephemeral responses so no one can copy or leak answers.
- 🎯 **Target Player Management (`/spy`):**
  - Add, remove, list, or clear targeted players per server (`/spy add`, `/spy remove`, `/spy list`, `/spy clear`).
  - Automatically removes a player from the remaining target list as soon as they find the right answer and announces their progress in the channel.
  - **Guild-Isolated Persistence:** Each Discord server has its own state stored asynchronously in `data/guilds/<guild_id>.json`.
- 🔥 **Fun & Roasts (`/roast`):**
  - Roasts a friend with a randomized punchline loaded from `data/roasts.json`.
- 🏗️ **Clean Architecture & Automated Tests:**
  - Subclassed `commands.Bot` (`RiddleBot`) with asynchronous `setup_hook` and persistent `discord.ui.View` registration across restarts.
  - Feature modularity using **Cogs** (`cogs/riddle.py`, `cogs/spy.py`, `cogs/roast.py`, `cogs/general.py`).
  - Dedicated non-blocking **Services** (`StorageService`, `RoastService`).
  - Unit test suite (`tests/`) and GitHub Actions CI pipeline.

---

## 📁 Project Structure

```text
BotDiscord/
├── .github/workflows/ci.yml    # GitHub Actions CI (syntax check & unit tests)
├── pyproject.toml              # UV project metadata & dependencies
├── uv.lock                     # Deterministic UV lockfile
├── requirements.txt            # Pip dependencies (used for Wispbyte deployment)
├── .env.example                # Environment variables template
├── .env                        # Local secrets (DISCORD_TOKEN) - ignored by git
├── .gitignore
├── README.md
│
├── src/
│   ├── config.py               # Typed configuration & .env loader
│   ├── bot.py                  # Custom RiddleBot subclass (setup_hook, persistent views & tree sync)
│   │
│   ├── services/               # Asynchronous service layer
│   │   ├── storage.py          # Guild-isolated async JSON storage (riddles, clues, targets)
│   │   └── roast_service.py    # Punchlines & roasts manager
│   │
│   ├── ui/                     # Discord UI components
│   │   └── riddle_views.py     # Persistent RiddleView buttons (clues & rules) & RiddleAnswerModal
│   │
│   └── cogs/                   # Modular feature extensions
│       ├── general.py          # /help, /ping, and @Bot mentionsync
│       ├── riddle.py           # /riddle, /answer, /riddle_set, /riddle_edit
│       ├── spy.py              # /spy (add, remove, list, clear)
│       └── roast.py            # /roast
│
├── data/                       # Runtime data
│   ├── guilds/                 # Per-guild JSON state storage (auto-created, git-ignored)
│   └── roasts.json             # Curated French punchlines list
│
├── tests/                      # Automated unit tests
│   ├── test_riddle.py          # Riddle storage, clue editing & dynamic UI button tests
│   └── test_storage.py         # Empty-state & answer checking tests
│
└── main.py                     # Main application entry point
```

---

## ⚙️ Discord Developer Portal Configuration

1. Visit the [Discord Developer Portal](https://discord.com/developers/applications) and create/select your Application.
2. Go to the **Bot** tab:
   - Click **Reset Token** to retrieve your `DISCORD_TOKEN`.
   - Under **Privileged Gateway Intents**, enable **Message Content Intent** and save changes.
3. Go to **OAuth2 > URL Generator**:
   - **Scopes:** `bot`, `applications.commands`
   - **Bot Permissions:** `Send Messages`, `Read Message History`, `View Channels`, `Embed Links`, `Use Slash Commands`, `Manage Messages` (required for admins using `/riddle_set` and `/riddle_edit`).
4. Copy the generated URL and invite the bot to your Discord server.

---

## 🛠️ Local Installation & Setup

### 1. Install Dependencies
Using [uv](https://docs.astral.sh/uv/) (recommended):
```bash
uv sync
```
Or using standard `pip`:
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials (`.env`)
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and set your Discord Bot Token:
```env
DISCORD_TOKEN=your_secret_discord_bot_token
```

### 3. Run the Bot Locally
```bash
uv run main.py
```

### 4. Run Unit Tests
```bash
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

---

## ☁️ Deploying on Wispbyte (24/7 Hosting)

The project includes a `requirements.txt` and `main.py` at the root so it can be deployed out-of-the-box on **[Wispbyte](https://wispbyte.com/)** (or any Pterodactyl-based Python host):

1. **Create a Server on Wispbyte:**
   - Select **Python** as the server environment.
2. **Deploy the Code:**
   - Either connect/pull your GitHub repository (`main` branch) via the **Git** tab, or upload the project files (`main.py`, `requirements.txt`, `src/`, `data/roasts.json`) in the **Files** tab.
3. **Configure the `.env` File:**
   - In the Wispbyte **Files** tab, create a new file named `.env` at the root directory containing:
     ```env
     DISCORD_TOKEN=your_secret_discord_bot_token
     ```
4. **Check Startup Settings (`Startup` Tab):**
   - **Main file / Bot file:** `main.py`
   - **Additional Python packages / Requirements file:** `requirements.txt` (Wispbyte automatically installs `discord.py` and `python-dotenv` from `requirements.txt` on startup).
5. **Start / Restart the Bot:**
   - Go to the **Console** tab and click **Start** (or **Restart** after pulling new updates).
   - You should see:
     ```text
     [INFO] riddlebot.bot: Slash commands synced globally: 8 commands
     [INFO] riddlebot.bot: Logged in as ...
     ```

> **💡 Tip — Updating or Resetting Server Data on Wispbyte:**  
> Server riddles and target lists are saved in `data/guilds/<guild_id>.json` so your active riddle survives bot restarts and Git updates. If you ever want to wipe a server's state from scratch on Wispbyte, delete the corresponding JSON file inside `data/guilds/` (keep `data/roasts.json`!) and click **Restart** in the Console.

---

## 🎮 Slash Commands Overview

| Command | Permission | Description |
| :--- | :--- | :--- |
| **`/riddle`** | Everyone | Displays the interactive riddle card with targeted mentions and clue/answer buttons. |
| **`/answer <réponse>`** | Everyone | Submits a riddle answer directly via Slash command (private/ephemeral). |
| **`/riddle_set`** | Manage Messages | Opens an interactive modal popup to configure a new riddle, its secret answer, and its breakdown clues. |
| **`/riddle_edit`** | Manage Messages | Opens a modal popup pre-filled with the current riddle and clues so you can easily modify any field and update the active card live. |
| **`/spy add <@Membre>`** | Everyone | Adds a user to the riddle target list for this server. |
| **`/spy remove <@Membre>`** | Everyone | Removes a user from the target list. |
| **`/spy list`** | Everyone | Lists all users currently targeted by the active riddle. |
| **`/spy clear`** | Everyone | Clears the entire target list for the current server. |
| **`/roast <@Membre>`** | Everyone | Sends a randomized humorous punchline to a friend. |
| **`/help`** | Everyone | Displays the complete interactive bot guide and command list. |
| **`/ping`** | Everyone | Displays bot latency and Discord API connectivity status. |
