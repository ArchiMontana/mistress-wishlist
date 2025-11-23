import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").strip()

_raw_mod = os.getenv("MOD_CHAT_ID", "").strip()
MOD_CHAT_ID = int(_raw_mod) if _raw_mod else None

CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
CHANNEL_ID = int(CHANNEL_ID) if CHANNEL_ID else None
