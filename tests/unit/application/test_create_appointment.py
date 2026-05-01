from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.create_appointment import (
    CreateAppointmentCommand,
    CreateAppointmentUseCase,
)
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@pytest.mark.anyio
async def test_create_appointment_returns_repository_result() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    scheduled_for = datetime(2026, 5, 1, 14, 30)
    command = CreateAppointmentCommand(
        user_id="user-123",
        datetime=scheduled_for,
        notes="consulta inicial",
    )
    persisted = Appointment(
        id="appointment-1",
        user_id=command.user_id,
        datetime=scheduled_for,
        status=AppointmentStatus.SCHEDULED,
        notes=command.notes,
    )
    repository.create.return_value = persisted
    use_case = CreateAppointmentUseCase(repository=repository)

    result = await use_case.execute(command)

    assert result == persisted


@pytest.mark.anyio
async def test_create_appointment_validates_repository_call() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    scheduled_for = datetime(2026, 5, 1, 14, 30)
    repository.create.return_value = Appointment(
        id="appointment-3",
        user_id="user-789",
        datetime=scheduled_for,
        status=AppointmentStatus.SCHEDULED,
        notes="primeira consulta",
    )
    use_case = CreateAppointmentUseCase(repository=repository)

    await use_case.execute(
        CreateAppointmentCommand(
            user_id="user-789",
            datetime=scheduled_for,
            notes="primeira consulta",
        )
    )

    repository.create.assert_awaited_once()


@pytest.mark.anyio
async def test_create_appointment_calls_repository_with_domain_entity() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    scheduled_for = datetime(2026, 5, 2, 9, 0)
    command = CreateAppointmentCommand(
        user_id="user-456",
        datetime=scheduled_for,
        notes="retorno",
        status=AppointmentStatus.CONFIRMED,
    )
    repository.create.return_value = Appointment(
        id="appointment-2",
        user_id=command.user_id,
        datetime=scheduled_for,
        status=command.status,
        notes=command.notes,
    )
    use_case = CreateAppointmentUseCase(repository=repository)

    await use_case.execute(command)

    repository.create.assert_awaited_once()
    created_appointment = repository.create.await_args.args[0]
    assert isinstance(created_appointment, Appointment)
    assert created_appointment.id is None
    assert created_appointment.user_id == command.user_id
    assert created_appointment.datetime == command.datetime
    assert created_appointment.status == command.status
    assert created_appointment.notes == command.notes