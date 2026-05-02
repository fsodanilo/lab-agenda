import re
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.hooks import AgentHooks, LoggingAgentHooks
from app.agents.schemas import (
    AgentAction,
    AgentActionParameters,
    AgentIntent,
    AgentRole,
)
from app.application.use_cases.create_appointment import (
    CreateAppointmentCommand,
    CreateAppointmentUseCase,
)
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.application.use_cases.update_appointment import (
    UpdateAppointmentCommand,
    UpdateAppointmentUseCase,
)
from app.domain.entities.appointment import AppointmentStatus

DATETIME_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?"
)
APPOINTMENT_ID_PATTERNS = [
    re.compile(r"(?:compromisso|appointment)(?:_id| id)?[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"(?:^|\s)id[:= ]+([\w-]+)\b", re.IGNORECASE),
]
USER_ID_PATTERNS = [
    re.compile(r"user_id[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"usuario[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"para[:= ]+([\w-]+)", re.IGNORECASE),
]
NOTES_PATTERNS = [
    re.compile(r"notas?[:= ]+(.+)$", re.IGNORECASE),
    re.compile(r"obs[:= ]+(.+)$", re.IGNORECASE),
    re.compile(r"nota[:= ]+(.+)$", re.IGNORECASE),
]


class AgentState(TypedDict, total=False):
    user_input: str
    normalized_input: str
    intent: str
    route: str
    action: AgentAction


class _NaturalLanguageParser:
    def extract_datetime(self, text: str) -> datetime | None:
        match = DATETIME_PATTERN.search(text)
        if match is None:
            return None
        return datetime.fromisoformat(match.group(0).replace("Z", "+00:00"))

    def extract_status(self, text: str) -> AppointmentStatus | None:
        lowered = text.lower()
        for status in AppointmentStatus:
            if status.value in lowered:
                return status
        return None

    def extract_user_id(self, text: str) -> str | None:
        for pattern in USER_ID_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1)
        return None

    def extract_appointment_id(self, text: str) -> str | None:
        for pattern in APPOINTMENT_ID_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1)
        return None

    def extract_notes(self, text: str) -> str | None:
        for pattern in NOTES_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1).strip()
        return None


class RouterAgent:
    async def handle(self, state: AgentState) -> dict[str, Any]:
        text = state["normalized_input"]

        if any(keyword in text for keyword in ["confirmar", "confirmado"]):
            intent = AgentIntent.CONFIRM
            route = AgentRole.CONFIRMATION
        elif any(keyword in text for keyword in ["cancelar", "cancelado"]):
            intent = AgentIntent.CANCEL
            route = AgentRole.CONFIRMATION
        elif any(keyword in text for keyword in ["criar", "agendar", "marcar"]):
            intent = AgentIntent.CREATE
            route = AgentRole.SCHEDULING
        elif any(keyword in text for keyword in ["atualizar", "editar", "alterar", "reagendar"]):
            intent = AgentIntent.UPDATE
            route = AgentRole.SCHEDULING
        elif any(
            keyword in text
            for keyword in ["disponibilidade", "horario disponivel", "horarios disponiveis"]
        ):
            intent = AgentIntent.AVAILABILITY
            route = AgentRole.QUERY
        elif any(keyword in text for keyword in ["listar", "mostrar", "ver compromissos"]):
            intent = AgentIntent.LIST
            route = AgentRole.QUERY
        elif any(keyword in text for keyword in ["buscar", "procurar", "detalhe", "obter"]):
            intent = AgentIntent.GET
            route = AgentRole.QUERY
        else:
            intent = AgentIntent.UNKNOWN
            route = AgentRole.UNKNOWN

        return {"intent": intent.value, "route": route.value}


class SchedulingAgent(_NaturalLanguageParser):
    async def handle(self, state: AgentState) -> dict[str, Any]:
        intent = AgentIntent(state["intent"])
        action = AgentAction(
            agent_role=AgentRole.SCHEDULING,
            intent=intent,
            parameters=AgentActionParameters(
                appointment_id=self.extract_appointment_id(state["user_input"]),
                user_id=self.extract_user_id(state["user_input"]),
                datetime=self.extract_datetime(state["user_input"]),
                status=self.extract_status(state["user_input"]) or AppointmentStatus.SCHEDULED,
                notes=self.extract_notes(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}


class QueryAgent(_NaturalLanguageParser):
    async def handle(self, state: AgentState) -> dict[str, Any]:
        intent = AgentIntent(state["intent"])
        action = AgentAction(
            agent_role=AgentRole.QUERY,
            intent=intent,
            parameters=AgentActionParameters(
                appointment_id=self.extract_appointment_id(state["user_input"]),
                user_id=self.extract_user_id(state["user_input"]),
                datetime=self.extract_datetime(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}


class ConfirmationAgent(_NaturalLanguageParser):
    async def handle(self, state: AgentState) -> dict[str, Any]:
        intent = AgentIntent(state["intent"])
        status = (
            AppointmentStatus.CONFIRMED
            if intent is AgentIntent.CONFIRM
            else AppointmentStatus.CANCELED
        )
        action = AgentAction(
            agent_role=AgentRole.CONFIRMATION,
            intent=intent,
            parameters=AgentActionParameters(
                appointment_id=self.extract_appointment_id(state["user_input"]),
                status=status,
            ),
            original_input=state["user_input"],
        )
        return {"action": action}


class UnknownAgent:
    async def handle(self, state: AgentState) -> dict[str, Any]:
        return {
            "action": AgentAction(
                agent_role=AgentRole.UNKNOWN,
                intent=AgentIntent.UNKNOWN,
                parameters=AgentActionParameters(),
                original_input=state["user_input"],
            )
        }


class AppointmentLangGraphAgent:
    def __init__(self, hooks: AgentHooks | None = None) -> None:
        self._hooks = hooks or LoggingAgentHooks()
        self._router_agent = RouterAgent()
        self._scheduling_agent = SchedulingAgent()
        self._query_agent = QueryAgent()
        self._confirmation_agent = ConfirmationAgent()
        self._unknown_agent = UnknownAgent()

        builder = StateGraph(AgentState)
        builder.add_node("input", self._input_node)
        builder.add_node("router_agent", self._router_node)
        builder.add_node("scheduling_agent", self._scheduling_node)
        builder.add_node("query_agent", self._query_node)
        builder.add_node("confirmation_agent", self._confirmation_node)
        builder.add_node("unknown_action", self._unknown_action_node)

        builder.add_edge(START, "input")
        builder.add_edge("input", "router_agent")
        builder.add_conditional_edges(
            "router_agent",
            self._route_agent,
            {
                AgentRole.SCHEDULING.value: "scheduling_agent",
                AgentRole.QUERY.value: "query_agent",
                AgentRole.CONFIRMATION.value: "confirmation_agent",
                AgentRole.UNKNOWN.value: "unknown_action",
            },
        )
        builder.add_edge("scheduling_agent", END)
        builder.add_edge("query_agent", END)
        builder.add_edge("confirmation_agent", END)
        builder.add_edge("unknown_action", END)

        self._graph = builder.compile()

    async def decide(self, user_input: str) -> AgentAction:
        result = await self._graph.ainvoke({"user_input": user_input})
        return result["action"]

    async def _input_node(self, state: AgentState) -> dict[str, Any]:
        normalized_input = " ".join(state["user_input"].strip().split()).lower()
        result = {"normalized_input": normalized_input}
        await self._hooks.before_node("input", dict(state))
        await self._hooks.after_node("input", dict(state), result)
        return result

    async def _router_node(self, state: AgentState) -> dict[str, Any]:
        await self._hooks.before_node("router_agent", dict(state))
        result = await self._router_agent.handle(state)
        await self._hooks.after_node("router_agent", dict(state), result)
        return result

    def _route_agent(self, state: AgentState) -> str:
        return state["route"]

    async def _scheduling_node(self, state: AgentState) -> dict[str, Any]:
        await self._hooks.before_node("scheduling_agent", dict(state))
        result = await self._scheduling_agent.handle(state)
        await self._hooks.after_node("scheduling_agent", dict(state), result)
        return result

    async def _query_node(self, state: AgentState) -> dict[str, Any]:
        await self._hooks.before_node("query_agent", dict(state))
        result = await self._query_agent.handle(state)
        await self._hooks.after_node("query_agent", dict(state), result)
        return result

    async def _confirmation_node(self, state: AgentState) -> dict[str, Any]:
        await self._hooks.before_node("confirmation_agent", dict(state))
        result = await self._confirmation_agent.handle(state)
        await self._hooks.after_node("confirmation_agent", dict(state), result)
        return result

    async def _unknown_action_node(self, state: AgentState) -> dict[str, Any]:
        await self._hooks.before_node("unknown_action", dict(state))
        result = await self._unknown_agent.handle(state)
        await self._hooks.after_node("unknown_action", dict(state), result)
        return result


class AppointmentAgentExecutor:
    def __init__(
        self,
        create_use_case: CreateAppointmentUseCase,
        get_use_case: GetAppointmentUseCase,
        list_use_case: ListAppointmentsUseCase,
        update_use_case: UpdateAppointmentUseCase,
    ) -> None:
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._update_use_case = update_use_case

    async def execute(self, action: AgentAction) -> Any:
        params = action.parameters

        if action.intent is AgentIntent.CREATE:
            return await self._create_use_case.execute(
                CreateAppointmentCommand(
                    user_id=params.user_id or "",
                    datetime=params.datetime,
                    status=params.status or AppointmentStatus.SCHEDULED,
                    notes=params.notes,
                )
            )

        if action.intent is AgentIntent.GET:
            return await self._get_use_case.execute(params.appointment_id or "")

        if action.intent is AgentIntent.LIST:
            return await self._list_use_case.execute(user_id=params.user_id)

        if action.intent is AgentIntent.UPDATE:
            return await self._update_use_case.execute(
                UpdateAppointmentCommand(
                    appointment_id=params.appointment_id or "",
                    user_id=params.user_id or "",
                    datetime=params.datetime,
                    status=params.status or AppointmentStatus.SCHEDULED,
                    notes=params.notes,
                )
            )

        if action.intent in {AgentIntent.CONFIRM, AgentIntent.CANCEL}:
            existing = await self._get_use_case.execute(params.appointment_id or "")
            target_status = (
                AppointmentStatus.CONFIRMED
                if action.intent is AgentIntent.CONFIRM
                else AppointmentStatus.CANCELED
            )
            return await self._update_use_case.execute(
                UpdateAppointmentCommand(
                    appointment_id=existing.id or "",
                    user_id=existing.user_id,
                    datetime=existing.datetime,
                    status=target_status,
                    notes=existing.notes,
                )
            )

        return action
