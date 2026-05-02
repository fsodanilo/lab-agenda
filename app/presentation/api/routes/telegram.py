from fastapi import APIRouter, Depends

from app.infrastructure.dependencies import get_telegram_webhook_service
from app.infrastructure.services.telegram_multi_agent_service import TelegramWebhookService
from app.presentation.api.schemas.telegram import TelegramUpdate

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def receive_telegram_webhook(
    payload: TelegramUpdate,
    service: TelegramWebhookService = Depends(get_telegram_webhook_service),
) -> dict[str, bool]:
    await service.handle_update(payload)
    return {"ok": True}
