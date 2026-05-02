from functools import lru_cache

from app.agents.appointment_agent import AppointmentAgentExecutor, AppointmentLangGraphAgent
from app.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.application.use_cases.check_health import CheckHealthUseCase
from app.application.use_cases.find_available_slots import FindAvailableSlotsUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.application.use_cases.update_appointment import UpdateAppointmentUseCase
from app.domain.interfaces.appointment_repository import AppointmentRepository
from app.domain.interfaces.calendar_service import CalendarService
from app.domain.interfaces.health_service import HealthService
from app.infrastructure.config.settings import Settings
from app.infrastructure.database.mongo import get_mongo_database
from app.infrastructure.repositories.mongo_appointment_repository import (
    MongoAppointmentRepository,
)
from app.infrastructure.services.conversation_context_store import (
    InMemoryConversationContextStore,
)
from app.infrastructure.services.gemini_llm_service import GeminiLLMService
from app.infrastructure.services.google_calendar_service import GoogleCalendarService
from app.infrastructure.services.telegram_client import TelegramClient
from app.infrastructure.services.telegram_multi_agent_service import (
    TelegramAppointmentAssistant,
    TelegramWebhookService,
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


def get_calendar_service() -> CalendarService:
    return GoogleCalendarService(settings=get_settings())


def get_create_appointment_use_case() -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(
        repository=get_appointment_repository(),
        calendar_service=get_calendar_service(),
    )


def get_get_appointment_use_case() -> GetAppointmentUseCase:
    return GetAppointmentUseCase(repository=get_appointment_repository())


def get_list_appointments_use_case() -> ListAppointmentsUseCase:
    return ListAppointmentsUseCase(repository=get_appointment_repository())


def get_update_appointment_use_case() -> UpdateAppointmentUseCase:
    return UpdateAppointmentUseCase(repository=get_appointment_repository())


def get_delete_appointment_use_case() -> DeleteAppointmentUseCase:
    return DeleteAppointmentUseCase(repository=get_appointment_repository())


def get_find_available_slots_use_case() -> FindAvailableSlotsUseCase:
    return FindAvailableSlotsUseCase(repository=get_appointment_repository())


@lru_cache
def get_appointment_langgraph_agent() -> AppointmentLangGraphAgent:
    return AppointmentLangGraphAgent()


def get_appointment_agent_executor() -> AppointmentAgentExecutor:
    return AppointmentAgentExecutor(
        create_use_case=get_create_appointment_use_case(),
        get_use_case=get_get_appointment_use_case(),
        list_use_case=get_list_appointments_use_case(),
        update_use_case=get_update_appointment_use_case(),
    )


@lru_cache
def get_conversation_context_store() -> InMemoryConversationContextStore:
    return InMemoryConversationContextStore()


@lru_cache
def get_gemini_llm_service() -> GeminiLLMService:
    return GeminiLLMService(settings=get_settings())


@lru_cache
def get_telegram_client() -> TelegramClient:
    return TelegramClient(settings=get_settings())


def get_telegram_appointment_assistant() -> TelegramAppointmentAssistant:
    return TelegramAppointmentAssistant(
        agent=get_appointment_langgraph_agent(),
        executor=get_appointment_agent_executor(),
        get_use_case=get_get_appointment_use_case(),
        list_use_case=get_list_appointments_use_case(),
        available_slots_use_case=get_find_available_slots_use_case(),
        context_store=get_conversation_context_store(),
        llm_service=get_gemini_llm_service(),
    )


def get_telegram_webhook_service() -> TelegramWebhookService:
    return TelegramWebhookService(
        assistant=get_telegram_appointment_assistant(),
        telegram_client=get_telegram_client(),
    )

