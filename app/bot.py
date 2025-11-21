import logging
from typing import Dict

from fastapi import APIRouter, Request
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from .config import (
    BOT_TOKEN, WEBAPP_URL,
    MOD_CHAT_IDS, ADMIN_IDS,
    TEXT_18_TITLE, TEXT_18_BODY,
    BTN_CONFIRM_18, BTN_OPEN_WISHLIST,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------
# Память 18+ (в RAM).
# На проде можно заменить на БД/файл.
# ---------------------------
adult_ok: Dict[int, bool] = {}


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("wishlist", wishlist_cmd))
    app.add_handler(CallbackQueryHandler(confirm_18_cb, pattern="^confirm_18$"))

    return app


application = build_application()

# ---------------------------
# FastAPI router для webhook
# ---------------------------
router = APIRouter()


@router.post("/bot")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


# ---------------------------
# Команды / коллбэки бота
# ---------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показываем 18+ подтверждение."""
    user_id = update.effective_user.id

    # Если уже подтвердил 18+ — сразу даём кнопку витрины
    if adult_ok.get(user_id):
        await send_wishlist_button(update, context)
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(BTN_CONFIRM_18, callback_data="confirm_18")]
    ])

    # Попытка отправить лого (если доступно по URL)
    logo_url = f"{WEBAPP_URL}/static/img/af_logo.png"
    try:
        await update.message.reply_photo(
            photo=logo_url,
            caption=f"**{TEXT_18_TITLE}**\n\n{TEXT_18_BODY}",
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception:
        await update.message.reply_text(
            f"**{TEXT_18_TITLE}**\n\n{TEXT_18_BODY}",
            parse_mode="Markdown",
            reply_markup=kb,
        )


async def confirm_18_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь подтвердил 18+."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    adult_ok[user_id] = True

    await query.edit_message_caption(
        caption="✅ Доступ подтверждён.\n\nНажми кнопку ниже и открой витрину.",
    )

    await send_wishlist_button(update, context)


async def wishlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдать витрину по команде."""
    user_id = update.effective_user.id
    if not adult_ok.get(user_id):
        await start_cmd(update, context)
        return

    await send_wishlist_button(update, context)


async def send_wishlist_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Большая кнопка витрины (Mini App)."""
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_OPEN_WISHLIST, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Нажми кнопку ниже",
    )

    # reply_text работает и после callback, и после /start
    target = update.effective_message
    await target.reply_text(
        "🔥 Витрина открывается через кнопку ниже:",
        reply_markup=kb
    )


# ---------------------------
# Старт/стоп для FastAPI lifespan
# ---------------------------
async def start_bot():
    await application.initialize()
    await application.start()
    logger.info("Telegram bot started (webhook mode)")


async def stop_bot():
    await application.stop()
    await application.shutdown()
    logger.info("Telegram bot stopped")
