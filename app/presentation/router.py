from fastapi import APIRouter

from app.presentation.api.routes.appointments import router as appointments_router
from app.presentation.api.routes.health import router as health_router
from app.presentation.api.routes.telegram import router as telegram_router

api_router = APIRouter()
api_router.include_router(appointments_router)
api_router.include_router(health_router)
api_router.include_router(telegram_router)
