import requests
from config import API_BASE


def semantic_search(
    token: str,
    query: str,
    limit: int = 8,
    is_veg: bool | None = None,
    cuisine: str | None = None,
    max_calories: int | None = None,
    min_protein: float | None = None,
) -> tuple[list, int]:
    """
    POST /api/v1/menu/search

    Sends the query text to the backend, which:
      1. Embeds it with OpenAI text-embedding-3-small
      2. Runs vector similarity search in Qdrant
      3. Applies any pre-filters (is_veg, cuisine, calories, protein)
      4. Returns results sorted by cosine similarity score (highest first
    """
    body: dict = {"query": query, "limit": limit}

    if is_veg is not None:
        body["is_veg"] = is_veg
    if cuisine:
        body["cuisine"] = cuisine
    if max_calories is not None:
        body["max_calories"] = max_calories
    if min_protein is not None:
        body["min_protein"] = min_protein

    try:
        resp = requests.post(
            f"{API_BASE}/v1/menu/search",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,   # embedding + vector search can take a moment
        )
        data = resp.json()
        return (data if isinstance(data, list) else []), resp.status_code
    except requests.exceptions.ConnectionError:
        return [], 503
    except requests.exceptions.Timeout:
        return [], 504
