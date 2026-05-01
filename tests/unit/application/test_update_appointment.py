from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.errors import AppointmentNotFoundError
from app.application.use_cases.update_appointment import (
    UpdateAppointmentCommand,
    UpdateAppointmentUseCase,
)
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@pytest.mark.anyio
async def test_update_appointment_returns_updated_entity() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    existing = Appointment(
        id="appointment-1",
        user_id="user-1",
        datetime=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        status=AppointmentStatus.SCHEDULED,
        notes="antes",
    )
    updated = Appointment(
        id="appointment-1",
        user_id="user-1",
        datetime=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
        status=AppointmentStatus.CONFIRMED,
        notes="depois",
    )
    repository.get_by_id.return_value = existing
    repository.update.return_value = updated
    use_case = UpdateAppointmentUseCase(repository=repository)

    result = await use_case.execute(
        UpdateAppointmentCommand(
            appointment_id="appointment-1",
            user_id="user-1",
            datetime=updated.datetime,
            status=updated.status,
            notes=updated.notes,
        )
    )

    assert result == updated
    repository.update.assert_awaited_once()


@pytest.mark.anyio
async def test_update_appointment_raises_when_entity_does_not_exist() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    repository.get_by_id.return_value = None
    use_case = UpdateAppointmentUseCase(repository=repository)

    with pytest.raises(AppointmentNotFoundError):
        await use_case.execute(
            UpdateAppointmentCommand(
                appointment_id="missing-id",
                user_id="user-1",
                datetime=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
                status=AppointmentStatus.CONFIRMED,
                notes="depois",
            )
        )
