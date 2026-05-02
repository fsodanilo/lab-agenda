from fastapi.testclient import TestClient

from app.infrastructure.dependencies import get_telegram_webhook_service
from app.main import create_application
from app.presentation.api.schemas.telegram import TelegramUpdate


class FakeTelegramWebhookService:
    def __init__(self) -> None:
        self.payload: TelegramUpdate | None = None

    async def handle_update(self, update: TelegramUpdate) -> str:
        self.payload = update
        return "ok"


def test_telegram_webhook_receives_update() -> None:
    app = create_application()
    service = FakeTelegramWebhookService()

    app.dependency_overrides[get_telegram_webhook_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/telegram/webhook",
            json={
                "update_id": 1,
                "message": {
                    "message_id": 42,
                    "text": "Tenho horario amanha?",
                    "chat": {"id": 1001},
                    "from": {"id": 2002},
                },
            },
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert service.payload is not None
    assert service.payload.message is not None
    assert service.payload.message.text == "Tenho horario amanha?"
    assert service.payload.message.sender.id == 2002
