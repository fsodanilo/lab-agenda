from unittest.mock import AsyncMock

import pytest

from app.application.errors import AppointmentNotFoundError
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase
from app.domain.interfaces.appointment_repository import AppointmentRepository


@pytest.mark.anyio
async def test_delete_appointment_calls_repository_delete() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    repository.delete.return_value = True
    use_case = DeleteAppointmentUseCase(repository=repository)

    await use_case.execute("appointment-1")

    repository.delete.assert_awaited_once_with("appointment-1")


@pytest.mark.anyio
async def test_delete_appointment_raises_when_not_found() -> None:
    repository = AsyncMock(spec=AppointmentRepository)
    repository.delete.return_value = False
    use_case = DeleteAppointmentUseCase(repository=repository)

    with pytest.raises(AppointmentNotFoundError):
        await use_case.execute("missing-id")
