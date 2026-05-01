from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.infrastructure.config.settings import Settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client(settings: Settings) -> AsyncIOMotorClient:
    global _client

    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_mongo_database(settings: Settings) -> AsyncIOMotorDatabase:
    client = get_mongo_client(settings)
    return client[settings.mongodb_database]


async def close_mongo_connection() -> None:
    global _client

    if _client is not None:
        _client.close()
        _client = None
