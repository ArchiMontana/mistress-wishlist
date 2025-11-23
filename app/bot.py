from pathlib import Path
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN, BASE_URL

LOGO_PATH = Path("app/static/img/af_logo.png")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Лого
    if LOGO_PATH.exists():
        try:
            with open(LOGO_PATH, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption="Подарки для Госпожи"
                )
        except Exception:
            pass

    # 18+
    kb_18 = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Мне есть 18+ ✅", callback_data="age:yes")],
            [InlineKeyboardButton("Мне нет 18 ❌", callback_data="age:no")],
        ]
    )
    await update.message.reply_text(
        "Этот бот содержит материалы 18+. Подтверди возраст.",
        reply_markup=kb_18,
    )


async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "age:no":
        await q.edit_message_text("Доступ запрещён. Вернись, когда будет 18+.")
        return

    await q.edit_message_text("Доступ подтверждён ✅")

    # Большая кнопка Старт
    start_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🔥 Старт")]],
        resize_keyboard=True
    )
    await context.bot.send_message(
        chat_id=q.message.chat_id,
        text="Нажми «🔥 Старт», чтобы открыть витрину подарков.",
        reply_markup=start_kb
    )


async def start_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Открыть витрину 🎁", url=BASE_URL)]]
    )
    await update.message.reply_text(
        "Витрина готова. Открывай:",
        reply_markup=kb
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Сначала подтверди 18+, потом жми «🔥 Старт»."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(age_callback, pattern="^age:"))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^🔥 Старт$"), start_button_handler)
    )

    print("✅ Bot started (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
