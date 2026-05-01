from app.domain.entities.health_status import HealthStatus
from app.domain.interfaces.health_service import HealthService
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger


class SystemHealthService(HealthService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger(__name__)

    def check(self) -> HealthStatus:
        self._logger.info("health_check_executed")
        return HealthStatus(
            status="ok",
            service=self._settings.app_name,
            version=self._settings.app_version,
        )
