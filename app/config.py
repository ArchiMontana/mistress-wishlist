import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

# URL твоего Mini App (после деплоя на Render)
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
if not WEBAPP_URL:
    # локально можно так, но на Render обязательно поменяешь
    WEBAPP_URL = "http://127.0.0.1:8000"

# Мод-чат(ы) — туда уходят чеки. Через запятую.
# пример: MOD_CHAT_ID=-1001234567890,-1009876543210
_raw_mod_ids = os.getenv("MOD_CHAT_ID", "").strip()
MOD_CHAT_IDS = []
if _raw_mod_ids:
    for part in _raw_mod_ids.split(","):
        part = part.strip()
        if part:
            try:
                MOD_CHAT_IDS.append(int(part))
            except ValueError:
                pass

# Админы (не обязательно, но удобно)
_raw_admins = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = []
if _raw_admins:
    for part in _raw_admins.split(","):
        part = part.strip()
        if part:
            try:
                ADMIN_IDS.append(int(part))
            except ValueError:
                pass

# --- Тексты ---
TEXT_18_TITLE = "Доступ строго 18+"
TEXT_18_BODY = (
    "Этот проект предназначен только для совершеннолетних.\n\n"
    "Подтвердите, что вам есть 18 лет."
)

BTN_CONFIRM_18 = "Мне есть 18+ ✅"
BTN_OPEN_WISHLIST = "🔥 Открыть витрину подарков"
