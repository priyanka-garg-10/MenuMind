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

    _client = AsyncQdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        https=settings.QDRANT_HTTPS,          # explicit — never left to inference
        api_key=settings.QDRANT_API_KEY or None,
    )

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


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Qdrant client closed")
