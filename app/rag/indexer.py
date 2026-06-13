import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from app.models.menu import MenuItem
from app.rag.embedder import Embedder

_COLLECTION = "menu_items"


class MenuIndexer:
    """
    Write path of the RAG pipeline.
    Converts MenuItem ORM objects into Qdrant vector points.
    """

    def __init__(self, client: AsyncQdrantClient, embedder: Embedder) -> None:
        self.client = client
        self.embedder = embedder

    async def index_item(self, item: MenuItem) -> str:
        """
        Embed a single menu item and upsert it into Qdrant.
        Returns the UUID used as the Qdrant point ID.
        """
        point_id = str(uuid.uuid4())
        text = Embedder.build_menu_text(item)
        vector = await self.embedder.embed(text)

        await self.client.upsert(
            collection_name=_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=self._build_payload(item),
                )
            ],
        )
        return point_id

    async def index_batch(self, items: list[MenuItem]) -> list[str]:
        """
        Embed and upsert multiple items in one batched API call.
        More efficient than calling index_item() in a loop.
        Returns list of UUIDs in the same order as input items.
        """
        point_ids = [str(uuid.uuid4()) for _ in items]
        texts = [Embedder.build_menu_text(item) for item in items]
        vectors = await self.embedder.embed_batch(texts)

        points = [
            PointStruct(
                id=pid,
                vector=vector,
                payload=self._build_payload(item),
            )
            for pid, vector, item in zip(point_ids, vectors, items)
        ]

        await self.client.upsert(collection_name=_COLLECTION, points=points)
        return point_ids

    async def delete_item(self, qdrant_id: str) -> None:
        """Remove a vector point from Qdrant by its UUID."""
        from qdrant_client.models import PointIdsList

        await self.client.delete(
            collection_name=_COLLECTION,
            points_selector=PointIdsList(points=[qdrant_id]),
        )

    @staticmethod
    def _build_payload(item: MenuItem) -> dict:
        """
        The payload is stored alongside the vector in Qdrant.
        It serves two purposes:
          1. Filtering before similarity search (e.g. is_veg=True, cuisine=Indian)
          2. Returning results without a second MySQL round-trip
        """
        return {
            "mysql_id": item.id,
            "name": item.name,
            "cuisine": item.cuisine,
            "category": item.category,
            "is_veg": item.is_veg,
            "spice_level": item.spice_level.value if item.spice_level else None,
            "calories": item.calories,
            "protein_g": float(item.protein_g or 0),
            "carbs_g": float(item.carbs_g or 0),
            "fat_g": float(item.fat_g or 0),
            "price": float(item.price),
            "tags": item.tags or [],
            "is_available": item.is_available,
        }
