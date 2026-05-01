from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.errors import AppointmentNotFoundError
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@pytest.mark.anyio
async def test_get_appointment_returns_repository_result() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    appointment = Appointment(
        id="appointment-1",
        user_id="user-1",
        datetime=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        status=AppointmentStatus.CONFIRMED,
        notes="retorno",
    )
    repository.get_by_id.return_value = appointment
    use_case = GetAppointmentUseCase(repository=repository)

    result = await use_case.execute("appointment-1")

    assert result == appointment
    repository.get_by_id.assert_awaited_once_with("appointment-1")


@pytest.mark.anyio
async def test_get_appointment_raises_when_not_found() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    repository.get_by_id.return_value = None
    use_case = GetAppointmentUseCase(repository=repository)

    with pytest.raises(AppointmentNotFoundError):
        await use_case.execute("missing-id")
