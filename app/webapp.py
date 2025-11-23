from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
        "title": "Трусы эротические бразильяна, чёрные с молнией",
        "price": "840",
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
        "title": "Туфли на каблуке, вечерние лодочки, красные",
        "price": "2 708",
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
        "title": "Колье из жемчуга, бижутерия",
        "price": "5 384",
        "image": "/static/items/item_13.jpg",
    },
    {
        "id": 14,
        "title": "Боди красное глянцевое с доступом",
        "price": "1 845",
        "image": "/static/items/item_14.jpg",
    },
]


# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": ITEMS},
    )


# Страница товара
@app.get("/item/{item_id}", response_class=HTMLResponse)
async def item_page(item_id: int, request: Request):
    item = next(i for i in ITEMS if i["id"] == item_id)
    return templates.TemplateResponse(
        "item.html",
        {"request": request, "item": item},
    )


# Обработка загрузки чека
@app.post("/upload_receipt")
async def upload_receipt(
    item_id: str = Form(...),
    file: UploadFile = File(...),
):
    # Позже — отправка чека в мод-чат
    return {"status": "ok", "item_id": item_id, "filename": file.filename}
