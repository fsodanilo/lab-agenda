from datetime import UTC, date, datetime

import pytest

from app.application.use_cases.find_available_slots import FindAvailableSlotsUseCase
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


class InMemoryAppointmentRepository(AppointmentRepository):
    def __init__(self, items: list[Appointment]) -> None:
        self._items = items

    async def create(self, entity: Appointment) -> Appointment:
        raise NotImplementedError

    async def get_by_id(self, entity_id: str) -> Appointment | None:
        raise NotImplementedError

    async def update(self, entity_id: str, entity: Appointment) -> Appointment | None:
        raise NotImplementedError

    async def delete(self, entity_id: str) -> bool:
        raise NotImplementedError

    async def list(self, user_id: str | None = None) -> list[Appointment]:
        return list(self._items)


@pytest.mark.anyio
async def test_find_available_slots_excludes_booked_hours() -> None:
    repository = InMemoryAppointmentRepository(
        [
            Appointment(
                id="appt-1",
                user_id="user-1",
                datetime=datetime(2026, 5, 4, 13, 0, tzinfo=UTC),
                status=AppointmentStatus.SCHEDULED,
            )
        ]
    )
    use_case = FindAvailableSlotsUseCase(repository=repository)

    slots = await use_case.execute(date(2026, 5, 4))

    assert all(slot.hour != 10 for slot in slots)
    assert any(slot.hour == 9 for slot in slots)
    assert any(slot.hour == 11 for slot in slots)


@pytest.mark.anyio
async def test_find_available_slots_returns_empty_for_sunday() -> None:
    repository = InMemoryAppointmentRepository([])
    use_case = FindAvailableSlotsUseCase(repository=repository)

    slots = await use_case.execute(date(2026, 5, 10))

    assert slots == []
