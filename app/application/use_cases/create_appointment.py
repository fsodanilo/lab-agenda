from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository
from app.domain.interfaces.calendar_service import CalendarService


@dataclass(frozen=True, slots=True)
class CreateAppointmentCommand:
    user_id: str
    datetime: datetime
    notes: str | None = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


class CreateAppointmentUseCase:
    def __init__(
        self,
        repository: AppointmentRepository,
        calendar_service: CalendarService,
    ) -> None:
        self._repository = repository
        self._calendar_service = calendar_service

    async def execute(self, command: CreateAppointmentCommand) -> Appointment:
        appointment = Appointment(
            user_id=command.user_id,
            datetime=command.datetime,
            status=command.status,
            notes=command.notes,
        )
        event_id = await self._calendar_service.create_event(appointment)
        appointment = Appointment(
            user_id=command.user_id,
            datetime=command.datetime,
            status=command.status,
            notes=command.notes,
            event_id=event_id,
        )
        return await self._repository.create(appointment)
