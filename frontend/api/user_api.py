import requests
from config import API_BASE


def get_profile(token: str) -> tuple[dict, int]:
    """
    GET /api/v1/users/me
    Returns: { id, phone, name, email, is_active, created_at }
    """
    try:
        resp = requests.get(
            f"{API_BASE}/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend."}, 503


def get_preferences(token: str) -> tuple[dict | None, int]:
    """
    GET /api/v1/users/me/preferences
    Returns: { diet_type, spice_level, favorite_cuisines, allergies, health_goals }
    or null if the user has not saved preferences yet.
    """
    try:
        resp = requests.get(
            f"{API_BASE}/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend."}, 503


def save_preferences(token: str, payload: dict) -> tuple[dict, int]:
    """
    PUT /api/v1/users/me/preferences
    payload: { diet_type, spice_level, favorite_cuisines, allergies, health_goals }
    Returns the saved preferences dict.
    """
    try:
        resp = requests.put(
            f"{API_BASE}/v1/users/me/preferences",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend."}, 503


def get_order_history(token: str) -> tuple[list, int]:
    """
    GET /api/v1/orders/my
    Returns last 10 orders: [{ id, item_id, item_name, ordered_at }]
    """
    try:
        resp = requests.get(
            f"{API_BASE}/v1/orders/my",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        data = resp.json()
        return (data if isinstance(data, list) else []), resp.status_code
    except requests.exceptions.ConnectionError:
        return [], 503
