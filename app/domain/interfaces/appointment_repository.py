from abc import abstractmethod

from app.domain.entities.appointment import Appointment
from app.domain.interfaces.base_repository import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    @abstractmethod
    async def list_by_user_id(self, user_id: str) -> list[Appointment]:
        """Return all appointments for a given user."""
