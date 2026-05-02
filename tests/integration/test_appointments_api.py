from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.calendar_service import CalendarService
from app.domain.interfaces.appointment_repository import AppointmentRepository
from app.infrastructure.dependencies import (
    get_calendar_service,
    get_create_appointment_use_case,
)
from app.main import create_application


class InMemoryAppointmentRepository(AppointmentRepository):
    def __init__(self) -> None:
        self._items: dict[str, Appointment] = {}

    async def create(self, entity: Appointment) -> Appointment:
        appointment = Appointment(
            id="integration-1",
            user_id=entity.user_id,
            datetime=entity.datetime,
            status=entity.status,
            notes=entity.notes,
            event_id=entity.event_id,
        )
        self._items[appointment.id] = appointment
        return appointment

    async def get_by_id(self, entity_id: str) -> Appointment | None:
        return self._items.get(entity_id)

    async def update(self, entity_id: str, entity: Appointment) -> Appointment | None:
        if entity_id not in self._items:
            return None
        updated = Appointment(
            id=entity_id,
            user_id=entity.user_id,
            datetime=entity.datetime,
            status=entity.status,
            notes=entity.notes,
            event_id=entity.event_id,
        )
        self._items[entity_id] = updated
        return updated

    async def delete(self, entity_id: str) -> bool:
        return self._items.pop(entity_id, None) is not None

    async def list(self, user_id: str | None = None) -> list[Appointment]:
        items = list(self._items.values())
        if user_id is None:
            return items
        return [item for item in items if item.user_id == user_id]


class FakeCalendarService(CalendarService):
    async def create_event(self, appointment: Appointment) -> str:
        return "integration-event-1"


def test_create_appointment_endpoint_returns_created_resource() -> None:
    app = create_application()
    repository = InMemoryAppointmentRepository()
    calendar_service = FakeCalendarService()

    def override_use_case() -> CreateAppointmentUseCase:
        return CreateAppointmentUseCase(
            repository=repository,
            calendar_service=calendar_service,
        )

    def override_calendar_service() -> CalendarService:
        return calendar_service

    app.dependency_overrides[get_create_appointment_use_case] = override_use_case
    app.dependency_overrides[get_calendar_service] = override_calendar_service

    with TestClient(app) as client:
        response = client.post(
            "/appointments",
            json={
                "user_id": "user-123",
                "datetime": datetime(2026, 5, 3, 15, 30, tzinfo=UTC).isoformat(),
                "status": AppointmentStatus.SCHEDULED.value,
                "notes": "consulta por integracao",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": "integration-1",
        "user_id": "user-123",
        "datetime": "2026-05-03T15:30:00Z",
        "status": "scheduled",
        "notes": "consulta por integracao",
        "event_id": "integration-event-1",
    }
