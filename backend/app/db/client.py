from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def connect(settings: Settings) -> AsyncIOMotorDatabase:
    """Create the process-wide motor client. Idempotent."""
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )
        _db = _client[settings.MONGO_DB]
    return _db


def get_client() -> AsyncIOMotorClient | None:
    return _client


def get_db() -> AsyncIOMotorDatabase | None:
    return _db


async def ping() -> bool:
    """True when the server answers `ping`; never raises."""
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False


async def close() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
