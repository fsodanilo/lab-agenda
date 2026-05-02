from datetime import UTC, date, datetime

import pytest

from app.agents.schemas import AgentAction, AgentActionParameters, AgentIntent, AgentRole
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.infrastructure.services.conversation_context_store import (
    InMemoryConversationContextStore,
)
from app.infrastructure.services.gemini_llm_service import IntentClassification
from app.infrastructure.services.telegram_multi_agent_service import TelegramAppointmentAssistant


class FakeAgent:
    def __init__(self, action: AgentAction) -> None:
        self.action = action
        self.calls: list[str] = []

    async def decide(self, user_input: str) -> AgentAction:
        self.calls.append(user_input)
        return self.action


class FakeExecutor:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[AgentAction] = []

    async def execute(self, action: AgentAction) -> object:
        self.calls.append(action)
        return self.result


class FakeGetAppointmentUseCase:
    def __init__(self, appointment: Appointment | None = None) -> None:
        self.appointment = appointment

    async def execute(self, appointment_id: str) -> Appointment:
        if self.appointment is None:
            raise AssertionError("appointment not configured")
        return self.appointment


class FakeListAppointmentsUseCase:
    def __init__(self, by_user: list[Appointment], all_items: list[Appointment] | None = None) -> None:
        self.by_user = by_user
        self.all_items = all_items if all_items is not None else by_user

    async def execute(self, user_id: str | None = None) -> list[Appointment]:
        if user_id is None:
            return list(self.all_items)
        return list(self.by_user)


class FakeFindAvailableSlotsUseCase:
    def __init__(self, slots: list[datetime], within_business_hours: bool = True) -> None:
        self.slots = slots
        self.within_business_hours = within_business_hours

    async def execute(self, target_date: date) -> list[datetime]:
        return list(self.slots)

    def is_within_business_hours(self, target_datetime: datetime) -> bool:
        return self.within_business_hours


class FakeLLMService:
    def __init__(self, classification: IntentClassification) -> None:
        self.classification = classification
        self.reply_calls: list[dict[str, str]] = []

    async def classify_intent(
        self,
        user_message: str,
        history: str,
        current_datetime: datetime,
    ) -> IntentClassification:
        return self.classification

    async def generate_reply(
        self,
        user_message: str,
        intent: str,
        booking_result: str,
        events: str,
        slots: str,
    ) -> str:
        self.reply_calls.append(
            {
                "intent": intent,
                "booking_result": booking_result,
                "events": events,
                "slots": slots,
            }
        )
        return f"reply:{intent}:{booking_result}"


@pytest.mark.anyio
async def test_assistant_handles_availability_and_updates_context() -> None:
    llm = FakeLLMService(
        IntentClassification(
            intent="availability",
            confidence=0.98,
            requested_time_iso="2026-05-03T00:00:00",
        )
    )
    agent = FakeAgent(
        AgentAction(
            agent_role=AgentRole.QUERY,
            intent=AgentIntent.AVAILABILITY,
            parameters=AgentActionParameters(),
            original_input="disponibilidade",
        )
    )
    assistant = TelegramAppointmentAssistant(
        agent=agent,
        executor=FakeExecutor(result=[]),
        get_use_case=FakeGetAppointmentUseCase(),
        list_use_case=FakeListAppointmentsUseCase(by_user=[]),
        available_slots_use_case=FakeFindAvailableSlotsUseCase(
            [datetime(2026, 5, 3, 8, 0, tzinfo=UTC)]
        ),
        context_store=InMemoryConversationContextStore(),
        llm_service=llm,
    )

    reply = await assistant.handle_message("tg-user-1", "Tenho horario amanha?")
    context = await assistant._context_store.get("tg-user-1")

    assert reply == "reply:availability:N/A"
    assert agent.calls[0].startswith("disponibilidade user_id tg-user-1")
    assert context.last_discussed_date == date(2026, 5, 3)


@pytest.mark.anyio
async def test_assistant_creates_appointment_when_slot_is_free() -> None:
    created = Appointment(
        id="appt-99",
        user_id="tg-user-2",
        datetime=datetime(2026, 5, 3, 15, 0, tzinfo=UTC),
        status=AppointmentStatus.SCHEDULED,
    )
    llm = FakeLLMService(
        IntentClassification(
            intent="schedule",
            confidence=0.99,
            requested_time_iso="2026-05-03T15:00:00-03:00",
        )
    )
    agent = FakeAgent(
        AgentAction(
            agent_role=AgentRole.SCHEDULING,
            intent=AgentIntent.CREATE,
            parameters=AgentActionParameters(
                user_id="tg-user-2",
                datetime=datetime(2026, 5, 3, 15, 0, tzinfo=UTC),
                status=AppointmentStatus.SCHEDULED,
            ),
            original_input="criar compromisso",
        )
    )
    assistant = TelegramAppointmentAssistant(
        agent=agent,
        executor=FakeExecutor(result=created),
        get_use_case=FakeGetAppointmentUseCase(created),
        list_use_case=FakeListAppointmentsUseCase(by_user=[], all_items=[]),
        available_slots_use_case=FakeFindAvailableSlotsUseCase([], within_business_hours=True),
        context_store=InMemoryConversationContextStore(),
        llm_service=llm,
    )

    reply = await assistant.handle_message("tg-user-2", "Quero agendar sabado as 15h")
    context = await assistant._context_store.get("tg-user-2")

    assert reply == "reply:schedule:confirmed"
    assert agent.calls[0].startswith("criar compromisso user_id tg-user-2")
    assert context.last_appointment_id == "appt-99"


@pytest.mark.anyio
async def test_assistant_lists_user_appointments() -> None:
    appointment = Appointment(
        id="appt-7",
        user_id="tg-user-3",
        datetime=datetime(2026, 5, 4, 10, 0, tzinfo=UTC),
        status=AppointmentStatus.CONFIRMED,
    )
    llm = FakeLLMService(
        IntentClassification(intent="question", confidence=0.42, requested_time_iso=None)
    )
    agent = FakeAgent(
        AgentAction(
            agent_role=AgentRole.QUERY,
            intent=AgentIntent.LIST,
            parameters=AgentActionParameters(user_id="tg-user-3"),
            original_input="listar compromissos",
        )
    )
    assistant = TelegramAppointmentAssistant(
        agent=agent,
        executor=FakeExecutor(result=[appointment]),
        get_use_case=FakeGetAppointmentUseCase(appointment),
        list_use_case=FakeListAppointmentsUseCase(by_user=[appointment]),
        available_slots_use_case=FakeFindAvailableSlotsUseCase([]),
        context_store=InMemoryConversationContextStore(),
        llm_service=llm,
    )

    reply = await assistant.handle_message("tg-user-3", "listar meus agendamentos")

    assert reply == "reply:list:N/A"
    assert agent.calls[0] == "listar compromissos user_id tg-user-3"


@pytest.mark.anyio
async def test_assistant_confirms_latest_appointment_from_context() -> None:
    appointment = Appointment(
        id="appt-10",
        user_id="tg-user-4",
        datetime=datetime(2026, 5, 4, 10, 0, tzinfo=UTC),
        status=AppointmentStatus.CONFIRMED,
    )
    llm = FakeLLMService(
        IntentClassification(intent="confirm", confidence=0.93, requested_time_iso=None)
    )
    agent = FakeAgent(
        AgentAction(
            agent_role=AgentRole.CONFIRMATION,
            intent=AgentIntent.CONFIRM,
            parameters=AgentActionParameters(appointment_id="appt-10"),
            original_input="confirmar compromisso",
        )
    )
    context_store = InMemoryConversationContextStore()
    context = await context_store.get("tg-user-4")
    context.last_appointment_id = "appt-10"
    await context_store.save("tg-user-4", context)
    assistant = TelegramAppointmentAssistant(
        agent=agent,
        executor=FakeExecutor(result=appointment),
        get_use_case=FakeGetAppointmentUseCase(appointment),
        list_use_case=FakeListAppointmentsUseCase(by_user=[appointment]),
        available_slots_use_case=FakeFindAvailableSlotsUseCase([]),
        context_store=context_store,
        llm_service=llm,
    )

    reply = await assistant.handle_message("tg-user-4", "pode confirmar")

    assert reply == "reply:confirm:confirmed"
    assert agent.calls[0] == "confirmar compromisso id appt-10"
