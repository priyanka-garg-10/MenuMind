from fastapi import HTTPException, status
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.rag.embedder import Embedder
from app.rag.indexer import MenuIndexer
from app.rag.retriever import MenuRetriever
from app.repositories.menu_repository import MenuRepository
from app.schemas.menu_schemas import (
    IngestResponse,
    MenuItemRequest,
    MenuItemResponse,
    MenuSearchRequest,
    MenuSearchResult,
)

logger = get_logger(__name__)


class MenuService:
    def __init__(self, db: AsyncSession, qdrant: AsyncQdrantClient) -> None:
        self.menu_repo = MenuRepository(db)
        embedder = Embedder()
        self.indexer = MenuIndexer(qdrant, embedder)
        self.retriever = MenuRetriever(qdrant, embedder)

    async def create_item(self, data: MenuItemRequest) -> MenuItemResponse:
        """
        Create a menu item in MySQL, index it in Qdrant, then store the
        Qdrant point ID back in MySQL.  All three steps must succeed.
        """
        item = await self.menu_repo.create(**data.model_dump())
        logger.info("Menu item saved to MySQL: id=%s name=%r", item.id, item.name)

        qdrant_id = await self.indexer.index_item(item)
        item = await self.menu_repo.update(item, qdrant_id=qdrant_id)
        logger.info("Menu item indexed in Qdrant: id=%s qdrant_id=%s", item.id, qdrant_id)

        return MenuItemResponse.model_validate(item)

    async def get_all_items(self) -> list[MenuItemResponse]:
        items = await self.menu_repo.get_all()
        return [MenuItemResponse.model_validate(i) for i in items]

    async def get_item(self, item_id: int) -> MenuItemResponse:
        item = await self.menu_repo.get_by_id(item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        return MenuItemResponse.model_validate(item)

    async def ingest_unindexed(self) -> IngestResponse:
        """
        Batch-index all menu items that don't have a Qdrant ID yet.
        Useful after bulk MySQL inserts or after a Qdrant reset.
        """
        items = await self.menu_repo.get_unindexed()
        if not items:
            return IngestResponse(indexed=0, message="All menu items are already indexed")

        qdrant_ids = await self.indexer.index_batch(items)

        for item, qid in zip(items, qdrant_ids):
            await self.menu_repo.update(item, qdrant_id=qid)

        logger.info("Batch ingestion complete: %d items indexed", len(items))
        return IngestResponse(
            indexed=len(items),
            message=f"Successfully indexed {len(items)} menu items",
        )

    async def search(self, data: MenuSearchRequest) -> list[MenuSearchResult]:
        """
        Semantic search over the Qdrant menu collection.
        This is the RAG retrieval step — used directly in Phase 4 for testing,
        and called by the Recommendation Agent in Phase 7.
        """
        raw = await self.retriever.search(
            query=data.query,
            limit=data.limit,
            is_veg=data.is_veg,
            cuisine=data.cuisine,
            max_calories=data.max_calories,
            min_protein=data.min_protein,
        )
        return [MenuSearchResult(**r) for r in raw]
