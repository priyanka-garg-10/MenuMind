import re

from pydantic import BaseModel, field_validator

from app.schemas.user_schemas import UserResponse


class SendOTPRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError("Phone must be 10–15 digits, optionally starting with +")
        return v


class SendOTPResponse(BaseModel):
    message: str
    # Returned directly in this mocked implementation.
    # In production this field is removed and OTP is delivered via SMS.
    otp: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return v.strip()

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP must be a 6-digit number")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user: UserResponse
