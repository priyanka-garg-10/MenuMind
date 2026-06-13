from fastapi import APIRouter

from app.api.v1 import auth, menu, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/v1/users", tags=["Users"])
api_router.include_router(menu.router, prefix="/v1/menu", tags=["Menu"])
