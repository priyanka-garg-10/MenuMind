import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DietType(str, enum.Enum):
    VEG = "veg"
    NON_VEG = "non_veg"
    VEGAN = "vegan"
    JAIN = "jain"


class SpiceLevel(str, enum.Enum):
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"
    EXTRA_HOT = "extra_hot"


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # unique=True enforces one preference record per user at the DB level
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    diet_type: Mapped[DietType] = mapped_column(SAEnum(DietType), nullable=False)
    spice_level: Mapped[SpiceLevel] = mapped_column(
        SAEnum(SpiceLevel), default=SpiceLevel.MEDIUM, nullable=False
    )
    # JSON columns store Python lists as MySQL JSON arrays
    favorite_cuisines: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    allergies: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    health_goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
