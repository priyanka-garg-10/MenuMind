from pydantic import BaseModel, field_validator

from app.models.menu import MenuSpiceLevel


class MenuItemRequest(BaseModel):
    name: str
    description: str | None = None
    cuisine: str | None = None
    category: str | None = None
    price: float
    calories: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    spice_level: MenuSpiceLevel = MenuSpiceLevel.MEDIUM
    is_veg: bool = True
    is_available: bool = True
    ingredients: list[str] | None = None
    tags: list[str] | None = None

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2)


class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cuisine: str | None
    category: str | None
    price: float
    calories: int | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    spice_level: MenuSpiceLevel
    is_veg: bool
    is_available: bool
    ingredients: list[str] | None
    tags: list[str] | None
    qdrant_id: str | None

    model_config = {"from_attributes": True}


# ── RAG search schemas ────────────────────────────────────────────────────────

class MenuSearchRequest(BaseModel):
    query: str
    limit: int = 10
    is_veg: bool | None = None
    cuisine: str | None = None
    max_calories: int | None = None
    min_protein: float | None = None

    @field_validator("limit")
    @classmethod
    def limit_range(cls, v: int) -> int:
        if not 1 <= v <= 50:
            raise ValueError("limit must be between 1 and 50")
        return v


class MenuSearchResult(BaseModel):
    score: float
    mysql_id: int
    name: str
    cuisine: str | None
    category: str | None
    is_veg: bool
    spice_level: str | None
    calories: int | None
    protein_g: float
    price: float
    tags: list[str]
    is_available: bool


class IngestResponse(BaseModel):
    indexed: int
    message: str
