from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository

BRAZIL_TIMEZONE = ZoneInfo("America/Sao_Paulo")
SLOT_DURATION = timedelta(hours=1)


class FindAvailableSlotsUseCase:
    def __init__(self, repository: AppointmentRepository) -> None:
        self._repository = repository

    async def execute(self, target_date: date) -> list[datetime]:
        slots = self._build_daily_slots(target_date)
        appointments = await self._repository.list()
        blocked = [
            appointment
            for appointment in appointments
            if appointment.status is not AppointmentStatus.CANCELED
            and self._to_brazil_datetime(appointment.datetime).date() == target_date
        ]
        return [
            slot
            for slot in slots
            if not any(self._overlaps(slot, appointment) for appointment in blocked)
        ]

    def is_within_business_hours(self, target_datetime: datetime) -> bool:
        localized = self._to_brazil_datetime(target_datetime)
        day_slots = self._build_daily_slots(localized.date())
        return any(slot == localized for slot in day_slots)

    def _build_daily_slots(self, target_date: date) -> list[datetime]:
        weekday = target_date.weekday()
        if weekday == 6:
            return []

        start_hour = 8
        end_hour = 14 if weekday == 5 else 19
        return [
            datetime.combine(target_date, time(hour=hour), tzinfo=BRAZIL_TIMEZONE)
            for hour in range(start_hour, end_hour)
        ]

    def _overlaps(self, slot_start: datetime, appointment: Appointment) -> bool:
        appointment_start = self._to_brazil_datetime(appointment.datetime)
        appointment_end = appointment_start + SLOT_DURATION
        slot_end = slot_start + SLOT_DURATION
        return slot_start < appointment_end and appointment_start < slot_end

    def _to_brazil_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=BRAZIL_TIMEZONE)
        return value.astimezone(BRAZIL_TIMEZONE)
