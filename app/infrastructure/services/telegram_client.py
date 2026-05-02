import httpx

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger


class TelegramClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger(__name__)

    async def send_message(self, chat_id: str, text: str) -> None:
        if not self._settings.telegram_bot_token:
            raise ValueError("APP_TELEGRAM_BOT_TOKEN is not configured")

        base_url = self._settings.telegram_api_base_url.rstrip("/")
        url = f"{base_url}/bot{self._settings.telegram_bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        self._logger.info("telegram_message_sent", extra={"chat_id": chat_id})
