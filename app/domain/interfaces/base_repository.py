from abc import ABC, abstractmethod
from typing import Generic, TypeVar

EntityT = TypeVar("EntityT")


class BaseRepository(ABC, Generic[EntityT]):
    @abstractmethod
    async def create(self, entity: EntityT) -> EntityT:
        """Persist and return the created entity."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> EntityT | None:
        """Return an entity by identifier when it exists."""
