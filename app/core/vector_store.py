from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


COLLECTIONS: dict[str, dict] = {
    "menu_items": {
        "size": 1536,
        "distance": Distance.COSINE,
    },
    "customer_preferences": {
        "size": 1536,
        "distance": Distance.COSINE,
    },
}

_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Return the module-level Qdrant client (must call init_qdrant first)."""
    if _client is None:
        raise RuntimeError("Qdrant client not initialised. Call init_qdrant() at startup.")
    return _client


async def init_qdrant() -> None:
    """
    Create the AsyncQdrantClient singleton and ensure all required
    collections exist.
    """
    global _client

    # Qdrant Cloud gives a full URL (https://xxxx.cloud.qdrant.io).
    # The host= + port= form only works for bare hostnames like "localhost".
    # If QDRANT_HOST already starts with http, pass it as url= instead.
    if settings.QDRANT_HOST.startswith("http"):
        connect_url = settings.QDRANT_HOST
        _client = AsyncQdrantClient(
            url=connect_url,
            api_key=settings.QDRANT_API_KEY or None,
            check_compatibility=False,
        )
    else:
        connect_url = f"{'https' if settings.QDRANT_HTTPS else 'http'}://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        _client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            https=settings.QDRANT_HTTPS,
            api_key=settings.QDRANT_API_KEY or None,
            check_compatibility=False,
        )

    logger.info("Connecting to Qdrant at: %s", connect_url)

    try:
        response = await _client.get_collections()
        existing = {c.name for c in response.collections}

        for name, params in COLLECTIONS.items():
            if name not in existing:
                await _client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=params["size"],
                        distance=params["distance"],
                    ),
                )
                logger.info("Created Qdrant collection: %s", name)
            else:
                logger.info("Qdrant collection already exists: %s", name)

    except Exception as exc:
        # Log the exact URL so it's easy to verify in Railway logs.
        # The app still starts — endpoints that don't need Qdrant will work.
        # Search/recommendation endpoints will fail with a clear error at call time.
        logger.error(
            "Qdrant startup check failed (URL: %s) — %s: %s. "
            "Search and recommendation endpoints will be unavailable until Qdrant is reachable.",
            connect_url, type(exc).__name__, exc,
        )
        # Keep _client set so the app can retry at request time rather than crash.


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Qdrant client closed")
