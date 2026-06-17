"""
Seed script: loads initial menu data into MySQL and indexes it in Qdrant.

Usage (from the project root with venv activated):
    python scripts/seed_menu.py
"""
import asyncio
import os
import sys

# Allow imports from the project root regardless of where the script is run from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import app.models  # noqa: F401 — registers ORM models with Base.metadata

from app.core.database import AsyncSessionLocal, init_db
from app.core.logging_config import get_logger, setup_logging
from app.core.vector_store import init_qdrant, get_qdrant_client
from app.rag.embedder import Embedder
from app.rag.indexer import MenuIndexer
from app.repositories.menu_repository import MenuRepository

setup_logging()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Menu data — realistic Indian restaurant with full nutritional profiles
# ---------------------------------------------------------------------------
MENU: list[dict] = [
    
    {
        "name": "Samosa (2 pcs)",
        "description": "Crispy pastry filled with spiced potato and green peas, served with mint chutney",
        "cuisine": "Indian",
        "category": "Starter",
        "price": 120.0,
        "calories": 280,
        "protein_g": 6.0,
        "carbs_g": 38.0,
        "fat_g": 12.0,
        "spice_level": "medium",
        "is_veg": True,
        "ingredients": ["potato", "green peas", "pastry", "cumin", "coriander", "green chili"],
        "tags": ["fried", "street-food", "snack", "popular"],
    },
    {
        "name": "Paneer Tikka",
        "description": "Chunks of fresh cottage cheese marinated in spiced yogurt, grilled in tandoor",
        "cuisine": "Indian",
        "category": "Starter",
        "price": 280.0,
        "calories": 320,
        "protein_g": 22.0,
        "carbs_g": 8.0,
        "fat_g": 22.0,
        "spice_level": "medium",
        "is_veg": True,
        "ingredients": ["paneer", "yogurt", "bell pepper", "onion", "tandoori masala", "lemon"],
        "tags": ["grilled", "high-protein", "tandoor", "vegetarian-favorite"],
    },
    {
        "name": "Chicken Tikka",
        "description": "Boneless chicken pieces marinated in yogurt and spices, grilled over charcoal",
        "cuisine": "Indian",
        "category": "Starter",
        "price": 320.0,
        "calories": 350,
        "protein_g": 35.0,
        "carbs_g": 4.0,
        "fat_g": 18.0,
        "spice_level": "medium",
        "is_veg": False,
        "ingredients": ["chicken", "yogurt", "ginger", "garlic", "red chili", "garam masala"],
        "tags": ["grilled", "high-protein", "tandoor", "low-carb", "keto-friendly"],
    },
    {
        "name": "Hara Bhara Kabab",
        "description": "Pan-fried patties made with spinach, peas and potatoes, rich in iron",
        "cuisine": "Indian",
        "category": "Starter",
        "price": 220.0,
        "calories": 180,
        "protein_g": 8.0,
        "carbs_g": 24.0,
        "fat_g": 7.0,
        "spice_level": "mild",
        "is_veg": True,
        "ingredients": ["spinach", "green peas", "potato", "paneer", "cumin", "coriander"],
        "tags": ["healthy", "iron-rich", "low-calorie", "green", "fitness"],
    },
    {
        "name": "Soup of the Day",
        "description": "Light and nutritious lentil soup with turmeric and ginger",
        "cuisine": "Indian",
        "category": "Starter",
        "price": 150.0,
        "calories": 120,
        "protein_g": 7.0,
        "carbs_g": 18.0,
        "fat_g": 3.0,
        "spice_level": "mild",
        "is_veg": True,
        "ingredients": ["red lentil", "turmeric", "ginger", "garlic", "tomato"],
        "tags": ["light", "healthy", "low-calorie", "soup", "weight-loss"],
    },
  
    {
        "name": "Dal Makhani",
        "description": "Slow-cooked black lentils in a rich buttery tomato sauce, simmered overnight",
        "cuisine": "Indian",
        "category": "Main",
        "price": 280.0,
        "calories": 380,
        "protein_g": 16.0,
        "carbs_g": 42.0,
        "fat_g": 16.0,
        "spice_level": "medium",
        "is_veg": True,
        "ingredients": ["black lentil", "kidney beans", "butter", "cream", "tomato", "ginger", "garlic"],
        "tags": ["protein-rich", "comfort-food", "lentil", "creamy", "popular"],
    },
    {
        "name": "Palak Paneer",
        "description": "Fresh cottage cheese cubes in a smooth, spiced spinach gravy",
        "cuisine": "Indian",
        "category": "Main",
        "price": 300.0,
        "calories": 340,
        "protein_g": 18.0,
        "carbs_g": 12.0,
        "fat_g": 24.0,
        "spice_level": "mild",
        "is_veg": True,
        "ingredients": ["spinach", "paneer", "onion", "tomato", "ginger", "garlic", "cream"],
        "tags": ["iron-rich", "calcium-rich", "high-protein", "green", "healthy"],
    },
    {
        "name": "Chana Masala",
        "description": "Bold and tangy chickpea curry with whole spices and amchur",
        "cuisine": "Indian",
        "category": "Main",
        "price": 260.0,
        "calories": 310,
        "protein_g": 15.0,
        "carbs_g": 46.0,
        "fat_g": 8.0,
        "spice_level": "hot",
        "is_veg": True,
        "ingredients": ["chickpeas", "onion", "tomato", "amchur", "cumin", "coriander", "green chili"],
        "tags": ["high-fiber", "protein-rich", "vegan", "gluten-free", "budget"],
    },
    {
        "name": "Veg Biryani",
        "description": "Fragrant basmati rice layered with seasonal vegetables and caramelised onions",
        "cuisine": "Indian",
        "category": "Main",
        "price": 300.0,
        "calories": 480,
        "protein_g": 9.0,
        "carbs_g": 82.0,
        "fat_g": 12.0,
        "spice_level": "medium",
        "is_veg": True,
        "ingredients": ["basmati rice", "mixed vegetables", "onion", "saffron", "mint", "whole spices"],
        "tags": ["rice", "festive", "aromatic", "filling"],
    },
    
    {
        "name": "Butter Chicken",
        "description": "Tender chicken in a silky, mildly spiced tomato and butter sauce",
        "cuisine": "Indian",
        "category": "Main",
        "price": 380.0,
        "calories": 420,
        "protein_g": 32.0,
        "carbs_g": 14.0,
        "fat_g": 26.0,
        "spice_level": "mild",
        "is_veg": False,
        "ingredients": ["chicken", "butter", "cream", "tomato", "cashew", "cardamom", "fenugreek"],
        "tags": ["creamy", "high-protein", "mild", "popular", "comfort-food"],
    },
    {
        "name": "Chicken Biryani",
        "description": "Aromatic basmati rice slow-cooked with marinated chicken and whole spices",
        "cuisine": "Indian",
        "category": "Main",
        "price": 400.0,
        "calories": 620,
        "protein_g": 38.0,
        "carbs_g": 68.0,
        "fat_g": 18.0,
        "spice_level": "medium",
        "is_veg": False,
        "ingredients": ["chicken", "basmati rice", "onion", "yogurt", "saffron", "mint", "fried onion"],
        "tags": ["rice", "high-protein", "aromatic", "filling", "popular"],
    },
    {
        "name": "Grilled Fish",
        "description": "Whole pomfret marinated in coastal spices and grilled over charcoal",
        "cuisine": "Indian",
        "category": "Main",
        "price": 480.0,
        "calories": 280,
        "protein_g": 42.0,
        "carbs_g": 3.0,
        "fat_g": 10.0,
        "spice_level": "medium",
        "is_veg": False,
        "ingredients": ["pomfret", "kokum", "coconut", "green chili", "garlic", "ginger"],
        "tags": ["grilled", "high-protein", "low-carb", "omega-3", "coastal", "keto-friendly"],
    },
    {
        "name": "Lamb Rogan Josh",
        "description": "Slow-cooked lamb in a rich Kashmiri sauce with whole spices and dried ginger",
        "cuisine": "Indian",
        "category": "Main",
        "price": 520.0,
        "calories": 460,
        "protein_g": 35.0,
        "carbs_g": 10.0,
        "fat_g": 30.0,
        "spice_level": "hot",
        "is_veg": False,
        "ingredients": ["lamb", "Kashmiri chili", "yogurt", "fennel", "dried ginger", "cardamom"],
        "tags": ["slow-cooked", "high-protein", "Kashmiri", "bold-flavor", "premium"],
    },
   
    {
        "name": "Garlic Naan",
        "description": "Soft leavened bread topped with garlic and butter, baked in tandoor",
        "cuisine": "Indian",
        "category": "Bread",
        "price": 80.0,
        "calories": 260,
        "protein_g": 7.0,
        "carbs_g": 44.0,
        "fat_g": 7.0,
        "spice_level": "none",
        "is_veg": True,
        "ingredients": ["flour", "garlic", "butter", "yeast", "milk"],
        "tags": ["bread", "tandoor", "accompaniment", "popular"],
    },
    
    {
        "name": "Gulab Jamun",
        "description": "Soft milk-solid dumplings soaked in rose-flavoured sugar syrup",
        "cuisine": "Indian",
        "category": "Dessert",
        "price": 120.0,
        "calories": 380,
        "protein_g": 5.0,
        "carbs_g": 68.0,
        "fat_g": 10.0,
        "spice_level": "none",
        "is_veg": True,
        "ingredients": ["milk solids", "sugar", "rose water", "cardamom", "saffron"],
        "tags": ["sweet", "indulgent", "high-sugar", "traditional", "dessert"],
    },
    {
        "name": "Mango Kulfi",
        "description": "Traditional Indian frozen dessert made with condensed milk and Alphonso mango",
        "cuisine": "Indian",
        "category": "Dessert",
        "price": 150.0,
        "calories": 220,
        "protein_g": 5.0,
        "carbs_g": 34.0,
        "fat_g": 8.0,
        "spice_level": "none",
        "is_veg": True,
        "ingredients": ["condensed milk", "mango pulp", "cardamom", "pistachio"],
        "tags": ["frozen", "mango", "refreshing", "summer", "lower-calorie-dessert"],
    },
   
    {
        "name": "Masala Chai",
        "description": "Spiced Indian tea brewed with ginger, cardamom and cinnamon",
        "cuisine": "Indian",
        "category": "Beverage",
        "price": 60.0,
        "calories": 80,
        "protein_g": 3.0,
        "carbs_g": 12.0,
        "fat_g": 2.0,
        "spice_level": "mild",
        "is_veg": True,
        "ingredients": ["black tea", "milk", "ginger", "cardamom", "cinnamon", "sugar"],
        "tags": ["hot-drink", "warming", "antioxidant", "low-calorie"],
    },
    {
        "name": "Mango Lassi",
        "description": "Thick yogurt-based drink blended with fresh Alphonso mango and a hint of cardamom",
        "cuisine": "Indian",
        "category": "Beverage",
        "price": 120.0,
        "calories": 210,
        "protein_g": 6.0,
        "carbs_g": 38.0,
        "fat_g": 4.0,
        "spice_level": "none",
        "is_veg": True,
        "ingredients": ["yogurt", "mango", "cardamom", "sugar"],
        "tags": ["cold-drink", "probiotic", "mango", "cooling", "refreshing"],
    },
    {
        "name": "Fresh Lime Soda",
        "description": "Freshly squeezed lime with sparkling water and a pinch of black salt",
        "cuisine": "Indian",
        "category": "Beverage",
        "price": 80.0,
        "calories": 40,
        "protein_g": 0.0,
        "carbs_g": 10.0,
        "fat_g": 0.0,
        "spice_level": "none",
        "is_veg": True,
        "ingredients": ["lime", "sparkling water", "black salt", "sugar"],
        "tags": ["cold-drink", "low-calorie", "refreshing", "weight-loss", "vegan"],
    },
]


async def seed() -> None:
    from sqlalchemy import delete as sa_delete
    from app.models.menu import MenuItem
    from app.core.database import engine

    logger.info("Starting menu seed...")

    await init_db()
    await init_qdrant()

    async with AsyncSessionLocal() as db:
        repo = MenuRepository(db)
        existing = await repo.get_all()

        if len(existing) == len(MENU):
            logger.info("Menu fully seeded (%d items). Skipping insert.", len(existing))
        else:
            if existing:
                # Partial seed from a previous failed run — wipe and restart clean
                logger.info(
                    "Partial seed detected (%d/%d items). Clearing and re-seeding...",
                    len(existing), len(MENU)
                )
                await db.execute(sa_delete(MenuItem))
                await db.commit()

            for data in MENU:
                await repo.create(**data)
            logger.info("Inserted %d menu items into MySQL.", len(MENU))

        # Index any items that don't yet have a Qdrant ID
        unindexed = await repo.get_unindexed()
        if not unindexed:
            logger.info("All items already indexed in Qdrant.")
        else:
            logger.info("Indexing %d items in Qdrant...", len(unindexed))
            qdrant = get_qdrant_client()
            embedder = Embedder()
            indexer = MenuIndexer(qdrant, embedder)

            ids = await indexer.index_batch(unindexed)
            for item, qid in zip(unindexed, ids):
                await repo.update(item, qdrant_id=qid)

            logger.info("Seed complete. %d items indexed.", len(unindexed))

    # Explicitly dispose the engine so aiomysql connections close before
    # the event loop shuts down — prevents the "Event loop is closed" noise.
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
