from pathlib import Path
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN, BASE_URL, ADMIN_API_PASSWORD

# Базовая папка этого модуля (app/)
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "static" / "img" / "af_logo.png"


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — логотип + запрос 18+."""
    chat_id = update.effective_chat.id

    # 1) Логотип
    if LOGO_PATH.exists():
        try:
            with open(LOGO_PATH, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption="Подарки для Госпожи",
                )
        except Exception as e:
            print(f"Ошибка отправки логотипа: {e}")
    else:
        print(f"Логотип не найден по пути: {LOGO_PATH}")

    # 2) Кнопки 18+
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
    """Обработка нажатия на кнопки 18+."""
    q = update.callback_query
    await q.answer()

    if q.data == "age:no":
        await q.edit_message_text("Доступ запрещён. Вернись, когда будет 18+.")
        return

    await q.edit_message_text("Доступ подтверждён ✅")

    # Большая кнопка «🔥 Старт» внизу экрана
    start_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🔥 Старт")]],
        resize_keyboard=True,
    )

    await context.bot.send_message(
        chat_id=q.message.chat_id,
        text="Нажми «🔥 Старт», чтобы открыть витрину подарков.",
        reply_markup=start_kb,
    )


async def start_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка нажатия на «🔥 Старт».
    Даём кнопку, которая открывает WebApp внутри Telegram.
    """
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Открыть витрину 🎁",
                    web_app=WebAppInfo(url=BASE_URL),
                )
            ]
        ]
    )

    await update.message.reply_text(
        "Витрина готова. Открывай:",
        reply_markup=kb,
    )


async def mod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопок модерации чека:
    - mod:confirm:<item_id>
    - mod:reject:<item_id>
    """
    q = update.callback_query
    await q.answer()

    data = q.data or ""
    print(f"[MOD CALLBACK] data = {data}")  # чтобы видеть в консоли

    try:
        _, action, item_id_str = data.split(":")
        item_id = int(item_id_str)
    except Exception:
        await q.edit_message_caption(
            caption=(q.message.caption or "") + "\n\n⚠️ Некорректные данные callback."
        )
        return

    if action == "confirm":
        new_status = "gifted"
        suffix = "\n\n✅ Оплата подтверждена. Подарок отмечен как подаренный."
    elif action == "reject":
        new_status = "available"
        suffix = "\n\n❌ Оплата отклонена. Подарок снова доступен."
    else:
        new_status = None
        suffix = "\n\n⚠️ Неизвестное действие."

    if new_status and ADMIN_API_PASSWORD:
        try:
            api_url = BASE_URL.rstrip("/") + "/admin/update_status"
            payload = {
                "item_id": item_id,
                "status": new_status,
                "password": ADMIN_API_PASSWORD,
            }
            resp = requests.post(api_url, json=payload, timeout=10)
            print(f"[ADMIN API] {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Ошибка вызова admin/update_status: {e}")

    # Обновляем подпись к сообщению в мод-чате
    old_caption = q.message.caption or ""
    new_caption = old_caption + suffix

    try:
        await q.edit_message_caption(caption=new_caption)
    except Exception as e:
        print(f"Ошибка обновления подписи в мод-чате: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text(
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Сначала подтверди 18+, потом жми «🔥 Старт»."
    )


def main():
    """Точка входа для локального запуска бота."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    # 18+
    app.add_handler(CallbackQueryHandler(age_callback, pattern=r"^age:"))

    # Модерация чеков
    app.add_handler(CallbackQueryHandler(mod_callback, pattern=r"^mod:"))

    # Кнопка "🔥 Старт"
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^🔥 Старт$"),
            start_button_handler,
        )
    )

    print("✅ Bot started (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
