from abc import ABC, abstractmethod

from app.domain.entities.appointment import Appointment


class CalendarService(ABC):
    @abstractmethod
    async def create_event(self, appointment: Appointment) -> str:
        """Create an external calendar event and return its identifier."""
