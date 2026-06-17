from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — registers all ORM models with Base.metadata before init_db()

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging_config import get_logger, setup_logging
from app.core.vector_store import close_qdrant, init_qdrant

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup 
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    await init_db()
    await init_qdrant()

    yield

    #Shutdown 
    logger.info("Shutting down %s", settings.APP_NAME)
    await close_qdrant()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Restaurant Personalization Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "title": settings.APP_NAME}
