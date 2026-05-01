from functools import lru_cache

from app.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.application.use_cases.check_health import CheckHealthUseCase
from app.domain.interfaces.appointment_repository import AppointmentRepository
from app.domain.interfaces.health_service import HealthService
from app.infrastructure.config.settings import Settings
from app.infrastructure.database.mongo import get_mongo_database
from app.infrastructure.repositories.mongo_appointment_repository import (
    MongoAppointmentRepository,
)
from app.infrastructure.services.system_health_service import SystemHealthService


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_health_service() -> HealthService:
    return SystemHealthService(settings=get_settings())


def get_check_health_use_case() -> CheckHealthUseCase:
    return CheckHealthUseCase(health_service=get_health_service())


def get_appointment_repository() -> AppointmentRepository:
    database = get_mongo_database(get_settings())
    return MongoAppointmentRepository(database=database)


def get_create_appointment_use_case() -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(repository=get_appointment_repository())

