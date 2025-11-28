from pathlib import Path
import time
import json

import requests
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import BOT_TOKEN, MOD_CHAT_ID, ADMIN_API_PASSWORD
from .storage import get_item_status, set_item_status

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# === 14 карточек магазина ===
ITEMS = [
    {
        "id": 1,
        "title": "Перчатки атласные Lippa, красные",
        "price": "524",
        "image": "/static/items/item_1.jpg",
    },
    {
        "id": 2,
        "title": "Туфли стрипы тройки силиконовые",
        "price": "19 440",
        "image": "/static/items/item_2.jpg",
    },
    {
        "id": 3,
        "title": "Туфли на высоком каблуке, красные",
        "price": "3 406",
        "image": "/static/items/item_3.jpg",
    },
    {
        "id": 4,
        "title": "Корсет вечерний утягивающий кружевной, ByAsso",
        "price": "5 002",
        "image": "/static/items/item_4.jpg",
    },
    {
        "id": 5,
        "title": "Афро член киберкожа люкс, реалистичный, тёмный",
        "price": "1 428",
        "image": "/static/items/item_5.jpg",
    },
    {
        "id": 6,
        "title": "Набор низкотемпературных свечей для WAXPLAY",
        "price": "600",
        "image": "/static/items/item_6.jpg",
    },
    {
        "id": 7,
        "title": "Ботфорты зима высокие на платформе, CYJP",
        "price": "4 340",
        "image": "/static/items/item_7.jpg",
    },
    {
        "id": 8,
        "title": "Конфеты ручной работы",
        "price": "698",
        "image": "/static/items/item_8.jpg",
    },
    {
        "id": 9,
        "title": "Лосины прозрачные из сетки для танцев и фитнеса, чёрные",
        "price": "2 766",
        "image": "/static/items/item_9.jpg",
    },
    {
        "id": 10,
        "title": "Букет алых роз",
        "price": "8 000",
        "image": "/static/items/item_10.jpg",
    },
    {
        "id": 11,
        "title": "Трусики эротик женские, чёрные",
        "price": "562",
        "image": "/static/items/item_11.jpg",
    },
    {
        "id": 12,
        "title": "Атласный комплект постельного белья, красный (1.5 сп)",
        "price": "3 497",
        "image": "/static/items/item_12.jpg",
    },
    {
        "id": 13,
        "title": "Жидкий вибратор, LOVESHOT, soft, 10 мл, HYDROP",
        "price": "3 379",
        "image": "/static/items/item_13.jpg",
    },
    {
        "id": 14,
        "title": "Martini Prosecco DOC Treviso Brut, 0.75 л",
        "price": "2300",
        "image": "/static/items/item_14.jpg",
    },
]


def get_item_by_id(item_id: int):
    for i in ITEMS:
        if i["id"] == item_id:
            return i
    return None


# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # читаем tg_id / tg_username из query-параметров
    tg_id = request.query_params.get("tg_id")
    tg_username = request.query_params.get("tg_username")

    # Подмешиваем статус к каждому товару
    items_with_status = []
    for item in ITEMS:
        status = get_item_status(item["id"])
        items_with_status.append({**item, "status": status})

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items_with_status,
            "tg_id": tg_id,
            "tg_username": tg_username,
        },
    )


# Страница товара
@app.get("/item/{item_id}", response_class=HTMLResponse)
async def item_page(item_id: int, request: Request):
    item = get_item_by_id(item_id)
    if not item:
        return HTMLResponse("Товар не найден", status_code=404)

    status = get_item_status(item_id)

    # Протаскиваем tg_id / username дальше (из query в шаблон)
    tg_id = request.query_params.get("tg_id")
    tg_username = request.query_params.get("tg_username")

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item": item,
            "status": status,
            "tg_id": tg_id,
            "tg_username": tg_username,
        },
    )


# Обработка загрузки чека
@app.post("/upload_receipt")
async def upload_receipt(
    item_id: str = Form(...),
    file: UploadFile = File(...),
    tg_id: str | None = Form(None),
    tg_username: str | None = Form(None),
):
    item_id_int = int(item_id)
    item = get_item_by_id(item_id_int)
    if not item:
        return HTMLResponse("Товар не найден", status_code=404)

    # Проверяем текущий статус
    current_status = get_item_status(item_id_int)
    if current_status in ("pending", "gifted"):
        # просто возвращаемся к карточке с тем же статусом
        return RedirectResponse(
            url=f"/item/{item_id_int}",
            status_code=303,
        )

    # Сохраняем чек на диск
    receipts_dir = Path("data") / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    safe_name = file.filename.replace(" ", "_")
    filename = f"item_{item_id_int}_{ts}_{safe_name}"
    filepath = receipts_dir / filename

    content = await file.read()
    with filepath.open("wb") as f:
        f.write(content)

    # Ставим статус "в обработке"
    set_item_status(item_id_int, "pending")

    # Подпись, включая отправителя, если есть
    user_part = ""
    if tg_username:
        user_part = f"\nОт: @{tg_username}"
    elif tg_id:
        user_part = f"\nОт пользователя ID: {tg_id}"

    # Шлём в мод-чат документ с кнопками
    if BOT_TOKEN and MOD_CHAT_ID:
        try:
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

            caption = (
                f"Новый чек по подарку #{item_id_int}\n"
                f"{item['title']}\n\n"
                f"Статус: на проверке ✅"
                f"{user_part}"
            )

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "✅ Подтвердить оплату",
                            "callback_data": f"mod:confirm:{item_id_int}",
                        },
                        {
                            "text": "❌ Отклонить",
                            "callback_data": f"mod:reject:{item_id_int}",
                        },
                    ]
                ]
            }

            with filepath.open("rb") as f:
                files = {
                    "document": (filename, f, "application/pdf"),
                }
                data = {
                    "chat_id": str(MOD_CHAT_ID),
                    "caption": caption,
                    "reply_markup": json.dumps(keyboard, ensure_ascii=False),
                }
                requests.post(telegram_api_url, data=data, files=files, timeout=20)
        except Exception as e:
            print(f"Ошибка отправки чека в мод-чат: {e}")

    # Возвращаем пользователя обратно на страницу товара
    # (чтобы он увидел статус "идёт проверка оплаты")
    return RedirectResponse(
        url=f"/item/{item_id_int}",
        status_code=303,
    )


# --- Админ-API для обновления статуса (бот дёргает этот эндпоинт) ---


@app.post("/admin/update_status")
async def admin_update_status(
    item_id: int = Form(...),
    new_status: str = Form(...),
    admin_password: str = Form(...),
):
    """
    Эндпоинт дергается ботом при нажатии кнопок:
    - confirm -> gifted
    - reject  -> available
    """
    if not ADMIN_API_PASSWORD or admin_password != ADMIN_API_PASSWORD:
        return HTMLResponse("Forbidden", status_code=403)

    if new_status not in ("available", "pending", "gifted"):
        return HTMLResponse("Bad status", status_code=400)

    set_item_status(item_id, new_status)
    return {"status": "ok", "item_id": item_id, "new_status": new_status}
