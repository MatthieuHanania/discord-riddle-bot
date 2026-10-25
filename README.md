# 🧩 RiddleBot — Interactive Discord Riddle & Game Bot

[![CI](https://github.com/MatthieuHanania/discord-riddle-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthieuHanania/discord-riddle-bot/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-v2.x-5865F2.svg?style=flat&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Package Manager: uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9.svg?style=flat&logo=rust&logoColor=white)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, scalable Discord bot built with **Python 3.12+**, **`discord.py` 2.x**, and managed with **`uv`**.  
Features **Slash Commands (`/`)**, **Interactive Buttons & Modal pop-ups** (anti-cheat answer submissions), **guild-isolated state persistence**, and **modular Cogs architecture**.

---

## ✨ Features

- 🧩 **Interactive Riddles (`/riddle`):**
  - Sends a styled card with the active riddle and tags the targeted players.
  - **"🔑 Proposer une réponse" Button:** Opens a private Discord Modal window.
  - **Anti-Cheat / Anti-Spoiler:** Guesses submitted through the modal are validated privately with ephemeral responses so no one can copy or leak answers!
  - **Dynamic Configuration (`/riddle_set`):** Change the riddle text and secret answer directly via Slash command without touching JSON files or rebooting!
- 🎯 **Target Player Management (`/spy`):**
  - Add, remove, list, or clear targeted players per server (`/spy add`, `/spy remove`, `/spy list`, `/spy clear`).
  - Isolated per server: each Discord server has its own riddle and target list!
- 🔥 **Fun & Roasts (`/roast`):**
  - Roasts a friend with a curated collection of punchlines loaded asynchronously from `data/roasts.json`.
- ⚡ **Pure Discord Slash Commands (`/`):**
  - Native autocomplete and Discord slash command tree integration.
  - Ephemeral private validation so users cannot cheat or spoil riddles.
- 🏗️ **Clean Architecture (GitHub Best Practices):**
  - Subclassed `commands.Bot` with asynchronous `setup_hook`.
  - Feature modularity using **Cogs** (`cogs/riddle.py`, `cogs/spy.py`, `cogs/roast.py`, `cogs/general.py`).
  - Dedicated non-blocking **Services** (`StorageService`, `RoastService`).
  - Structured console logging with timestamps and log levels.

---

## 📁 Project Structure

```text
BotDiscord/
├── pyproject.toml              # UV dependencies & project metadata
├── uv.lock                     # Deterministic dependency lockfile
├── .env.example                # Environment variables template
├── .env                        # Local secrets (DISCORD_TOKEN) - ignored by git
├── .gitignore
├── README.md
│
├── src/
│   ├── config.py               # Typed configuration & env loader
│   ├── bot.py                  # Custom RiddleBot subclass (setup_hook & tree sync)
│   │
│   ├── services/               # Asynchronous service layer
│   │   ├── storage.py          # Guild-isolated async storage
│   │   └── roast_service.py    # Punchlines & roasts manager
│   │
│   ├── ui/                     # Discord UI components
│   │   └── riddle_views.py     # Persistent Buttons & Modal popups
│   │
│   └── cogs/                   # Modular feature extensions
│       ├── general.py          # /help, /ping
│       ├── riddle.py           # /riddle, /answer, /riddle_set
│       ├── spy.py              # /spy (add, remove, list, clear)
│       └── roast.py            # /roast
│
├── data/                       # Persistent runtime data
│   ├── guilds/                 # Per-guild JSON state storage
│   └── roasts.json             # Punchlines list
│
└── main.py                     # Main application entry point
```

---

## 🛠️ Installation & Setup

### 1. Install Dependencies
Make sure you have [uv](https://docs.astral.sh/uv/) installed, then run:
```bash
uv sync
```

### 2. Configure Credentials (`.env`)
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and fill in your Discord Bot Token:
```env
DISCORD_TOKEN=your_secret_discord_bot_token

# (Optional) Set your server ID for instant slash command sync during development:
# DEV_GUILD_ID=123456789012345678
```

---

## ⚙️ Discord Developer Portal Configuration

1. Visit the [Discord Developer Portal](https://discord.com/developers/applications).
2. Select your Application, then go to the **Bot** tab.
3. Retrieve your token via **Reset Token** (paste it into `.env`).
4. In **OAuth2 > URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Read Message History`, `View Channels`, `Embed Links`, `Manage Messages` (optional, for riddle_set).
5. Invite the bot to your server using the generated URL.

---

## 🚀 Running the Bot

Run the bot with `uv`:
```bash
uv run main.py
```

---

## 🎮 Slash Commands Overview

| Command | Description |
| :--- | :--- |
| **`/riddle`** | Displays the interactive riddle card with targeted mentions and answer button. |
| **`/answer <réponse>`** | Submits a riddle answer directly via Slash command (private/ephemeral). |
| **`/riddle_set <texte> <réponse>`** | *(Admin)* Configures a new riddle and secret answer. |
| **`/spy add @Membre`** | Adds a user to the riddle target list. |
| **`/spy remove @Membre`** | Removes a user from the target list. |
| **`/spy list`** | Lists all currently targeted users. |
| **`/spy clear`** | Clears the target list for the current server. |
| **`/roast @Membre`** | Sends a randomized humorous punchline to a friend. |
| **`/help`** | Displays the interactive bot guide and command help. |
| **`/ping`** | Displays bot latency and API connectivity. |
