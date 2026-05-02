from abc import ABC, abstractmethod
from typing import Any

from app.infrastructure.logging.logger import get_logger


class AgentHooks(ABC):
    @abstractmethod
    async def before_node(self, node_name: str, state: dict[str, Any]) -> None:
        """Hook executed before a graph node runs."""

    @abstractmethod
    async def after_node(
        self,
        node_name: str,
        state: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Hook executed after a graph node finishes."""


class LoggingAgentHooks(AgentHooks):
    def __init__(self) -> None:
        self._logger = get_logger(__name__)

    async def before_node(self, node_name: str, state: dict[str, Any]) -> None:
        self._logger.info(
            "agent_node_started",
            extra={
                "node_name": node_name,
                "state_keys": sorted(state.keys()),
            },
        )

    async def after_node(
        self,
        node_name: str,
        state: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        self._logger.info(
            "agent_node_finished",
            extra={
                "node_name": node_name,
                "state_keys": sorted(state.keys()),
                "result_keys": sorted(result.keys()),
            },
        )