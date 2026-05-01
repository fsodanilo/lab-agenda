from abc import abstractmethod

from app.domain.entities.appointment import Appointment
from app.domain.interfaces.base_repository import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    @abstractmethod
    async def list(self, user_id: str | None = None) -> list[Appointment]:
        """Return appointments, optionally filtered by user."""
