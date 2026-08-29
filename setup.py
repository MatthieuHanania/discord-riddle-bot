import os

def run_setup():
    print("==================================================")
    print(" 🛠️  Discord Bot Initial Setup")
    print("==================================================")
    print("This script will generate the local '.env' file containing")
    print("your sensitive credentials. This file should NEVER")
    print("be shared or pushed to GitHub.\n")

    env_path = ".env"
    if os.path.exists(env_path):
        response = input("⚠️ A '.env' file already exists. Overwrite it? (y/N): ").strip().lower()
        if response not in ["y", "yes", "o", "oui"]:
            print("❌ Setup cancelled.")
            return

    # Prompt for Token (Required)
    token = ""
    while not token:
        token = input("🔑 Enter your Discord Bot Token (from Developer Portal): ").strip()
        if not token:
            print("⚠️ Discord Bot Token is required!")

    # Prompt for Command Prefix
    default_prefix = "/riddlebot"
    prefix_input = input(f"⚡ Command Prefix [{default_prefix}]: ").strip()
    prefix = prefix_input if prefix_input else default_prefix

    # Prompt for Riddle Text
    default_riddle = "Le détective anglais est a moitié enfermé"
    riddle_input = input(f"🧩 Riddle Text [{default_riddle}]: ").strip()
    riddle = riddle_input if riddle_input else default_riddle

    # Prompt for Riddle Answer
    default_answer = "lock"
    answer_input = input(f"🔑 Riddle Answer [{default_answer}]: ").strip()
    answer = answer_input if answer_input else default_answer

    # Write to .env file
    env_content = f"""# Discord Bot Configuration (DO NOT PUSH TO GITHUB)
DISCORD_TOKEN={token}
COMMAND_PREFIX={prefix}
RIDDLE_TEXT={riddle}
RIDDLE_ANSWER={answer}
"""

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n✅ The '.env' file was created successfully!")
    print("🔒 This file is automatically ignored by Git (via .gitignore).")
    print("🚀 You can now start the bot using: python bot.py\n")

if __name__ == "__main__":
    run_setup()
