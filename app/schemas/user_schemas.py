from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.preference import DietType, SpiceLevel


# ── User ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    phone: str
    name: str | None
    email: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip() if v else v


# ── Preferences ───────────────────────────────────────────────────────────────

class PreferenceRequest(BaseModel):
    diet_type: DietType
    spice_level: SpiceLevel = SpiceLevel.MEDIUM
    favorite_cuisines: list[str] | None = None
    allergies: list[str] | None = None
    health_goals: list[str] | None = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    diet_type: DietType
    spice_level: SpiceLevel
    favorite_cuisines: list[str] | None
    allergies: list[str] | None
    health_goals: list[str] | None
    updated_at: datetime

    model_config = {"from_attributes": True}
