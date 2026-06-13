from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth_schemas import SendOTPRequest, SendOTPResponse, TokenResponse, VerifyOTPRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(payload: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Send a 6-digit OTP to the given phone number.
    In this mocked implementation the OTP is returned directly in the response.
    """
    service = AuthService(db)
    return await service.send_otp(phone=payload.phone)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP and return a JWT bearer token.
    `is_new_user=true` means the user was just created — frontend should
    redirect to the preference collection flow.
    """
    service = AuthService(db)
    return await service.verify_otp(phone=payload.phone, otp=payload.otp)
