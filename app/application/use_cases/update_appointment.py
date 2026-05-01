from dataclasses import dataclass
from datetime import datetime

from app.application.errors import AppointmentNotFoundError
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@dataclass(frozen=True, slots=True)
class UpdateAppointmentCommand:
    appointment_id: str
    user_id: str
    datetime: datetime
    status: AppointmentStatus
    notes: str | None = None


class UpdateAppointmentUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateAppointmentCommand) -> Appointment:
        existing = await self._repository.get_by_id(command.appointment_id)
        if existing is None:
            raise AppointmentNotFoundError(command.appointment_id)

        appointment = Appointment(
            id=command.appointment_id,
            user_id=command.user_id,
            datetime=command.datetime,
            status=command.status,
            notes=command.notes,
        )
        updated = await self._repository.update(command.appointment_id, appointment)
        if updated is None:
            raise AppointmentNotFoundError(command.appointment_id)
        return updated
