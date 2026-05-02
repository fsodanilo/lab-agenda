import pytest

from app.agents.appointment_agent import AppointmentLangGraphAgent
from app.agents.schemas import AgentIntent


@pytest.mark.anyio
async def test_agent_decides_create_and_extracts_parameters() -> None:
    agent = AppointmentLangGraphAgent()

    action = await agent.decide(
        "criar compromisso user_id user-123 em 2026-05-03T15:30:00Z status scheduled nota consulta inicial"
    )

    assert action.intent is AgentIntent.CREATE
    assert action.parameters.user_id == "user-123"
    assert action.parameters.datetime is not None
    assert action.parameters.status.value == "scheduled"


@pytest.mark.anyio
async def test_agent_decides_list_action() -> None:
    agent = AppointmentLangGraphAgent()

    action = await agent.decide("listar compromissos user_id user-456")

    assert action.intent is AgentIntent.LIST
    assert action.parameters.user_id == "user-456"


@pytest.mark.anyio
async def test_agent_decides_update_action() -> None:
    agent = AppointmentLangGraphAgent()

    action = await agent.decide(
        "atualizar compromisso id appointment-1 user_id user-123 em 2026-05-03T16:00:00Z status confirmed"
    )

    assert action.intent is AgentIntent.UPDATE
    assert action.parameters.appointment_id == "appointment-1"
    assert action.parameters.status.value == "confirmed"