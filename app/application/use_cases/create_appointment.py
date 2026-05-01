from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository


@dataclass(frozen=True, slots=True)
class CreateAppointmentCommand:
    user_id: str
    datetime: datetime
    notes: str | None = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


class CreateAppointmentUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateAppointmentCommand) -> Appointment:
        appointment = Appointment(
            user_id=command.user_id,
            datetime=command.datetime,
            status=command.status,
            notes=command.notes,
        )
        return await self._repository.create(appointment)
