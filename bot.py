"""Entry point redirect for backward compatibility.

For modern execution, run:
    uv run main.py
"""

from __future__ import annotations

import asyncio
from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[+] RiddleBot stopped.")
