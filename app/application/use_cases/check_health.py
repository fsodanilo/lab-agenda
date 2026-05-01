from app.domain.entities.health_status import HealthStatus
from app.domain.interfaces.health_service import HealthService


class CheckHealthUseCase:
    def __init__(self, health_service: HealthService) -> None:
        self._health_service = health_service

    async def execute(self) -> HealthStatus:
        return await self._health_service.check()
