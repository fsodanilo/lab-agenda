import asyncio
from datetime import timedelta

from app.domain.entities.appointment import Appointment
from app.domain.interfaces.calendar_service import CalendarService
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class GoogleCalendarService(CalendarService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger(__name__)

    async def create_event(self, appointment: Appointment) -> str:
        return await asyncio.to_thread(self._create_event_sync, appointment)

    def _create_event_sync(self, appointment: Appointment) -> str:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        if not self._settings.google_calendar_id:
            raise ValueError("APP_GOOGLE_CALENDAR_ID is not configured")
        if not self._settings.google_service_account_file:
            raise ValueError("APP_GOOGLE_SERVICE_ACCOUNT_FILE is not configured")

        credentials = service_account.Credentials.from_service_account_file(
            self._settings.google_service_account_file,
            scopes=GOOGLE_CALENDAR_SCOPES,
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

        start_datetime = appointment.datetime
        end_datetime = appointment.datetime + timedelta(hours=1)
        body = {
            "summary": f"Appointment for {appointment.user_id}",
            "description": appointment.notes or "Appointment created by Lab Agenda API",
            "start": {"dateTime": start_datetime.isoformat()},
            "end": {"dateTime": end_datetime.isoformat()},
        }

        event = (
            service.events()
            .insert(calendarId=self._settings.google_calendar_id, body=body)
            .execute()
        )
        event_id = event["id"]
        self._logger.info("google_calendar_event_created", extra={"event_id": event_id})
        return event_id
