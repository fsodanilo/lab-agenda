from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@pytest.mark.anyio
async def test_list_appointments_returns_repository_result() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    appointments = [
        Appointment(
            id="appointment-1",
            user_id="user-1",
            datetime=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
            status=AppointmentStatus.SCHEDULED,
            notes=None,
        )
    ]
    repository.list.return_value = appointments
    use_case = ListAppointmentsUseCase(repository=repository)

    result = await use_case.execute(user_id="user-1")

    assert result == appointments
    repository.list.assert_awaited_once_with(user_id="user-1")
