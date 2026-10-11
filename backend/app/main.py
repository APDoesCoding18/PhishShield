import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application Startup
    setup_logging()
    logger.info("PhishShield application starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    # Ensure tables exist for SQLite/dev setups
    from app.models.base import Base
    from app.core.database import engine
    Base.metadata.create_all(bind=engine)
    yield
    # Application Shutdown
    logger.info("PhishShield application shutting down...")

app = FastAPI(
    title="PhishShield API",
    description="AI-Driven Phishing Email & Malicious Attachment Sandboxing Portal",
    version="0.1.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
