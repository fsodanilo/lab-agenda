from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.config.settings import Settings
from app.infrastructure.dependencies import get_settings
from app.infrastructure.logging.logger import configure_logging, get_logger
from app.presentation.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("starting_application", extra={"environment": settings.app_env})
    yield
    logger.info("stopping_application")


def create_application() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.include_router(api_router)
    return application


app = create_application()
