from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"


@dataclass(frozen=True, slots=True)
class Appointment:
    user_id: str
    datetime: datetime
    status: AppointmentStatus
    notes: str | None = None
    id: str | None = None
