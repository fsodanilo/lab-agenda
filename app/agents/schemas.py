from datetime import datetime as DateTime
from enum import StrEnum

from pydantic import BaseModel

from app.domain.entities.appointment import AppointmentStatus


class AgentIntent(StrEnum):
    CREATE = "create"
    GET = "get"
    LIST = "list"
    UPDATE = "update"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


class AgentRole(StrEnum):
    ROUTER = "router"
    SCHEDULING = "scheduling"
    QUERY = "query"
    CONFIRMATION = "confirmation"
    UNKNOWN = "unknown"


class AgentActionParameters(BaseModel):
    appointment_id: str | None = None
    user_id: str | None = None
    datetime: DateTime | None = None
    status: AppointmentStatus | None = None
    notes: str | None = None


class AgentAction(BaseModel):
    agent_role: AgentRole
    intent: AgentIntent
    parameters: AgentActionParameters
    original_input: str
