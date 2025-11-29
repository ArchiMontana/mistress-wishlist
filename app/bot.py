from pathlib import Path
from urllib.parse import urlencode

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

from .config import BOT_TOKEN, BASE_URL
from .storage import set_item_status

# Базовая папка этого модуля (app/)
BASE_DIR = Path(__file__).resolve().parent

# Логотип (может использоваться внутри витрины или как запасной вариант)
LOGO_PATH = BASE_DIR / "static" / "img" / "af_logo.png"
# Новая приветственная картинка для /start
WELCOME_PATH = BASE_DIR / "static" / "img" / "af_welcome.png"


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — приветственная картинка + запрос 18+."""
    chat_id = update.effective_chat.id

    print(f"[bot] /start from chat_id={chat_id}")

    # 1) Приветственная картинка
    image_path = None
    if WELCOME_PATH.exists():
        image_path = WELCOME_PATH
        print(f"[bot] Using WELCOME_PATH = {WELCOME_PATH}")
    elif LOGO_PATH.exists():
        image_path = LOGO_PATH
        print(f"[bot] Using LOGO_PATH = {LOGO_PATH}")
    else:
        print(f"[bot] ⚠️ Картинки не найдены: {WELCOME_PATH} / {LOGO_PATH}")

    if image_path:
        try:
            with open(image_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption="Подарки для Госпожи",
                )
        except Exception as e:
            print(f"[bot] Ошибка отправки приветственной картинки: {e}")

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
    """Обработка нажатия на «🔥 Старт».

    Даём кнопку, которая открывает WebApp внутри Telegram
    и пробрасываем tg_id/tg_username в витрину.
    """
    user = update.effective_user
    tg_id = user.id
    tg_username = user.username or ""

    print(f"[bot] 🔥 Старт от user_id={tg_id}, username={tg_username!r}")

    params = urlencode({"tg_id": tg_id, "tg_username": tg_username})
    webapp_url = f"{BASE_URL}?{params}"

    print(f"[bot] WebApp URL = {webapp_url}")

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Открыть витрину 🎁",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )

    await update.message.reply_text(
        "Витрина готова. Открывай:",
        reply_markup=kb,
    )


async def mod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок модерации чека:

    - mod:confirm:<item_id>
    - mod:reject:<item_id>

    Пишем статус товара напрямую в state.json через storage.set_item_status.
    """
    q = update.callback_query
    print(f"[MOD CALLBACK] data = {q.data}")
    await q.answer()

    try:
        _, action, item_id_str = q.data.split(":")
        item_id = int(item_id_str)
    except Exception as e:
        print(f"[MOD CALLBACK] parse error: {e}")
        await q.edit_message_caption(
            caption=(q.message.caption or "") + "\n\n⚠️ Некорректные данные callback."
        )
        return

    # Решаем, какой статус выставить
    if action == "confirm":
        set_item_status(item_id, "gifted")
        suffix = "\n\n✅ Оплата подтверждена. Подарок отмечен как подаренный."
    elif action == "reject":
        set_item_status(item_id, "available")
        suffix = "\n\n❌ Оплата отклонена. Подарок снова доступен."
    else:
        suffix = "\n\n⚠️ Неизвестное действие."

    # Обновляем подпись к сообщению в мод-чате
    old_caption = q.message.caption or ""
    new_caption = old_caption + suffix

    try:
        await q.edit_message_caption(caption=new_caption)
    except Exception as e:
        print(f"[MOD CALLBACK] Ошибка обновления подписи в мод-чате: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text(
        "/start — запуск\n"
        "/help — помощь\n\n"
        "Сначала подтверди 18+, потом жми «🔥 Старт»."
    )


def main():
    """Точка входа для запуска бота (локально и на Render)."""

    # Логи по токену, чтобы понимать, что именно прилетело из окружения
    print(f"[bot] Starting bot, BOT_TOKEN length = {len(BOT_TOKEN)}")
    print(f"[bot] BOT_TOKEN prefix = {repr(BOT_TOKEN[:10])}")

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
