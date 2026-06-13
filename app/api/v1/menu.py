from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.vector_store import get_qdrant_client
from app.schemas.menu_schemas import (
    IngestResponse,
    MenuItemRequest,
    MenuItemResponse,
    MenuSearchRequest,
    MenuSearchResult,
)
from app.services.menu_service import MenuService

router = APIRouter()


def _service(
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_client),
) -> MenuService:
    return MenuService(db, qdrant)


@router.post("/items", response_model=MenuItemResponse, status_code=201)
async def create_menu_item(
    payload: MenuItemRequest,
    svc: MenuService = Depends(_service),
):
    """Add a menu item to MySQL and index it in Qdrant immediately."""
    return await svc.create_item(payload)


@router.get("/items", response_model=list[MenuItemResponse])
async def list_menu_items(svc: MenuService = Depends(_service)):
    """Return all available menu items."""
    return await svc.get_all_items()


@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: int, svc: MenuService = Depends(_service)):
    """Return a single menu item by MySQL ID."""
    return await svc.get_item(item_id)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_menu(svc: MenuService = Depends(_service)):
    """
    Batch-index all menu items that do not yet have a Qdrant ID.
    Call this after bulk-inserting rows directly into MySQL,
    or after resetting the Qdrant collection.
    """
    return await svc.ingest_unindexed()


@router.post("/search", response_model=list[MenuSearchResult])
async def search_menu(
    payload: MenuSearchRequest,
    svc: MenuService = Depends(_service),
):
    """
    Semantic search over the menu using RAG.
    Example queries:
      - "high protein grilled chicken"
      - "light vegetarian starter under 200 calories"
      - "spicy Indian curry"
    """
    return await svc.search(payload)
