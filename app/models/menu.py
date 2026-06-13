import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, JSON, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MenuSpiceLevel(str, enum.Enum):
    NONE = "none"
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"
    EXTRA_HOT = "extra_hot"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    spice_level: Mapped[MenuSpiceLevel] = mapped_column(
        SAEnum(MenuSpiceLevel), default=MenuSpiceLevel.MEDIUM, nullable=False
    )
    is_veg: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ingredients: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # UUID of the corresponding Qdrant point — null until indexed
    qdrant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MenuItem id={self.id} name={self.name!r}>"
