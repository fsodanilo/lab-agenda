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

    @abstractmethod
    async def update(self, entity_id: str, entity: EntityT) -> EntityT | None:
        """Replace an entity and return the updated version when it exists."""

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by identifier and return whether it existed."""
