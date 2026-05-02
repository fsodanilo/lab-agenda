import re
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.schemas import AgentAction, AgentActionParameters, AgentIntent
from app.application.use_cases.create_appointment import (
    CreateAppointmentCommand,
    CreateAppointmentUseCase,
)
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.application.use_cases.update_appointment import (
    UpdateAppointmentCommand,
    UpdateAppointmentUseCase,
)
from app.domain.entities.appointment import AppointmentStatus

DATETIME_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})"
)
APPOINTMENT_ID_PATTERNS = [
    re.compile(r"(?:compromisso|appointment)(?:_id| id)?[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"id[:= ]+([\w-]+)", re.IGNORECASE),
]
USER_ID_PATTERNS = [
    re.compile(r"user_id[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"usuario[:= ]+([\w-]+)", re.IGNORECASE),
    re.compile(r"para[:= ]+([\w-]+)", re.IGNORECASE),
]
NOTES_PATTERNS = [
    re.compile(r"notas?[:= ]+(.+)$", re.IGNORECASE),
    re.compile(r"obs[:= ]+(.+)$", re.IGNORECASE),
]


class AgentState(TypedDict, total=False):
    user_input: str
    normalized_input: str
    intent: str
    action: AgentAction


class AppointmentLangGraphAgent:
    def __init__(self) -> None:
        builder = StateGraph(AgentState)
        builder.add_node("input", self._input_node)
        builder.add_node("decision", self._decision_node)
        builder.add_node("create_action", self._create_action_node)
        builder.add_node("list_action", self._list_action_node)
        builder.add_node("update_action", self._update_action_node)
        builder.add_node("delete_action", self._delete_action_node)
        builder.add_node("unknown_action", self._unknown_action_node)

        builder.add_edge(START, "input")
        builder.add_edge("input", "decision")
        builder.add_conditional_edges(
            "decision",
            self._route_intent,
            {
                AgentIntent.CREATE.value: "create_action",
                AgentIntent.LIST.value: "list_action",
                AgentIntent.UPDATE.value: "update_action",
                AgentIntent.DELETE.value: "delete_action",
                AgentIntent.UNKNOWN.value: "unknown_action",
            },
        )
        builder.add_edge("create_action", END)
        builder.add_edge("list_action", END)
        builder.add_edge("update_action", END)
        builder.add_edge("delete_action", END)
        builder.add_edge("unknown_action", END)

        self._graph = builder.compile()

    async def decide(self, user_input: str) -> AgentAction:
        result = await self._graph.ainvoke({"user_input": user_input})
        return result["action"]

    async def _input_node(self, state: AgentState) -> dict[str, Any]:
        normalized_input = " ".join(state["user_input"].strip().split()).lower()
        return {"normalized_input": normalized_input}

    async def _decision_node(self, state: AgentState) -> dict[str, Any]:
        text = state["normalized_input"]

        if any(keyword in text for keyword in ["criar", "agendar", "marcar"]):
            intent = AgentIntent.CREATE
        elif any(keyword in text for keyword in ["listar", "mostrar", "ver compromissos"]):
            intent = AgentIntent.LIST
        elif any(keyword in text for keyword in ["atualizar", "editar", "alterar"]):
            intent = AgentIntent.UPDATE
        elif any(keyword in text for keyword in ["deletar", "excluir", "remover"]):
            intent = AgentIntent.DELETE
        else:
            intent = AgentIntent.UNKNOWN

        return {"intent": intent.value}

    def _route_intent(self, state: AgentState) -> str:
        return state["intent"]

    async def _create_action_node(self, state: AgentState) -> dict[str, Any]:
        action = AgentAction(
            intent=AgentIntent.CREATE,
            parameters=AgentActionParameters(
                user_id=self._extract_user_id(state["user_input"]),
                datetime=self._extract_datetime(state["user_input"]),
                status=self._extract_status(state["user_input"]) or AppointmentStatus.SCHEDULED,
                notes=self._extract_notes(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}

    async def _list_action_node(self, state: AgentState) -> dict[str, Any]:
        action = AgentAction(
            intent=AgentIntent.LIST,
            parameters=AgentActionParameters(
                user_id=self._extract_user_id(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}

    async def _update_action_node(self, state: AgentState) -> dict[str, Any]:
        action = AgentAction(
            intent=AgentIntent.UPDATE,
            parameters=AgentActionParameters(
                appointment_id=self._extract_appointment_id(state["user_input"]),
                user_id=self._extract_user_id(state["user_input"]),
                datetime=self._extract_datetime(state["user_input"]),
                status=self._extract_status(state["user_input"]),
                notes=self._extract_notes(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}

    async def _delete_action_node(self, state: AgentState) -> dict[str, Any]:
        action = AgentAction(
            intent=AgentIntent.DELETE,
            parameters=AgentActionParameters(
                appointment_id=self._extract_appointment_id(state["user_input"]),
            ),
            original_input=state["user_input"],
        )
        return {"action": action}

    async def _unknown_action_node(self, state: AgentState) -> dict[str, Any]:
        return {
            "action": AgentAction(
                intent=AgentIntent.UNKNOWN,
                parameters=AgentActionParameters(),
                original_input=state["user_input"],
            )
        }

    def _extract_datetime(self, text: str) -> datetime | None:
        match = DATETIME_PATTERN.search(text)
        if match is None:
            return None
        return datetime.fromisoformat(match.group(0).replace("Z", "+00:00"))

    def _extract_status(self, text: str) -> AppointmentStatus | None:
        for status in AppointmentStatus:
            if status.value in text.lower():
                return status
        return None

    def _extract_user_id(self, text: str) -> str | None:
        for pattern in USER_ID_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1)
        return None

    def _extract_appointment_id(self, text: str) -> str | None:
        for pattern in APPOINTMENT_ID_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1)
        return None

    def _extract_notes(self, text: str) -> str | None:
        for pattern in NOTES_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                return match.group(1).strip()
        return None


class AppointmentAgentExecutor:
    def __init__(
        self,
        create_use_case: CreateAppointmentUseCase,
        list_use_case: ListAppointmentsUseCase,
        update_use_case: UpdateAppointmentUseCase,
        delete_use_case: DeleteAppointmentUseCase,
    ) -> None:
        self._create_use_case = create_use_case
        self._list_use_case = list_use_case
        self._update_use_case = update_use_case
        self._delete_use_case = delete_use_case

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

        if action.intent is AgentIntent.DELETE:
            return await self._delete_use_case.execute(params.appointment_id or "")

        return action
