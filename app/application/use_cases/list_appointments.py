from app.domain.entities.appointment import Appointment
from app.domain.interfaces.appointment_repository import AppointmentRepository


class ListAppointmentsUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: str | None = None) -> list[Appointment]:
        return await self._repository.list(user_id=user_id)
