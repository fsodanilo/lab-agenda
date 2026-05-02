from datetime import datetime as DateTime
from enum import StrEnum

from pydantic import BaseModel

from app.domain.entities.appointment import AppointmentStatus


class AgentIntent(StrEnum):
    CREATE = "create"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"
    UNKNOWN = "unknown"


class AgentActionParameters(BaseModel):
    appointment_id: str | None = None
    user_id: str | None = None
    datetime: DateTime | None = None
    status: AppointmentStatus | None = None
    notes: str | None = None


class AgentAction(BaseModel):
    intent: AgentIntent
    parameters: AgentActionParameters
    original_input: str
