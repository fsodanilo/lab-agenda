from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.entities.appointment import AppointmentStatus


class AppointmentRequestBase(BaseModel):
    user_id: str
    datetime: datetime
    status: AppointmentStatus
    notes: str | None = None

    @field_validator("datetime")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must include timezone information")
        return value


class CreateAppointmentRequest(AppointmentRequestBase):
    pass


class UpdateAppointmentRequest(AppointmentRequestBase):
    pass


class AppointmentResponse(BaseModel):
    id: str
    user_id: str
    datetime: datetime
    status: AppointmentStatus
    notes: str | None = None
    event_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
