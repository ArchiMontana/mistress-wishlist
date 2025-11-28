from pathlib import Path
import time
import json

import requests
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import BOT_TOKEN, MOD_CHAT_ID
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
        "title": "Свечи БДСМ низкотемпературные для Wax Play, розовые",
        "price": "1 059",
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
        "title": "Вибратор вакуумный с язычком, розовый",
        "price": "2 580",
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
        "title": "БДСМ эротическое платье с задним декольте, чёрное",
        "price": "1 449",
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
        "title": "Poppers Возбудитель усилитель оргазма BDSM red 10 мл",
        "price": "626",
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
    # Подмешиваем статус к каждому товару
    items_with_status = []
    for item in ITEMS:
        status = get_item_status(item["id"])
        items_with_status.append({**item, "status": status})

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": items_with_status},
    )


# Страница товара
@app.get("/item/{item_id}", response_class=HTMLResponse)
async def item_page(item_id: int, request: Request):
    item = get_item_by_id(item_id)
    if not item:
        return HTMLResponse("Товар не найден", status_code=404)

    status = get_item_status(item_id)

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item": item,
            "status": status,
        },
    )


# Обработка загрузки чека
@app.post("/upload_receipt")
async def upload_receipt(
    request: Request,
    item_id: str = Form(...),
    file: UploadFile = File(...),
):
    item_id_int = int(item_id)
    item = get_item_by_id(item_id_int)
    if not item:
        return HTMLResponse("Товар не найден", status_code=404)

    # Проверяем текущий статус
    current_status = get_item_status(item_id_int)
    if current_status in ("pending", "gifted"):
        # Просто возвращаем пользователя на страницу товара —
        # там он увидит актуальный статус.
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

    # Шлём в мод-чат документ с кнопками
    if BOT_TOKEN and MOD_CHAT_ID:
        try:
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

            caption = (
                f"Новый чек по подарку #{item_id_int}\n"
                f"{item['title']}\n\n"
                f"Статус: на проверке ✅"
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
            # В лог можно вывести ошибку, но пользователю не палимся
            print(f"Ошибка отправки чека в мод-чат: {e}")

    # После успешной загрузки чека — возвращаем пользователя
    # на страницу товара, где он уже увидит статус "идёт проверка".
    return RedirectResponse(
        url=f"/item/{item_id_int}",
        status_code=303,
    )
