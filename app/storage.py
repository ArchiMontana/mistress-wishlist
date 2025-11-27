import json
from pathlib import Path
from typing import Dict, Any

STATE_FILE = Path("data") / "state.json"

DEFAULT_STATE: Dict[str, Any] = {
    "items": {}  # "1": {"status": "available"|"pending"|"gifted"}
}


def load_state() -> Dict[str, Any]:
    """
    Чтение state.json. Если файла нет или он битый — возвращаем дефолт.
    """
    if not STATE_FILE.exists():
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE.copy()

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "items" not in data or not isinstance(data["items"], dict):
            data["items"] = {}
        return data
    except Exception:
        # Если что-то пошло не так — не ломаемся, просто возвращаем дефолт
        return DEFAULT_STATE.copy()


def save_state(state: Dict[str, Any]) -> None:
    """
    Записываем state.json.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_item_status(item_id: int) -> str:
    """
    Возвращает статус товара: available / pending / gifted.
    По умолчанию — available.
    """
    state = load_state()
    return state.get("items", {}).get(str(item_id), {}).get("status", "available")


def set_item_status(item_id: int, status: str) -> None:
    """
    Устанавливает статус товара и сохраняет state.json.
    """
    state = load_state()
    items = state.setdefault("items", {})
    items[str(item_id)] = {"status": status}
    save_state(state)
