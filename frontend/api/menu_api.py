import requests
from config import API_BASE


def get_menu_items(token: str) -> tuple[list, int]:
    """
    GET /api/v1/menu/items
    Returns all available menu items.

    Each item contains:
      id, name, description, cuisine, category, price,
      calories, protein_g, carbs_g, fat_g,
      spice_level, is_veg, ingredients, tags, is_available
    """
    try:
        resp = requests.get(
            f"{API_BASE}/v1/menu/items",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        data = resp.json()
        return (data if isinstance(data, list) else []), resp.status_code
    except requests.exceptions.ConnectionError:
        return [], 503


def create_order(token: str, item_ids: list[int]) -> tuple[dict, int]:
    """
    POST /api/v1/orders/
    Places an order for one or more menu items in a single request.

    Request body: { "item_ids": [8, 9, 19] }
    Response:     { "orders": [...], "total": 3 }
    """
    try:
        resp = requests.post(
            f"{API_BASE}/v1/orders/",
            json={"item_ids": item_ids},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend."}, 503
