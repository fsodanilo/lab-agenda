from abc import ABC, abstractmethod

from app.domain.entities.health_status import HealthStatus


class HealthService(ABC):
    @abstractmethod
    def check(self) -> HealthStatus:
        """Return the current health status for the application."""
