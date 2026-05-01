from app.application.errors import AppointmentNotFoundError
from app.domain.entities.appointment import Appointment
from app.domain.interfaces.appointment_repository import AppointmentRepository


class GetAppointmentUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, appointment_id: str) -> Appointment:
        appointment = await self._repository.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(appointment_id)
        return appointment
