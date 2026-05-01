from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

EntityT = TypeVar("EntityT")


class MongoBaseRepository(ABC, Generic[EntityT]):
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self._collection: AsyncIOMotorCollection = database[collection_name]

    async def create(self, entity: EntityT) -> EntityT:
        payload = self._serialize(entity)
        result = await self._collection.insert_one(payload)
        document = await self._collection.find_one({"_id": result.inserted_id})
        if document is None:
            raise RuntimeError("created_document_not_found")
        return self._deserialize(document)

    async def get_by_id(self, entity_id: str) -> EntityT | None:
        object_id = self._parse_object_id(entity_id)
        if object_id is None:
            return None

        document = await self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return self._deserialize(document)

    async def update(self, entity_id: str, entity: EntityT) -> EntityT | None:
        object_id = self._parse_object_id(entity_id)
        if object_id is None:
            return None

        payload = self._serialize(entity)
        result = await self._collection.replace_one({"_id": object_id}, payload)
        if result.matched_count == 0:
            return None

        document = await self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return self._deserialize(document)

    async def delete(self, entity_id: str) -> bool:
        object_id = self._parse_object_id(entity_id)
        if object_id is None:
            return False

        result = await self._collection.delete_one({"_id": object_id})
        return result.deleted_count > 0

    def _parse_object_id(self, entity_id: str) -> ObjectId | None:
        if not ObjectId.is_valid(entity_id):
            return None
        return ObjectId(entity_id)

    @abstractmethod
    def _serialize(self, entity: EntityT) -> dict[str, Any]:
        """Convert a domain entity into a MongoDB document."""

    @abstractmethod
    def _deserialize(self, document: dict[str, Any]) -> EntityT:
        """Convert a MongoDB document into a domain entity."""
