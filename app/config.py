import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

# Адрес витрины (Render)
BASE_URL = os.getenv(
    "BASE_URL",
    "https://mistress-wishlist.onrender.com"  # дефолт на всякий
).strip()

# Мод-чат: туда летят чеки
_raw_mod = os.getenv("MOD_CHAT_ID", "").strip()
MOD_CHAT_ID = int(_raw_mod) if _raw_mod else None

# Канал (если понадобится позже)
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
CHANNEL_ID = int(CHANNEL_ID) if CHANNEL_ID else None

# Пример "сложного" пароля для админ-API (опционально)
ADMIN_API_PASSWORD = os.getenv("ADMIN_API_PASSWORD", "").strip() or None
