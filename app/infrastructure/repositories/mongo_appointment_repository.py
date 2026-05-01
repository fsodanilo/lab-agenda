from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.interfaces.appointment_repository import AppointmentRepository
from app.infrastructure.repositories.base import MongoBaseRepository


class MongoAppointmentRepository(MongoBaseRepository[Appointment], AppointmentRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        super().__init__(database=database, collection_name="appointments")

    async def list(self, user_id: str | None = None) -> list[Appointment]:
        query = {"user_id": user_id} if user_id is not None else {}
        cursor = self._collection.find(query).sort("datetime", 1)
        documents = await cursor.to_list(length=None)
        return [self._deserialize(document) for document in documents]

    def _serialize(self, entity: Appointment) -> dict[str, Any]:
        return {
            "user_id": entity.user_id,
            "datetime": entity.datetime,
            "status": entity.status.value,
            "notes": entity.notes,
        }

    def _deserialize(self, document: dict[str, Any]) -> Appointment:
        return Appointment(
            id=str(document["_id"]),
            user_id=document["user_id"],
            datetime=document["datetime"],
            status=AppointmentStatus(document["status"]),
            notes=document.get("notes"),
        )
