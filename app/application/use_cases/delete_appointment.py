from app.application.errors import AppointmentNotFoundError
from app.domain.interfaces.appointment_repository import AppointmentRepository


class DeleteAppointmentUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, appointment_id: str) -> None:
        deleted = await self._repository.delete(appointment_id)
        if not deleted:
            raise AppointmentNotFoundError(appointment_id)
