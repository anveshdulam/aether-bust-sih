import tempfile

import pytest
import pytest_asyncio

from data.generator import generate_run

# ensure_schema is idempotent but not free; run it once per test session.
_SCHEMA_READY = {"done": False}


@pytest.fixture(scope="session")
def synthetic_run():
    with tempfile.TemporaryDirectory() as d:
        paths = generate_run("test_run", d)
        yield paths


@pytest.fixture(scope="session")
def api_settings():
    from app.config import Settings

    return Settings()


@pytest.fixture(scope="session")
def api_app(api_settings):
    """
    The FastAPI app with lifespan work performed explicitly: httpx's
    ASGITransport does not run lifespan events.

    Session-scoped so the BustNet weights are built once and the RunService
    inference cache is shared by every test. The Mongo client is deliberately
    NOT created here -- motor binds to the running event loop, and pytest-asyncio
    gives each test its own, so `wired_db` attaches a fresh client per test.
    """
    from app.main import create_app
    from app.services.run_service import RunService

    app = create_app(api_settings)
    api_settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    svc = RunService(api_settings, db=None)
    svc.load_model()
    app.state.run_service = svc

    yield app


@pytest.fixture(scope="session")
def run_service(api_app):
    return api_app.state.run_service


@pytest.fixture(scope="session")
def demo_run_id(run_service):
    """A run materialized on disk, reused by every API test."""
    return run_service.default_run_id()


@pytest_asyncio.fixture
async def wired_db(api_app, api_settings):
    """
    A motor client created inside *this* test's event loop and attached to the
    RunService. Yields None (rather than skipping) when no server is reachable,
    so the Mongo-independent API tests still run.
    """
    from app.db import client as db_client
    from app.db.indexes import ensure_schema

    await db_client.close()  # drop any client bound to a previous test's loop
    db = db_client.connect(api_settings)

    if not await db_client.ping():
        await db_client.close()
        api_app.state.run_service.db = None
        yield None
        return

    if not _SCHEMA_READY["done"]:
        await ensure_schema(db)
        _SCHEMA_READY["done"] = True

    api_app.state.run_service.db = db
    try:
        yield db
    finally:
        api_app.state.run_service.db = None
        await db_client.close()


@pytest_asyncio.fixture
async def client(api_app, wired_db):
    import httpx

    transport = httpx.ASGITransport(app=api_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def mongo_db(wired_db, api_settings):
    """The live database, or a skip when no server is reachable."""
    if wired_db is None:
        pytest.skip(f"MongoDB not reachable at {api_settings.MONGO_URI}")
    return wired_db
