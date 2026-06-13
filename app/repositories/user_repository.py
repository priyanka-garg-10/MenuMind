from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import OTPSession, User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, phone: str) -> User:
        user = User(phone=phone)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user


class OTPRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, phone: str, otp_code: str, expires_at: datetime) -> OTPSession:
        # Invalidate all previous unused OTPs for this phone before creating a new one
        await self.db.execute(
            update(OTPSession)
            .where(OTPSession.phone == phone, OTPSession.is_used == False)  # noqa: E712
            .values(is_used=True)
        )
        session = OTPSession(phone=phone, otp_code=otp_code, expires_at=expires_at)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_valid(self, phone: str, otp_code: str) -> OTPSession | None:
        now = _utcnow()
        result = await self.db.execute(
            select(OTPSession).where(
                OTPSession.phone == phone,
                OTPSession.otp_code == otp_code,
                OTPSession.is_used == False,  # noqa: E712
                OTPSession.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, session_id: int) -> None:
        await self.db.execute(
            update(OTPSession).where(OTPSession.id == session_id).values(is_used=True)
        )
        await self.db.commit()
