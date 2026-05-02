from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.agents.appointment_agent import AppointmentAgentExecutor, AppointmentLangGraphAgent
from app.agents.schemas import AgentIntent
from app.application.errors import AppointmentNotFoundError
from app.application.use_cases.find_available_slots import FindAvailableSlotsUseCase
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.services.conversation_context_store import (
    ConversationContext,
    ConversationTurn,
    InMemoryConversationContextStore,
)
from app.infrastructure.services.gemini_llm_service import (
    GeminiLLMService,
    IntentClassification,
)
from app.infrastructure.services.telegram_client import TelegramClient
from app.presentation.api.schemas.telegram import TelegramUpdate

BRAZIL_TIMEZONE = ZoneInfo("America/Sao_Paulo")
LIST_KEYWORDS = (
    "meus agendamentos",
    "meus compromissos",
    "listar agendamentos",
    "listar compromissos",
    "mostrar agendamentos",
    "mostrar compromissos",
)


class TelegramAppointmentAssistant:
    def __init__(
        self,
        agent: AppointmentLangGraphAgent,
        executor: AppointmentAgentExecutor,
        get_use_case: GetAppointmentUseCase,
        list_use_case: ListAppointmentsUseCase,
        available_slots_use_case: FindAvailableSlotsUseCase,
        context_store: InMemoryConversationContextStore,
        llm_service: GeminiLLMService,
    ) -> None:
        self._agent = agent
        self._executor = executor
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._available_slots_use_case = available_slots_use_case
        self._context_store = context_store
        self._llm_service = llm_service
        self._logger = get_logger(__name__)

    async def handle_message(self, user_id: str, user_message: str) -> str:
        context = await self._context_store.get(user_id)
        now = datetime.now(BRAZIL_TIMEZONE)

        try:
            classification = await self._llm_service.classify_intent(
                user_message=user_message,
                history=self._format_history(context),
                current_datetime=now,
            )
            classification = self._apply_intent_overrides(user_message, classification)
            reply = await self._dispatch(user_id, user_message, context, classification, now)
        except Exception:
            self._logger.exception("telegram_message_processing_failed", extra={"user_id": user_id})
            reply = "Houve um problema tecnico ao processar sua mensagem. Tente novamente em instantes."

        context.turns.append(ConversationTurn(role="user", message=user_message))
        context.turns.append(ConversationTurn(role="assistant", message=reply))
        await self._context_store.save(user_id, context)
        return reply

    async def _dispatch(
        self,
        user_id: str,
        user_message: str,
        context: ConversationContext,
        classification: IntentClassification,
        now: datetime,
    ) -> str:
        requested_datetime = self._resolve_requested_datetime(
            classification.requested_time_iso,
            context.last_discussed_date,
        )
        intent = classification.intent

        if intent == "availability":
            target_date = (
                requested_datetime.date()
                if requested_datetime is not None
                else context.last_discussed_date or now.date()
            )
            context.last_discussed_date = target_date
            action = await self._agent.decide(
                f"disponibilidade user_id {user_id} em {self._date_to_midnight(target_date).isoformat()}"
            )
            if action.intent is not AgentIntent.AVAILABILITY:
                raise ValueError("unexpected agent route for availability")
            slots = await self._available_slots_use_case.execute(target_date)
            return await self._generate_reply(
                user_message=user_message,
                intent="availability",
                booking_result="N/A",
                events=await self._get_upcoming_user_appointments(user_id, now, hours=24),
                slots=slots,
            )

        if intent == "list":
            action = await self._agent.decide(f"listar compromissos user_id {user_id}")
            appointments = await self._executor.execute(action)
            if appointments:
                context.last_appointment_id = appointments[0].id
                context.last_discussed_date = self._to_brazil_datetime(appointments[0].datetime).date()
            return await self._generate_reply(
                user_message=user_message,
                intent="list",
                booking_result="N/A",
                events=appointments,
                slots=[],
            )

        if intent == "schedule":
            if requested_datetime is None:
                slots = await self._suggest_slots(context.last_discussed_date or now.date())
                return await self._generate_reply(
                    user_message=user_message,
                    intent="schedule",
                    booking_result="no_time",
                    events=await self._get_upcoming_user_appointments(user_id, now, hours=24),
                    slots=slots,
                )
            if not self._available_slots_use_case.is_within_business_hours(requested_datetime):
                return await self._generate_reply(
                    user_message=user_message,
                    intent="schedule",
                    booking_result="outside_hours",
                    events=await self._get_upcoming_user_appointments(user_id, now, hours=24),
                    slots=await self._suggest_slots(requested_datetime.date()),
                )
            if not await self._is_slot_available(requested_datetime):
                return await self._generate_reply(
                    user_message=user_message,
                    intent="schedule",
                    booking_result="unavailable",
                    events=await self._get_upcoming_user_appointments(user_id, now, hours=24),
                    slots=await self._suggest_slots(requested_datetime.date()),
                )

            action = await self._agent.decide(
                f"criar compromisso user_id {user_id} em {requested_datetime.isoformat()} status scheduled"
            )
            appointment = await self._executor.execute(action)
            context.last_appointment_id = appointment.id
            context.last_discussed_date = self._to_brazil_datetime(appointment.datetime).date()
            return await self._generate_reply(
                user_message=user_message,
                intent="schedule",
                booking_result="confirmed",
                events=[appointment],
                slots=[],
            )

        if intent == "reschedule":
            reference = await self._resolve_reference_appointment(user_id, context, now)
            if reference is None:
                return "Nao encontrei um agendamento seu para remarcar. Se quiser, posso listar seus proximos agendamentos."
            if requested_datetime is None:
                return await self._generate_reply(
                    user_message=user_message,
                    intent="reschedule",
                    booking_result="no_time",
                    events=[reference],
                    slots=await self._suggest_slots(self._to_brazil_datetime(reference.datetime).date()),
                )
            if not self._available_slots_use_case.is_within_business_hours(requested_datetime):
                return await self._generate_reply(
                    user_message=user_message,
                    intent="reschedule",
                    booking_result="outside_hours",
                    events=[reference],
                    slots=await self._suggest_slots(requested_datetime.date()),
                )
            if not await self._is_slot_available(requested_datetime, ignored_appointment_id=reference.id):
                return await self._generate_reply(
                    user_message=user_message,
                    intent="reschedule",
                    booking_result="unavailable",
                    events=[reference],
                    slots=await self._suggest_slots(requested_datetime.date()),
                )

            notes_segment = f" nota {reference.notes}" if reference.notes else ""
            action = await self._agent.decide(
                " ".join(
                    [
                        "reagendar compromisso",
                        f"id {reference.id}",
                        f"user_id {user_id}",
                        f"em {requested_datetime.isoformat()}",
                        f"status {reference.status.value}",
                        notes_segment.strip(),
                    ]
                ).strip()
            )
            appointment = await self._executor.execute(action)
            context.last_appointment_id = appointment.id
            context.last_discussed_date = self._to_brazil_datetime(appointment.datetime).date()
            return await self._generate_reply(
                user_message=user_message,
                intent="reschedule",
                booking_result="confirmed",
                events=[appointment],
                slots=[],
            )

        if intent in {"confirm", "cancel"}:
            reference = await self._resolve_reference_appointment(user_id, context, now)
            if reference is None:
                verb = "confirmar" if intent == "confirm" else "cancelar"
                return f"Nao encontrei um agendamento seu para {verb}. Posso listar seus proximos compromissos se voce quiser."
            action = await self._agent.decide(f"{intent}ar compromisso id {reference.id}")
            appointment = await self._executor.execute(action)
            context.last_appointment_id = appointment.id
            context.last_discussed_date = self._to_brazil_datetime(appointment.datetime).date()
            return await self._generate_reply(
                user_message=user_message,
                intent=intent,
                booking_result="confirmed",
                events=[appointment],
                slots=[],
            )

        return await self._generate_reply(
            user_message=user_message,
            intent="question",
            booking_result="N/A",
            events=await self._get_upcoming_user_appointments(user_id, now, hours=24),
            slots=[],
        )

    async def _generate_reply(
        self,
        user_message: str,
        intent: str,
        booking_result: str,
        events: list[Appointment],
        slots: list[datetime],
    ) -> str:
        return await self._llm_service.generate_reply(
            user_message=user_message,
            intent=intent,
            booking_result=booking_result,
            events=self._serialize_appointments(events),
            slots=self._serialize_slots(slots),
        )

    async def _resolve_reference_appointment(
        self,
        user_id: str,
        context: ConversationContext,
        now: datetime,
    ) -> Appointment | None:
        if context.last_appointment_id:
            try:
                appointment = await self._get_use_case.execute(context.last_appointment_id)
            except AppointmentNotFoundError:
                appointment = None
            if appointment is not None and appointment.user_id == user_id:
                return appointment

        upcoming = await self._get_upcoming_user_appointments(user_id, now, hours=None)
        return upcoming[0] if upcoming else None

    async def _get_upcoming_user_appointments(
        self,
        user_id: str,
        now: datetime,
        hours: int | None,
    ) -> list[Appointment]:
        appointments = await self._list_use_case.execute(user_id=user_id)
        filtered = []
        limit = now + timedelta(hours=hours) if hours is not None else None
        for appointment in appointments:
            localized = self._to_brazil_datetime(appointment.datetime)
            if localized < now or appointment.status is AppointmentStatus.CANCELED:
                continue
            if limit is not None and localized > limit:
                continue
            filtered.append(appointment)
        return sorted(filtered, key=lambda item: self._to_brazil_datetime(item.datetime))

    async def _is_slot_available(
        self,
        target_datetime: datetime,
        ignored_appointment_id: str | None = None,
    ) -> bool:
        appointments = await self._list_use_case.execute(user_id=None)
        target_start = self._to_brazil_datetime(target_datetime)
        target_end = target_start + timedelta(hours=1)
        for appointment in appointments:
            if appointment.id == ignored_appointment_id:
                continue
            if appointment.status is AppointmentStatus.CANCELED:
                continue
            start = self._to_brazil_datetime(appointment.datetime)
            end = start + timedelta(hours=1)
            if target_start < end and start < target_end:
                return False
        return True

    async def _suggest_slots(self, target_date: date) -> list[datetime]:
        return await self._available_slots_use_case.execute(target_date)

    def _apply_intent_overrides(
        self,
        user_message: str,
        classification: IntentClassification,
    ) -> IntentClassification:
        normalized = " ".join(user_message.lower().split())
        if any(keyword in normalized for keyword in LIST_KEYWORDS):
            return IntentClassification(intent="list", confidence=1.0, requested_time_iso=None)
        return classification

    def _format_history(self, context: ConversationContext) -> str:
        return "\n".join(f"{turn.role}: {turn.message}" for turn in context.turns)

    def _resolve_requested_datetime(
        self,
        requested_time_iso: str | None,
        fallback_date: date | None,
    ) -> datetime | None:
        if requested_time_iso is None:
            return None
        parsed = datetime.fromisoformat(requested_time_iso)
        if parsed.tzinfo is None:
            if parsed.time() == time(0, 0):
                if fallback_date is not None:
                    parsed = datetime.combine(fallback_date, parsed.time())
                return parsed.replace(tzinfo=BRAZIL_TIMEZONE)
            return parsed.replace(tzinfo=BRAZIL_TIMEZONE)
        return parsed.astimezone(BRAZIL_TIMEZONE)

    def _date_to_midnight(self, target_date: date) -> datetime:
        return datetime.combine(target_date, time(0, 0), tzinfo=BRAZIL_TIMEZONE)

    def _serialize_appointments(self, appointments: list[Appointment]) -> str:
        if not appointments:
            return "- nenhum"
        return "\n".join(
            (
                f"- {self._to_brazil_datetime(appointment.datetime).strftime('%d/%m/%Y %H:%M')} | "
                f"status={appointment.status.value} | id={appointment.id or 'sem-id'}"
            )
            for appointment in appointments
        )

    def _serialize_slots(self, slots: list[datetime]) -> str:
        if not slots:
            return "- nenhum"
        return "\n".join(
            f"- {self._to_brazil_datetime(slot).strftime('%d/%m/%Y %H:%M')}"
            for slot in slots[:8]
        )

    def _to_brazil_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=BRAZIL_TIMEZONE)
        return value.astimezone(BRAZIL_TIMEZONE)


class TelegramWebhookService:
    def __init__(
        self,
        assistant: TelegramAppointmentAssistant,
        telegram_client: TelegramClient,
    ) -> None:
        self._assistant = assistant
        self._telegram_client = telegram_client
        self._logger = get_logger(__name__)

    async def handle_update(self, update: TelegramUpdate) -> str | None:
        if update.message is None or not update.message.text:
            self._logger.info("telegram_update_ignored", extra={"update_id": update.update_id})
            return None

        user_id = str(update.message.sender.id)
        chat_id = str(update.message.chat.id)
        reply = await self._assistant.handle_message(user_id=user_id, user_message=update.message.text)
        await self._telegram_client.send_message(chat_id=chat_id, text=reply)
        return reply
