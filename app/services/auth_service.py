import random
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.security import create_access_token
from app.models.user import User
from app.repositories.user_repository import OTPRepository, UserRepository
from app.schemas.auth_schemas import SendOTPResponse, TokenResponse
from app.schemas.user_schemas import UserResponse

logger = get_logger(__name__)
settings = get_settings()


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)
        self.otp_repo = OTPRepository(db)

    async def send_otp(self, phone: str) -> SendOTPResponse:
        otp = _generate_otp()
        expires_at = _utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        await self.otp_repo.create(phone=phone, otp_code=otp, expires_at=expires_at)

        logger.info("OTP generated for phone=%s (mock — not sent via SMS)", phone)

        # In production: call SMS gateway here and do NOT return the OTP
        return SendOTPResponse(message="OTP sent successfully", otp=otp)

    async def verify_otp(self, phone: str, otp: str) -> TokenResponse:
        otp_session = await self.otp_repo.get_valid(phone=phone, otp_code=otp)

        if otp_session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        await self.otp_repo.mark_used(otp_session.id)

        user = await self.user_repo.get_by_phone(phone)
        is_new_user = user is None

        if is_new_user:
            user = await self.user_repo.create(phone=phone)
            logger.info("New user created: user_id=%s phone=%s", user.id, phone)
        else:
            logger.info("Existing user logged in: user_id=%s", user.id)

        token = create_access_token(user.id)

        return TokenResponse(
            access_token=token,
            is_new_user=is_new_user,
            user=UserResponse.model_validate(user),
        )

    async def get_user_from_token(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return user
